"""Lifecycle Monitor integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_DEVICE_ID, Platform
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.DATETIME,
    Platform.SENSOR,
]


def _cleanup_standalone_device(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove orphaned standalone device when entry is attached elsewhere."""
    if not entry.options.get(CONF_DEVICE_ID):
        return
    device_reg = dr.async_get(hass)
    standalone = device_reg.async_get_device(
        identifiers={(DOMAIN, entry.entry_id)},
    )
    if standalone is not None:
        device_reg.async_remove_device(standalone.id)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up lifecycle_monitor from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _cleanup_standalone_device(hass, entry)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
