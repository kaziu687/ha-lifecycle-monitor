"""Binary sensor platform for Lifecycle Monitor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import callback
from homeassistant.util import dt as dt_util

from .const import (
    CONF_BATTERY_LIFESPAN,
    CONF_DEVICE_TYPE,
    CONF_END_DATE,
    CONF_INTERVAL_DAYS,
    CONF_LOW_THRESHOLD,
    CONF_WARNING_THRESHOLD,
    DEVICE_TYPE_BATTERY,
    DEVICE_TYPE_FIXED_DATE,
    DEVICE_TYPE_MAINTENANCE,
)
from .data import (
    LifecyclePolledEntity,
    get_attached_device,
    get_elapsed_days,
    get_entry_name,
)

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
    """Set up the binary_sensor platform."""
    device_type = entry.data[CONF_DEVICE_TYPE]
    attached_device = get_attached_device(hass, entry)
    if device_type == DEVICE_TYPE_BATTERY:
        async_add_entities([BatteryLowBinarySensor(entry, attached_device)])
    elif device_type == DEVICE_TYPE_MAINTENANCE:
        async_add_entities(
            [
                MaintenanceWarningBinarySensor(entry, attached_device),
                MaintenanceOverdueBinarySensor(entry, attached_device),
            ]
        )
    elif device_type == DEVICE_TYPE_FIXED_DATE:
        async_add_entities(
            [
                FixedDateWarningBinarySensor(entry, attached_device),
                FixedDateOverdueBinarySensor(entry, attached_device),
            ]
        )


class _LifecycleBinarySensorBase(LifecyclePolledEntity, BinarySensorEntity):
    """Base class for Lifecycle Monitor binary sensors."""

    def __init__(
        self,
        entry: ConfigEntry,
        unique_id_suffix: str,
        attached_device: dr.DeviceEntry | None = None,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(entry, attached_device)
        self._attr_unique_id = f"{entry.entry_id}_{unique_id_suffix}"


class BatteryLowBinarySensor(_LifecycleBinarySensorBase):
    """Binary sensor that turns on when battery is below low threshold."""

    _attr_device_class = BinarySensorDeviceClass.BATTERY
    _attr_suggested_object_id = "battery_low"

    def __init__(
        self,
        entry: ConfigEntry,
        attached_device: dr.DeviceEntry | None = None,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(entry, "battery_low", attached_device)

    @callback
    def _update_state(self) -> None:
        """Compute and set the battery low state."""
        low_threshold = self._entry.options.get(CONF_LOW_THRESHOLD, 0)
        if low_threshold <= 0:
            new_state = False
        else:
            elapsed_days = get_elapsed_days(self._entry)
            if elapsed_days is None:
                new_state = False
            else:
                lifespan_days = self._entry.options.get(CONF_BATTERY_LIFESPAN, 365)
                remaining_days = lifespan_days - elapsed_days
                new_state = remaining_days <= low_threshold
        if self._attr_is_on == new_state:
            return
        self._attr_is_on = new_state
        self.async_write_ha_state()


class MaintenanceWarningBinarySensor(_LifecycleBinarySensorBase):
    """Binary sensor that turns on when maintenance is approaching."""

    _attr_translation_key = "warning"
    _attr_suggested_object_id = "warning"

    @property
    def name(self) -> str | None:
        """Return the name with user-provided prefix."""
        entry_name = get_entry_name(self._entry)
        base = self._get_translated_base_name("Warning")
        return f"{entry_name} {base}" if entry_name else base

    def __init__(
        self,
        entry: ConfigEntry,
        attached_device: dr.DeviceEntry | None = None,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(entry, "warning", attached_device)

    @callback
    def _update_state(self) -> None:
        """Compute and set the warning state."""
        warning_threshold = self._entry.options.get(CONF_WARNING_THRESHOLD, 0)
        if warning_threshold <= 0:
            new_state = False
        else:
            elapsed_days = get_elapsed_days(self._entry)
            if elapsed_days is None:
                new_state = False
            else:
                interval_days = self._entry.options.get(CONF_INTERVAL_DAYS, 365)
                remaining_days = interval_days - elapsed_days
                new_state = remaining_days <= warning_threshold
        if self._attr_is_on == new_state:
            return
        self._attr_is_on = new_state
        self.async_write_ha_state()


class MaintenanceOverdueBinarySensor(_LifecycleBinarySensorBase):
    """Binary sensor that turns on when maintenance is overdue."""

    _attr_translation_key = "overdue"
    _attr_suggested_object_id = "overdue"

    @property
    def name(self) -> str | None:
        """Return the name with user-provided prefix."""
        entry_name = get_entry_name(self._entry)
        base = self._get_translated_base_name("Overdue")
        return f"{entry_name} {base}" if entry_name else base

    def __init__(
        self,
        entry: ConfigEntry,
        attached_device: dr.DeviceEntry | None = None,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(entry, "overdue", attached_device)

    @callback
    def _update_state(self) -> None:
        """Compute and set the overdue state."""
        elapsed_days = get_elapsed_days(self._entry)
        if elapsed_days is None:
            new_state = False
        else:
            interval_days = self._entry.options.get(CONF_INTERVAL_DAYS, 365)
            new_state = (interval_days - elapsed_days) <= 0
        if self._attr_is_on == new_state:
            return
        self._attr_is_on = new_state
        self.async_write_ha_state()


def _get_fixed_date_remaining(entry: ConfigEntry) -> float | None:
    """Get days remaining for a fixed date entry."""
    end_date_str = entry.options.get(CONF_END_DATE)
    if end_date_str is None:
        return None
    end_date = dt_util.parse_datetime(end_date_str)
    if end_date is None:
        return None
    return (dt_util.as_local(end_date) - dt_util.now()).total_seconds() / 86400


class FixedDateWarningBinarySensor(_LifecycleBinarySensorBase):
    """Binary sensor that turns on when fixed date is approaching."""

    _attr_translation_key = "warning"
    _attr_suggested_object_id = "warning"

    @property
    def name(self) -> str | None:
        """Return the name with user-provided prefix."""
        entry_name = get_entry_name(self._entry)
        base = self._get_translated_base_name("Warning")
        return f"{entry_name} {base}" if entry_name else base

    def __init__(
        self,
        entry: ConfigEntry,
        attached_device: dr.DeviceEntry | None = None,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(entry, "warning", attached_device)

    @callback
    def _update_state(self) -> None:
        """Compute and set the warning state."""
        warning_threshold = self._entry.options.get(CONF_WARNING_THRESHOLD, 0)
        if warning_threshold <= 0:
            new_state = False
        else:
            remaining = _get_fixed_date_remaining(self._entry)
            new_state = remaining is not None and remaining <= warning_threshold
        if self._attr_is_on == new_state:
            return
        self._attr_is_on = new_state
        self.async_write_ha_state()


class FixedDateOverdueBinarySensor(_LifecycleBinarySensorBase):
    """Binary sensor that turns on when fixed date has passed."""

    _attr_translation_key = "overdue"
    _attr_suggested_object_id = "overdue"

    @property
    def name(self) -> str | None:
        """Return the name with user-provided prefix."""
        entry_name = get_entry_name(self._entry)
        base = self._get_translated_base_name("Overdue")
        return f"{entry_name} {base}" if entry_name else base

    def __init__(
        self,
        entry: ConfigEntry,
        attached_device: dr.DeviceEntry | None = None,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(entry, "overdue", attached_device)

    @callback
    def _update_state(self) -> None:
        """Compute and set the overdue state."""
        remaining = _get_fixed_date_remaining(self._entry)
        new_state = remaining is not None and remaining <= 0
        if self._attr_is_on == new_state:
            return
        self._attr_is_on = new_state
        self.async_write_ha_state()
