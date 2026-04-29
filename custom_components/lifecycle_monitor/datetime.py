"""Datetime platform for Lifecycle Monitor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.datetime import DateTimeEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.util import dt as dt_util

from .const import (
    CONF_DEVICE_TYPE,
    CONF_END_DATE,
    CONF_LAST_REPLACED,
    DEVICE_TYPE_BATTERY,
    DEVICE_TYPE_FIXED_DATE,
    DEVICE_TYPE_MAINTENANCE,
)
from .data import LifecycleEntity, get_attached_device

if TYPE_CHECKING:
    import datetime

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the datetime platform."""
    device_type = entry.data[CONF_DEVICE_TYPE]
    attached_device = get_attached_device(hass, entry)
    if device_type == DEVICE_TYPE_BATTERY:
        async_add_entities([BatteryReplacedDateTime(entry, attached_device)])
    elif device_type == DEVICE_TYPE_MAINTENANCE:
        async_add_entities([LastPerformedDateTime(entry, attached_device)])
    elif device_type == DEVICE_TYPE_FIXED_DATE:
        async_add_entities([EndDateDateTime(entry, attached_device)])


class _LifecycleDateTimeBase(LifecycleEntity, DateTimeEntity):
    """Base class for Lifecycle Monitor datetime entities."""

    _attr_entity_category = EntityCategory.CONFIG

    @property
    def native_value(self) -> datetime.datetime | None:
        """Return the stored datetime value."""
        last_replaced_str = self._entry.options.get(CONF_LAST_REPLACED)
        if last_replaced_str is None:
            return None
        parsed = dt_util.parse_datetime(last_replaced_str)
        if parsed is None:
            return None
        return dt_util.as_local(parsed)

    async def async_set_value(self, value: datetime.datetime) -> None:
        """Update the stored datetime."""
        new_options = {
            **self._entry.options,
            CONF_LAST_REPLACED: value.astimezone(dt_util.UTC).isoformat(),
        }
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)


class BatteryReplacedDateTime(_LifecycleDateTimeBase):
    """Datetime entity storing the last battery replacement date."""

    _attr_translation_key = "battery_replaced"
    _attr_suggested_object_id = "battery_replaced"
    _attr_icon = "mdi:battery-clock"

    def __init__(
        self,
        entry: ConfigEntry,
        attached_device: dr.DeviceEntry | None = None,
    ) -> None:
        """Initialize the datetime entity."""
        super().__init__(entry, attached_device)
        self._attr_unique_id = f"{entry.entry_id}_last_replaced"


class LastPerformedDateTime(_LifecycleDateTimeBase):
    """Datetime entity storing the last maintenance date."""

    _attr_translation_key = "last_performed"
    _attr_suggested_object_id = "last_performed"
    _attr_icon = "mdi:calendar-check"

    def __init__(
        self,
        entry: ConfigEntry,
        attached_device: dr.DeviceEntry | None = None,
    ) -> None:
        """Initialize the datetime entity."""
        super().__init__(entry, attached_device)
        self._attr_unique_id = f"{entry.entry_id}_last_performed"


class EndDateDateTime(_LifecycleDateTimeBase):
    """Datetime entity for the fixed end date."""

    _attr_translation_key = "end_date"
    _attr_suggested_object_id = "end_date"
    _attr_icon = "mdi:calendar-end"

    def __init__(
        self,
        entry: ConfigEntry,
        attached_device: dr.DeviceEntry | None = None,
    ) -> None:
        """Initialize the datetime entity."""
        super().__init__(entry, attached_device)
        self._attr_unique_id = f"{entry.entry_id}_end_date"

    @property
    def native_value(self) -> datetime.datetime | None:
        """Return the end date."""
        end_date_str = self._entry.options.get(CONF_END_DATE)
        if end_date_str is None:
            return None
        parsed = dt_util.parse_datetime(end_date_str)
        if parsed is None:
            return None
        return dt_util.as_local(parsed)

    async def async_set_value(self, value: datetime.datetime) -> None:
        """Update the end date."""
        new_options = {
            **self._entry.options,
            CONF_END_DATE: value.astimezone(dt_util.UTC).isoformat(),
        }
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)
