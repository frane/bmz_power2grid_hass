from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DEFAULT_SCAN_INTERVAL,
    REG_PV_POWER_W_INT32,
    REG_BATTERY_POWER_W_INT32,
    REG_BATTERY_SOC_PCT_U16,
    REG_BATTERY_SOH_PCT_U16,
    REG_INVERTER_TEMP_C_U16,
    REG_BATTERY_TEMP_C_U16,
    REG_GRID_L1_BLOCK_U16,
    REG_GRID_L2_BLOCK_U16,
    SCALE_SOC, SCALE_SOH, SCALE_INVERTER_TEMP, SCALE_BATTERY_TEMP,
    SCALE_GRID_V, SCALE_GRID_A, SCALE_GRID_HZ,
)
from .modbus_client import RtuOverTcpClient, regs_to_s32_be

class BmzCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, client: RtuOverTcpClient, unit_id: int, scan_interval: int) -> None:
        super().__init__(
            hass,
            logger=None,
            name="BMZ Power2Grid",
            update_interval=timedelta(seconds=scan_interval or DEFAULT_SCAN_INTERVAL),
        )
        self._client = client
        self._unit = unit_id

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            # Read blocks efficiently (few calls, stable)
            pv_regs = await self._client.read_holding_registers(self._unit, REG_PV_POWER_W_INT32, 2)
            bat_regs = await self._client.read_holding_registers(self._unit, REG_BATTERY_POWER_W_INT32, 2)

            soc_regs = await self._client.read_holding_registers(self._unit, REG_BATTERY_SOC_PCT_U16, 1)
            soh_regs = await self._client.read_holding_registers(self._unit, REG_BATTERY_SOH_PCT_U16, 1)

            inv_t_regs = await self._client.read_holding_registers(self._unit, REG_INVERTER_TEMP_C_U16, 1)
            bat_t_regs = await self._client.read_holding_registers(self._unit, REG_BATTERY_TEMP_C_U16, 1)

            l1 = await self._client.read_holding_registers(self._unit, REG_GRID_L1_BLOCK_U16, 3)
            l2 = await self._client.read_holding_registers(self._unit, REG_GRID_L2_BLOCK_U16, 3)

            pv_w = regs_to_s32_be(pv_regs)
            bat_w = regs_to_s32_be(bat_regs)

            # Derived
            battery_charge_w = max(-bat_w, 0)       # charging = negative raw
            battery_discharge_w = max(bat_w, 0)

            return {
                "pv_power_w": pv_w,
                "battery_power_w": bat_w,
                "battery_charge_w": battery_charge_w,
                "battery_discharge_w": battery_discharge_w,

                "battery_soc_pct": soc_regs[0] * SCALE_SOC,
                "battery_soh_pct": soh_regs[0] * SCALE_SOH,

                "inverter_temp_c": inv_t_regs[0] * SCALE_INVERTER_TEMP,
                "battery_temp_c": bat_t_regs[0] * SCALE_BATTERY_TEMP,

                "grid_l1_v": l1[0] * SCALE_GRID_V,
                "grid_l1_a": l1[1] * SCALE_GRID_A,
                "grid_l1_hz": l1[2] * SCALE_GRID_HZ,

                "grid_l2_v": l2[0] * SCALE_GRID_V,
                "grid_l2_a": l2[1] * SCALE_GRID_A,
                "grid_l2_hz": l2[2] * SCALE_GRID_HZ,
            }

        except Exception as err:
            raise UpdateFailed(str(err)) from err