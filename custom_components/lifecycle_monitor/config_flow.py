"""Config flow for Lifecycle Monitor."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import selector
from homeassistant.util import dt as dt_util

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

from .const import (
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


def _build_entry_title(
    hass: HomeAssistant, name: str, device_id: str | None,
) -> str:
    """Build config entry title with attached device name."""
    if not device_id:
        return name
    device = dr.async_get(hass).async_get(device_id)
    if not device or not (device_name := device.name_by_user or device.name):
        return name
    return f"{name} ({device_name})"


def _build_options(
    base: dict,
    user_input: dict,
    extra_fields: dict[str, object],
) -> dict:
    """Build options dict, only including CONF_DEVICE_ID when selected."""
    options = {**base, **extra_fields}
    if device_id := user_input.get(CONF_DEVICE_ID):
        options[CONF_DEVICE_ID] = device_id
    else:
        options.pop(CONF_DEVICE_ID, None)
    return options


class LifecycleMonitorFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Lifecycle Monitor."""

    VERSION = 1
    MINOR_VERSION = 1

    @staticmethod
    def _device_selector(
        default: str | None = None,
    ) -> dict[vol.Optional, selector.DeviceSelector]:
        return {
            vol.Optional(
                CONF_DEVICE_ID,
                default=default or vol.UNDEFINED,
            ): selector.DeviceSelector(),
        }

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
                    title=_build_entry_title(
                        self.hass, user_input[CONF_NAME],
                        user_input.get(CONF_DEVICE_ID),
                    ),
                    data={
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_DEVICE_TYPE: DEVICE_TYPE_BATTERY,
                    },
                    options=_build_options(
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
                    **self._device_selector(),
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
                    title=_build_entry_title(
                        self.hass, user_input[CONF_NAME],
                        user_input.get(CONF_DEVICE_ID),
                    ),
                    data={
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_DEVICE_TYPE: DEVICE_TYPE_MAINTENANCE,
                    },
                    options=_build_options(
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
                    **self._device_selector(),
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
                    title=_build_entry_title(
                        self.hass, user_input[CONF_NAME],
                        user_input.get(CONF_DEVICE_ID),
                    ),
                    data={
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_DEVICE_TYPE: DEVICE_TYPE_FIXED_DATE,
                    },
                    options=_build_options(
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
                    **self._device_selector(),
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


class LifecycleMonitorOptionsFlow(config_entries.OptionsFlow):
    """Options flow for Lifecycle Monitor."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    def _update_entry_title(self, new_options: dict) -> None:
        """Update config entry title to reflect current device attachment."""
        new_title = _build_entry_title(
            self.hass,
            self._config_entry.data[CONF_NAME],
            new_options.get(CONF_DEVICE_ID),
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
            new_options = _build_options(
                self._config_entry.options,
                user_input,
                {
                    CONF_BATTERY_LIFESPAN: user_input[CONF_BATTERY_LIFESPAN],
                    CONF_LOW_THRESHOLD: user_input.get(CONF_LOW_THRESHOLD, 0),
                },
            )
            if user_input.get("unassign_device"):
                new_options.pop(CONF_DEVICE_ID, None)
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
            new_options = _build_options(
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
                new_options.pop(CONF_DEVICE_ID, None)
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
                CONF_DEVICE_ID,
                default=self._config_entry.options.get(CONF_DEVICE_ID)
                or vol.UNDEFINED,
            ): selector.DeviceSelector(),
        }
        if self._config_entry.options.get(CONF_DEVICE_ID):
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
                CONF_DEVICE_ID,
                default=self._config_entry.options.get(CONF_DEVICE_ID)
                or vol.UNDEFINED,
            ): selector.DeviceSelector(),
        }
        if self._config_entry.options.get(CONF_DEVICE_ID):
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
            new_options = _build_options(
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
                new_options.pop(CONF_DEVICE_ID, None)
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
                CONF_DEVICE_ID,
                default=self._config_entry.options.get(CONF_DEVICE_ID)
                or vol.UNDEFINED,
            ): selector.DeviceSelector(),
        }
        if self._config_entry.options.get(CONF_DEVICE_ID):
            schema[vol.Optional("unassign_device", default=False)] = (
                selector.BooleanSelector()
            )
        return vol.Schema(schema)
