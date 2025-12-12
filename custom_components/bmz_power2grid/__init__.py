from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, CONF_HOST, CONF_PORT, CONF_UNIT_ID, CONF_SCAN_INTERVAL
from .modbus_client import RtuOverTcpClient
from .coordinator import BmzCoordinator

PLATFORMS = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = RtuOverTcpClient(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        timeout=3.0,
    )
    coordinator = BmzCoordinator(
        hass=hass,
        client=client,
        unit_id=entry.data[CONF_UNIT_ID],
        scan_interval=entry.data[CONF_SCAN_INTERVAL],
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok