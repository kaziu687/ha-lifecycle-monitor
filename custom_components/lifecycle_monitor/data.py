"""Utilities for lifecycle_monitor."""

from __future__ import annotations

import re
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import (
    CONF_LAST_REPLACED,
    CONF_NAME,
    DOMAIN,
)

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

type LifecycleMonitorConfigEntry = ConfigEntry


def _slugify_name(name: str) -> str:
    """Convert a user-provided name to a slug suitable for entity IDs."""
    slug = re.sub(r"[\s\-]+", "_", name.strip()).lower()
    return re.sub(r"[^a-z0-9_]", "", slug).strip("_")


def get_entry_name(entry: ConfigEntry) -> str:
    """Return the user-provided name from the config entry."""
    return entry.data.get(CONF_NAME, "")


def get_attached_device(
    hass: HomeAssistant, entry: ConfigEntry
) -> dr.DeviceEntry | None:
    """Return the attached device entry, or None for standalone mode."""
    if device_id := entry.options.get(CONF_DEVICE_ID):
        return dr.async_get(hass).async_get(device_id)
    return None


def get_elapsed_days(entry: ConfigEntry) -> float | None:
    """Get days elapsed since last replacement, or None if never set."""
    last_replaced_str = entry.options.get(CONF_LAST_REPLACED)
    if last_replaced_str is None:
        return None
    last_replaced = dt_util.parse_datetime(last_replaced_str)
    if last_replaced is None:
        return None
    return (dt_util.now() - last_replaced).total_seconds() / 86400


class LifecycleEntity(Entity):
    """Base class for all Lifecycle Monitor entities."""

    _attr_has_entity_name = True
    _attr_suggested_object_id: str | None = None

    def __init__(
        self,
        entry: ConfigEntry,
        attached_device: dr.DeviceEntry | None = None,
    ) -> None:
        """Initialize the entity."""
        self._entry = entry
        self._attached = attached_device is not None
        if attached_device:
            self.device_entry = attached_device
        else:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, entry.entry_id)},
                name=entry.data[CONF_NAME],
            )

    @property
    def suggested_object_id(self) -> str | None:
        """Return entity ID suffix prefixed with the slugified user name."""
        if self._attr_suggested_object_id is None:
            return super().suggested_object_id
        if self._attached:
            name_slug = _slugify_name(get_entry_name(self._entry))
            if not name_slug:
                return self._attr_suggested_object_id
            return f"{name_slug}_{self._attr_suggested_object_id}"
        return self._attr_suggested_object_id

    def _get_translated_base_name(self, fallback: str) -> str:
        """Get the translated entity base name from platform translations."""
        translation_key = getattr(self, "_attr_translation_key", None)
        if not translation_key:
            return fallback
        platform = getattr(self, "platform", None)
        if not platform:
            return fallback
        platform_data = getattr(platform, "platform_data", None)
        if not platform_data:
            return fallback
        translations = platform_data.platform_translations
        if not translations:
            return fallback
        key = (
            f"component.{platform.platform_name}"
            f".entity.{platform.domain}"
            f".{translation_key}.name"
        )
        return translations.get(key, fallback)


class LifecyclePolledEntity(LifecycleEntity):
    """Base class for entities that update on a time interval."""

    _attr_should_poll = False

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self._update_state()
        self.async_on_remove(
            async_track_time_interval(
                self.hass,
                self._timed_update,
                timedelta(hours=1),
            ),
        )

    @callback
    def _timed_update(self, _now: datetime) -> None:
        """Update the state on a time interval."""
        self._update_state()

    @callback
    def _update_state(self) -> None:
        """Compute and set the entity state. Override in subclasses."""
        raise NotImplementedError
