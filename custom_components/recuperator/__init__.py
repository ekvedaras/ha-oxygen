"""Recuperator integration for Home Assistant."""
import logging
import asyncio
import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, Platform

_LOGGER = logging.getLogger(__name__)

# Define platforms that this integration supports
PLATFORMS = [Platform.SENSOR, Platform.FAN]

# Configuration constants
DEFAULT_HOST = "192.168.1.255"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Recuperator from a config entry."""
    # Get the host from the config entry or use the default
    host = entry.data.get(CONF_HOST, DEFAULT_HOST)

    # Create a session to communicate with the device
    session = aiohttp.ClientSession()

    # Store the host and session in hass.data
    hass.data.setdefault(entry.entry_id, {})
    hass.data[entry.entry_id]["host"] = host
    hass.data[entry.entry_id]["session"] = session

    # Set up the platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register a callback to close the session when unloading
    entry.async_on_unload(entry.add_update_listener(update_listener))
    entry.async_on_unload(lambda: close_session(hass, entry))

    return True

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Close the session
    if unload_ok:
        await close_session(hass, entry)

    return unload_ok

async def close_session(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Close the session."""
    if "session" in hass.data[entry.entry_id]:
        await hass.data[entry.entry_id]["session"].close()
        hass.data[entry.entry_id].pop("session")