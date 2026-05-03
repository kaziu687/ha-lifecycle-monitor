"""Config flow for Lifecycle Monitor."""

from __future__ import annotations

import uuid

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.helpers import selector
from homeassistant.util import dt as dt_util

from custom_components.lifecycle_monitor.const import (
    CONF_BATTERY_LIFESPAN,
    CONF_DEVICE_TYPE,
    CONF_END_DATE,
    CONF_INTERVAL_DAYS,
    CONF_LAST_REPLACED,
    CONF_LOW_THRESHOLD,
    CONF_NAME,
    CONF_WARNING_THRESHOLD,
    DEVICE_TYPE_BATTERY,
    DEVICE_TYPE_FIXED_DATE,
    DEVICE_TYPE_MAINTENANCE,
    DOMAIN,
)

from .helpers import build_entry_title, build_options, device_selector
from .options import LifecycleMonitorOptionsFlow


class LifecycleMonitorFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Lifecycle Monitor."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle device type selection."""
        if user_input is not None:
            device_type = user_input[CONF_DEVICE_TYPE]
            if device_type == DEVICE_TYPE_BATTERY:
                return await self.async_step_battery()
            if device_type == DEVICE_TYPE_MAINTENANCE:
                return await self.async_step_maintenance()
            if device_type == DEVICE_TYPE_FIXED_DATE:
                return await self.async_step_fixed_date()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_TYPE): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(
                                    value=DEVICE_TYPE_BATTERY,
                                    label="Virtual Battery",
                                ),
                                selector.SelectOptionDict(
                                    value=DEVICE_TYPE_MAINTENANCE,
                                    label="Maintenance Interval",
                                ),
                                selector.SelectOptionDict(
                                    value=DEVICE_TYPE_FIXED_DATE,
                                    label="Fixed Date",
                                ),
                            ],
                        ),
                    ),
                },
            ),
        )

    async def async_step_battery(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Configure a Virtual Battery device."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_BATTERY_LIFESPAN] <= 0:
                errors["base"] = "invalid_duration"
            else:
                await self.async_set_unique_id(str(uuid.uuid4()))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=build_entry_title(
                        self.hass, user_input[CONF_NAME],
                        user_input.get(CONF_DEVICE_ID),
                    ),
                    data={
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_DEVICE_TYPE: DEVICE_TYPE_BATTERY,
                    },
                    options=build_options(
                        {},
                        user_input,
                        {
                            CONF_BATTERY_LIFESPAN: user_input[CONF_BATTERY_LIFESPAN],
                            CONF_LOW_THRESHOLD: user_input.get(CONF_LOW_THRESHOLD, 0),
                            CONF_LAST_REPLACED: dt_util.utcnow().isoformat(),
                        },
                    ),
                )

        return self.async_show_form(
            step_id="battery",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        default=(user_input or {}).get(CONF_NAME, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(
                        CONF_BATTERY_LIFESPAN,
                        default=(user_input or {}).get(CONF_BATTERY_LIFESPAN, 365),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="days",
                        ),
                    ),
                    vol.Optional(
                        CONF_LOW_THRESHOLD,
                        default=(user_input or {}).get(CONF_LOW_THRESHOLD, 0),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="days",
                        ),
                    ),
                    **device_selector(),
                },
            ),
            errors=errors,
        )

    async def async_step_maintenance(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Configure a Maintenance Interval device."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_INTERVAL_DAYS] <= 0:
                errors["base"] = "invalid_duration"
            else:
                await self.async_set_unique_id(str(uuid.uuid4()))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=build_entry_title(
                        self.hass, user_input[CONF_NAME],
                        user_input.get(CONF_DEVICE_ID),
                    ),
                    data={
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_DEVICE_TYPE: DEVICE_TYPE_MAINTENANCE,
                    },
                    options=build_options(
                        {},
                        user_input,
                        {
                            CONF_INTERVAL_DAYS: user_input[CONF_INTERVAL_DAYS],
                            CONF_WARNING_THRESHOLD: user_input.get(
                                CONF_WARNING_THRESHOLD, 0
                            ),
                            CONF_LAST_REPLACED: dt_util.utcnow().isoformat(),
                        },
                    ),
                )

        return self.async_show_form(
            step_id="maintenance",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        default=(user_input or {}).get(CONF_NAME, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(
                        CONF_INTERVAL_DAYS,
                        default=(user_input or {}).get(CONF_INTERVAL_DAYS, 365),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="days",
                        ),
                    ),
                    vol.Optional(
                        CONF_WARNING_THRESHOLD,
                        default=(user_input or {}).get(CONF_WARNING_THRESHOLD, 0),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="days",
                        ),
                    ),
                    **device_selector(),
                },
            ),
            errors=errors,
        )

    async def async_step_fixed_date(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Configure a Fixed Date device."""
        errors: dict[str, str] = {}
        if user_input is not None:
            end_date = user_input.get(CONF_END_DATE)
            if not end_date:
                errors["base"] = "invalid_date"
            else:
                await self.async_set_unique_id(str(uuid.uuid4()))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=build_entry_title(
                        self.hass, user_input[CONF_NAME],
                        user_input.get(CONF_DEVICE_ID),
                    ),
                    data={
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_DEVICE_TYPE: DEVICE_TYPE_FIXED_DATE,
                    },
                    options=build_options(
                        {},
                        user_input,
                        {
                            CONF_END_DATE: dt_util.as_local(end_date).isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date,
                            CONF_WARNING_THRESHOLD: user_input.get(
                                CONF_WARNING_THRESHOLD, 0
                            ),
                        },
                    ),
                )

        return self.async_show_form(
            step_id="fixed_date",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        default=(user_input or {}).get(CONF_NAME, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(
                        CONF_END_DATE,
                        default=(user_input or {}).get(CONF_END_DATE),
                    ): selector.DateTimeSelector(
                        selector.DateTimeSelectorConfig(),
                    ),
                    vol.Optional(
                        CONF_WARNING_THRESHOLD,
                        default=(user_input or {}).get(CONF_WARNING_THRESHOLD, 0),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="days",
                        ),
                    ),
                    **device_selector(),
                },
            ),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> LifecycleMonitorOptionsFlow:
        """Get the options flow for this handler."""
        return LifecycleMonitorOptionsFlow(config_entry)
