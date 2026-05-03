"""Shared helpers for Lifecycle Monitor config flow."""

from __future__ import annotations

from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import selector

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


def build_entry_title(
    hass: HomeAssistant, name: str, device_id: str | None,
) -> str:
    """Build config entry title with attached device name."""
    if not device_id:
        return name
    device = dr.async_get(hass).async_get(device_id)
    if not device or not (device_name := device.name_by_user or device.name):
        return name
    return f"{name} ({device_name})"


def build_options(
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


def device_selector(
    default: str | None = None,
) -> dict[vol.Optional, selector.DeviceSelector]:
    """Return a device selector field."""
    return {
        vol.Optional(
            CONF_DEVICE_ID,
            default=default or vol.UNDEFINED,
        ): selector.DeviceSelector(),
    }
