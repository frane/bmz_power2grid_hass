from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS, DEFAULT_PORT, DEFAULT_UNIT
from .coordinator import BmzCoordinator

LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host: str = entry.data["host"]
    port: int = entry.data.get("port", DEFAULT_PORT)
    unit: int = entry.data.get("unit", DEFAULT_UNIT)

    # IMPORTANT: do NOT pass "client=" here.
    # Keep scan interval simple; you can add an option flow later.
    coordinator = BmzCoordinator(
        hass=hass,
        host=host,
        port=port,
        unit=unit,
        scan_interval_s=5,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok