"""Sensor platform for Lifecycle Monitor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import callback
from homeassistant.helpers.entity_platform import current_platform
from homeassistant.util import dt as dt_util

from .const import (
    CONF_BATTERY_LIFESPAN,
    CONF_DEVICE_TYPE,
    CONF_END_DATE,
    CONF_INTERVAL_DAYS,
    CONF_LAST_REPLACED,
    DEVICE_TYPE_BATTERY,
    DEVICE_TYPE_FIXED_DATE,
    DEVICE_TYPE_MAINTENANCE,
)
from .data import LifecyclePolledEntity, get_attached_device, get_elapsed_days

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
    """Set up the sensor platform."""
    device_type = entry.data[CONF_DEVICE_TYPE]
    attached_device = get_attached_device(hass, entry)
    if device_type == DEVICE_TYPE_BATTERY:
        async_add_entities([TimedBatterySensor(entry, attached_device)])
    elif device_type == DEVICE_TYPE_MAINTENANCE:
        async_add_entities([MaintenanceDaysRemainingSensor(entry, attached_device)])
    elif device_type == DEVICE_TYPE_FIXED_DATE:
        async_add_entities([FixedDateDaysRemainingSensor(entry, attached_device)])

    platform = current_platform.get()
    if device_type == DEVICE_TYPE_BATTERY:
        platform.async_register_entity_service("reset_battery", {}, "async_reset")
    elif device_type == DEVICE_TYPE_MAINTENANCE:
        platform.async_register_entity_service("mark_as_done", {}, "async_mark_done")


class LifecycleSensorEntity(LifecyclePolledEntity, SensorEntity):
    """Base class for Lifecycle Monitor sensor entities."""

    _attr_unique_id: str | None = None

    def __init__(
        self,
        entry: ConfigEntry,
        attached_device: dr.DeviceEntry | None = None,
    ) -> None:
        """Initialize the entity."""
        super().__init__(entry, attached_device)
        self._attr_unique_id = entry.entry_id


class TimedBatterySensor(LifecycleSensorEntity):
    """Sensor that represents a battery draining over time."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_suggested_object_id = "battery"

    @callback
    def _update_state(self) -> None:
        """Compute and set the battery percentage."""
        elapsed_days = get_elapsed_days(self._entry)
        if elapsed_days is None:
            if self._attr_native_value is None:
                return
            self._attr_native_value = None
            self.async_write_ha_state()
            return

        lifespan_days = self._entry.options.get(CONF_BATTERY_LIFESPAN, 365) or 1
        percentage = round(max(0, min(100, 100 - (elapsed_days / lifespan_days * 100))))
        if self._attr_native_value == percentage:
            return
        self._attr_native_value = percentage
        self.async_write_ha_state()

    async def async_reset(self, **_: object) -> None:
        """Reset the battery to 100%."""
        new_options = {
            **self._entry.options,
            CONF_LAST_REPLACED: dt_util.utcnow().isoformat(),
        }
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)
        self._update_state()


class MaintenanceDaysRemainingSensor(LifecycleSensorEntity):
    """Sensor showing days remaining until maintenance is due."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_translation_key = "days_remaining"
    _attr_suggested_object_id = "days_remaining"

    @callback
    def _update_state(self) -> None:
        """Compute and set the days remaining."""
        elapsed_days = get_elapsed_days(self._entry)
        if elapsed_days is None:
            if self._attr_native_value is None:
                return
            self._attr_native_value = None
            self.async_write_ha_state()
            return

        interval_days = self._entry.options.get(CONF_INTERVAL_DAYS, 365)
        remaining = round(interval_days - elapsed_days, 1)
        if self._attr_native_value == remaining:
            return
        self._attr_native_value = remaining
        self.async_write_ha_state()

    async def async_mark_done(self, **_: object) -> None:
        """Mark maintenance as done."""
        new_options = {
            **self._entry.options,
            CONF_LAST_REPLACED: dt_util.utcnow().isoformat(),
        }
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)
        self._update_state()


class FixedDateDaysRemainingSensor(LifecycleSensorEntity):
    """Sensor showing days remaining until a fixed end date."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_translation_key = "days_remaining"
    _attr_suggested_object_id = "days_remaining"

    @callback
    def _update_state(self) -> None:
        """Compute and set the days remaining until end date."""
        end_date_str = self._entry.options.get(CONF_END_DATE)
        if end_date_str is None:
            if self._attr_native_value is None:
                return
            self._attr_native_value = None
            self.async_write_ha_state()
            return
        end_date = dt_util.parse_datetime(end_date_str)
        if end_date is None:
            if self._attr_native_value is None:
                return
            self._attr_native_value = None
            self.async_write_ha_state()
            return
        remaining = round(
            (dt_util.as_local(end_date) - dt_util.now()).total_seconds() / 86400,
            1,
        )
        if self._attr_native_value == remaining:
            return
        self._attr_native_value = remaining
        self.async_write_ha_state()
