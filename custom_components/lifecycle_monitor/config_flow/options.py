"""Options flow for Lifecycle Monitor."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.util import dt as dt_util

from custom_components.lifecycle_monitor.const import (
    CONF_BATTERY_LIFESPAN,
    CONF_DEVICE_TYPE,
    CONF_END_DATE,
    CONF_INTERVAL_DAYS,
    CONF_LOW_THRESHOLD,
    CONF_NAME,
    CONF_WARNING_THRESHOLD,
    DEVICE_TYPE_BATTERY,
    DEVICE_TYPE_FIXED_DATE,
    DEVICE_TYPE_MAINTENANCE,
)

from .helpers import build_entry_title, build_options


class LifecycleMonitorOptionsFlow(config_entries.OptionsFlow):
    """Options flow for Lifecycle Monitor."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    def _update_entry_title(self, new_options: dict) -> None:
        """Update config entry title to reflect current device attachment."""
        new_title = build_entry_title(
            self.hass,
            self._config_entry.data[CONF_NAME],
            new_options.get("device_id"),
        )
        if new_title != self._config_entry.title:
            self.hass.config_entries.async_update_entry(
                self._config_entry, title=new_title,
            )

    async def async_step_init(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        device_type = self._config_entry.data.get(CONF_DEVICE_TYPE)
        if device_type == DEVICE_TYPE_BATTERY:
            return await self.async_step_battery(user_input)
        if device_type == DEVICE_TYPE_MAINTENANCE:
            return await self.async_step_maintenance(user_input)
        if device_type == DEVICE_TYPE_FIXED_DATE:
            return await self.async_step_fixed_date(user_input)
        return self.async_abort(reason="unknown_device_type")

    async def async_step_battery(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Manage Virtual Battery options."""
        if user_input is not None:
            if user_input[CONF_BATTERY_LIFESPAN] <= 0:
                return self.async_show_form(
                    step_id="battery",
                    errors={"base": "invalid_duration"},
                    data_schema=self._build_battery_schema(),
                )
            new_options = build_options(
                self._config_entry.options,
                user_input,
                {
                    CONF_BATTERY_LIFESPAN: user_input[CONF_BATTERY_LIFESPAN],
                    CONF_LOW_THRESHOLD: user_input.get(CONF_LOW_THRESHOLD, 0),
                },
            )
            if user_input.get("unassign_device"):
                new_options.pop("device_id", None)
            self._update_entry_title(new_options)
            return self.async_create_entry(title="", data=new_options)

        return self.async_show_form(
            step_id="battery",
            data_schema=self._build_battery_schema(),
        )

    async def async_step_maintenance(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Manage Maintenance Interval options."""
        if user_input is not None:
            if user_input[CONF_INTERVAL_DAYS] <= 0:
                return self.async_show_form(
                    step_id="maintenance",
                    errors={"base": "invalid_duration"},
                    data_schema=self._build_maintenance_schema(),
                )
            new_options = build_options(
                self._config_entry.options,
                user_input,
                {
                    CONF_INTERVAL_DAYS: user_input[CONF_INTERVAL_DAYS],
                    CONF_WARNING_THRESHOLD: user_input.get(
                        CONF_WARNING_THRESHOLD, 0
                    ),
                },
            )
            if user_input.get("unassign_device"):
                new_options.pop("device_id", None)
            self._update_entry_title(new_options)
            return self.async_create_entry(title="", data=new_options)

        return self.async_show_form(
            step_id="maintenance",
            data_schema=self._build_maintenance_schema(),
        )

    def _build_battery_schema(self) -> vol.Schema:
        """Build the battery options schema."""
        schema: dict[vol.Marker, selector.Selector] = {
            vol.Required(
                CONF_BATTERY_LIFESPAN,
                default=self._config_entry.options.get(CONF_BATTERY_LIFESPAN, 365),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="days",
                ),
            ),
            vol.Optional(
                CONF_LOW_THRESHOLD,
                default=self._config_entry.options.get(CONF_LOW_THRESHOLD, 0),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="days",
                ),
            ),
            vol.Optional(
                "device_id",
                default=self._config_entry.options.get("device_id")
                or vol.UNDEFINED,
            ): selector.DeviceSelector(),
        }
        if self._config_entry.options.get("device_id"):
            schema[vol.Optional("unassign_device", default=False)] = (
                selector.BooleanSelector()
            )
        return vol.Schema(schema)

    def _build_maintenance_schema(self) -> vol.Schema:
        """Build the maintenance options schema."""
        schema: dict[vol.Marker, selector.Selector] = {
            vol.Required(
                CONF_INTERVAL_DAYS,
                default=self._config_entry.options.get(CONF_INTERVAL_DAYS, 365),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="days",
                ),
            ),
            vol.Optional(
                CONF_WARNING_THRESHOLD,
                default=self._config_entry.options.get(CONF_WARNING_THRESHOLD, 0),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="days",
                ),
            ),
            vol.Optional(
                "device_id",
                default=self._config_entry.options.get("device_id")
                or vol.UNDEFINED,
            ): selector.DeviceSelector(),
        }
        if self._config_entry.options.get("device_id"):
            schema[vol.Optional("unassign_device", default=False)] = (
                selector.BooleanSelector()
            )
        return vol.Schema(schema)

    async def async_step_fixed_date(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Manage Fixed Date options."""
        if user_input is not None:
            end_date = user_input.get(CONF_END_DATE)
            if not end_date:
                return self.async_show_form(
                    step_id="fixed_date",
                    errors={"base": "invalid_date"},
                    data_schema=self._build_fixed_date_schema(),
                )
            new_options = build_options(
                self._config_entry.options,
                user_input,
                {
                    CONF_END_DATE: dt_util.as_local(end_date).isoformat()
                    if hasattr(end_date, "isoformat")
                    else end_date,
                    CONF_WARNING_THRESHOLD: user_input.get(
                        CONF_WARNING_THRESHOLD, 0
                    ),
                },
            )
            if user_input.get("unassign_device"):
                new_options.pop("device_id", None)
            self._update_entry_title(new_options)
            return self.async_create_entry(title="", data=new_options)

        return self.async_show_form(
            step_id="fixed_date",
            data_schema=self._build_fixed_date_schema(),
        )

    def _build_fixed_date_schema(self) -> vol.Schema:
        """Build the fixed date options schema."""
        end_date_str = self._config_entry.options.get(CONF_END_DATE)
        end_date_default = None
        if end_date_str:
            parsed = dt_util.parse_datetime(end_date_str)
            if parsed:
                end_date_default = parsed

        schema: dict[vol.Marker, selector.Selector] = {
            vol.Required(
                CONF_END_DATE,
                default=end_date_default,
            ): selector.DateTimeSelector(
                selector.DateTimeSelectorConfig(),
            ),
            vol.Optional(
                CONF_WARNING_THRESHOLD,
                default=self._config_entry.options.get(CONF_WARNING_THRESHOLD, 0),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="days",
                ),
            ),
            vol.Optional(
                "device_id",
                default=self._config_entry.options.get("device_id")
                or vol.UNDEFINED,
            ): selector.DeviceSelector(),
        }
        if self._config_entry.options.get("device_id"):
            schema[vol.Optional("unassign_device", default=False)] = (
                selector.BooleanSelector()
            )
        return vol.Schema(schema)
