"""Button platform for Lifecycle Monitor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.util import dt as dt_util

from .const import (
    CONF_DEVICE_TYPE,
    CONF_LAST_REPLACED,
    DEVICE_TYPE_BATTERY,
    DEVICE_TYPE_MAINTENANCE,
)
from .data import LifecycleEntity, get_attached_device, get_entry_name

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    device_type = entry.data[CONF_DEVICE_TYPE]
    attached_device = get_attached_device(hass, entry)
    if device_type == DEVICE_TYPE_BATTERY:
        async_add_entities([BatteryReplacedButton(entry, attached_device)])
    elif device_type == DEVICE_TYPE_MAINTENANCE:
        async_add_entities([MarkAsDoneButton(entry, attached_device)])


class _LifecycleButtonBase(LifecycleEntity, ButtonEntity):
    """Base class for Lifecycle Monitor buttons."""

    _attr_entity_category = EntityCategory.CONFIG

    async def async_press(self) -> None:
        """Handle the button press."""
        new_options = {
            **self._entry.options,
            CONF_LAST_REPLACED: dt_util.utcnow().isoformat(),
        }
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)


class BatteryReplacedButton(_LifecycleButtonBase):
    """Button to reset the battery replacement date."""

    _attr_translation_key = "battery_replaced"
    _attr_suggested_object_id = "battery_replaced"
    _attr_icon = "mdi:battery-sync"

    def __init__(
        self,
        entry: ConfigEntry,
        attached_device: dr.DeviceEntry | None = None,
    ) -> None:
        """Initialize the button."""
        super().__init__(entry, attached_device)
        self._attr_unique_id = f"{entry.entry_id}_battery_replaced"


class MarkAsDoneButton(_LifecycleButtonBase):
    """Button to mark maintenance as done."""

    _attr_translation_key = "mark_as_done"
    _attr_suggested_object_id = "mark_as_done"
    _attr_icon = "mdi:check-circle"

    @property
    def name(self) -> str | None:
        """Return the name with user-provided prefix."""
        entry_name = get_entry_name(self._entry)
        base = self._get_translated_base_name("Mark as done")
        return f"{entry_name} {base}" if entry_name else base

    def __init__(
        self,
        entry: ConfigEntry,
        attached_device: dr.DeviceEntry | None = None,
    ) -> None:
        """Initialize the button."""
        super().__init__(entry, attached_device)
        self._attr_unique_id = f"{entry.entry_id}_mark_done"
