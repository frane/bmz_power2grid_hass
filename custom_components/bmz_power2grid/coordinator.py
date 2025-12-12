from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import (
    DOMAIN,
    CONF_UNIT_ID,
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_UNIT_ID,
    DEFAULT_SCAN_INTERVAL,
    REG_PV_POWER_W_INT32,
    REG_BATTERY_POWER_W_INT32,
    REG_BATTERY_SOC_PCT_U16,
    REG_BATTERY_SOH_PCT_U16,
    REG_INVERTER_TEMP_C_U16,
    REG_BATTERY_TEMP_C_U16,
    REG_GRID_L1_BLOCK_U16,
    REG_GRID_L2_BLOCK_U16,
    REG_GRID_L3_BLOCK_U16,
    REG_GRID_POWER_L123_W_INT32,
    SCALE_SOC,
    SCALE_SOH,
    SCALE_INVERTER_TEMP,
    SCALE_BATTERY_TEMP,
    SCALE_GRID_V,
    SCALE_GRID_A,
    SCALE_GRID_HZ,
    GRID_POWER_SIGN,
)

from .modbus_client import RtuOverTcpClient, regs_to_s32_be

_LOGGER = logging.getLogger(__name__)


class BmzCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry

        host = entry.data.get(CONF_HOST)
        port = entry.data.get(CONF_PORT, DEFAULT_PORT)
        unit_id = entry.data.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)
        scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        self.host = host
        self.port = port
        self.unit_id = unit_id

        self.client = RtuOverTcpClient(host=host, port=port, timeout=3.0)

        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=int(scan_interval)),
        )

    async def _async_update_data(self) -> dict:
        try:
            # --- POWER ---
            pv_regs = await self.client.read_holding_registers(self.unit_id, REG_PV_POWER_W_INT32, 2)
            pv_power_w = regs_to_s32_be(pv_regs)

            batt_regs = await self.client.read_holding_registers(self.unit_id, REG_BATTERY_POWER_W_INT32, 2)
            battery_power_w = regs_to_s32_be(batt_regs)  # your device: negative=charging (as observed)

            battery_charge_w = max(0, -battery_power_w)
            battery_discharge_w = max(0, battery_power_w)

            # --- SOC / SOH ---
            soc_raw = (await self.client.read_holding_registers(self.unit_id, REG_BATTERY_SOC_PCT_U16, 1))[0]
            soh_raw = (await self.client.read_holding_registers(self.unit_id, REG_BATTERY_SOH_PCT_U16, 1))[0]

            battery_soc_pct = round(soc_raw * SCALE_SOC, 2)
            battery_soh_pct = round(soh_raw * SCALE_SOH, 2)

            # --- TEMPERATURES ---
            inv_temp_raw = (await self.client.read_holding_registers(self.unit_id, REG_INVERTER_TEMP_C_U16, 1))[0]
            bat_temp_raw = (await self.client.read_holding_registers(self.unit_id, REG_BATTERY_TEMP_C_U16, 1))[0]

            inverter_temp_c = round(inv_temp_raw * SCALE_INVERTER_TEMP, 2)
            battery_temp_c = round(bat_temp_raw * SCALE_BATTERY_TEMP, 2)

            # --- GRID (per phase V/A/Hz blocks) ---
            # Each block is 3 regs: [V*10, A*100, Hz*100] (based on your confirmed mapping)
            l1 = await self.client.read_holding_registers(self.unit_id, REG_GRID_L1_BLOCK_U16, 3)
            l2 = await self.client.read_holding_registers(self.unit_id, REG_GRID_L2_BLOCK_U16, 3)
            l3 = await self.client.read_holding_registers(self.unit_id, REG_GRID_L3_BLOCK_U16, 3)

            grid_l1_v = round(l1[0] * SCALE_GRID_V, 2)
            grid_l1_a = round(l1[1] * SCALE_GRID_A, 2)
            grid_l1_hz = round(l1[2] * SCALE_GRID_HZ, 2)

            grid_l2_v = round(l2[0] * SCALE_GRID_V, 2)
            grid_l2_a = round(l2[1] * SCALE_GRID_A, 2)
            grid_l2_hz = round(l2[2] * SCALE_GRID_HZ, 2)

            grid_l3_v = round(l3[0] * SCALE_GRID_V, 2)
            grid_l3_a = round(l3[1] * SCALE_GRID_A, 2)
            grid_l3_hz = round(l3[2] * SCALE_GRID_HZ, 2)

            # --- GRID POWER (3x int32 in 6 regs) ---
            gp = await self.client.read_holding_registers(self.unit_id, REG_GRID_POWER_L123_W_INT32, 6)
            grid_l1_w = GRID_POWER_SIGN * regs_to_s32_be(gp[0:2])
            grid_l2_w = GRID_POWER_SIGN * regs_to_s32_be(gp[2:4])
            grid_l3_w = GRID_POWER_SIGN * regs_to_s32_be(gp[4:6])
            grid_power_total_w = grid_l1_w + grid_l2_w + grid_l3_w

            return {
                # power
                "pv_power_w": pv_power_w,
                "battery_power_w": battery_power_w,
                "battery_charge_w": battery_charge_w,
                "battery_discharge_w": battery_discharge_w,

                # soc/soh
                "battery_soc_pct": battery_soc_pct,
                "battery_soh_pct": battery_soh_pct,

                # temps
                "inverter_temp_c": inverter_temp_c,
                "battery_temp_c": battery_temp_c,

                # grid V/A/Hz
                "grid_l1_v": grid_l1_v,
                "grid_l1_a": grid_l1_a,
                "grid_l1_hz": grid_l1_hz,
                "grid_l2_v": grid_l2_v,
                "grid_l2_a": grid_l2_a,
                "grid_l2_hz": grid_l2_hz,
                "grid_l3_v": grid_l3_v,
                "grid_l3_a": grid_l3_a,
                "grid_l3_hz": grid_l3_hz,

                # grid power
                "grid_l1_w": grid_l1_w,
                "grid_l2_w": grid_l2_w,
                "grid_l3_w": grid_l3_w,
                "grid_power_total_w": grid_power_total_w,
            }

        except Exception as err:
            raise UpdateFailed(str(err)) from err