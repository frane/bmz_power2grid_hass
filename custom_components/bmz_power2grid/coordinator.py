from __future__ import annotations

import logging
import time
from dataclasses import dataclass
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


@dataclass
class EnergyAccumulators:
    """
    Persisted in the sensor entities (RestoreEntity), but computed here.
    Values are in kWh and monotonically increasing.
    """
    pv_kwh: float = 0.0
    battery_charge_kwh: float = 0.0
    battery_discharge_kwh: float = 0.0
    grid_import_kwh: float = 0.0
    grid_export_kwh: float = 0.0


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

        # Energy accumulation state
        self._last_ts: float | None = None
        self._energy = EnergyAccumulators()

        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=int(scan_interval)),
        )

    def set_energy_state(
        self,
        pv_kwh: float | None = None,
        battery_charge_kwh: float | None = None,
        battery_discharge_kwh: float | None = None,
        grid_import_kwh: float | None = None,
        grid_export_kwh: float | None = None,
    ) -> None:
        """Called by RestoreEntity sensors after restore."""
        if pv_kwh is not None:
            self._energy.pv_kwh = float(pv_kwh)
        if battery_charge_kwh is not None:
            self._energy.battery_charge_kwh = float(battery_charge_kwh)
        if battery_discharge_kwh is not None:
            self._energy.battery_discharge_kwh = float(battery_discharge_kwh)
        if grid_import_kwh is not None:
            self._energy.grid_import_kwh = float(grid_import_kwh)
        if grid_export_kwh is not None:
            self._energy.grid_export_kwh = float(grid_export_kwh)

    def _integrate_energy(
        self,
        pv_w: float | None,
        batt_w: float | None,
        grid_w: float | None,
        now: float,
    ) -> None:
        """
        Integrate power -> energy:
        - PV energy: only positive generation (>=0)
        - Battery:
            battery_power_w is signed:
              * negative = charging
              * positive = discharging
            We create two monotonic counters: charge_kWh and discharge_kWh.
        - Grid:
            grid_power_total_w is signed:
              * positive = importing from grid
              * negative = exporting to grid
            We create two monotonic counters: import_kWh and export_kWh.
        """
        if self._last_ts is None:
            self._last_ts = now
            return

        dt_s = max(0.0, now - self._last_ts)
        self._last_ts = now
        if dt_s <= 0:
            return

        # PV
        if pv_w is not None:
            pv_pos_w = max(0.0, float(pv_w))
            self._energy.pv_kwh += (pv_pos_w * dt_s) / 3_600_000.0  # W*s -> kWh

        # Battery
        if batt_w is not None:
            bw = float(batt_w)
            if bw < 0:  # charging
                self._energy.battery_charge_kwh += ((-bw) * dt_s) / 3_600_000.0
            elif bw > 0:  # discharging
                self._energy.battery_discharge_kwh += (bw * dt_s) / 3_600_000.0

        # Grid
        if grid_w is not None:
            gw = float(grid_w)
            if gw > 0:  # importing from grid
                self._energy.grid_import_kwh += (gw * dt_s) / 3_600_000.0
            elif gw < 0:  # exporting to grid
                self._energy.grid_export_kwh += ((-gw) * dt_s) / 3_600_000.0

    async def _async_update_data(self) -> dict:
        try:
            # --- POWER ---
            pv_regs = await self.client.read_holding_registers(self.unit_id, REG_PV_POWER_W_INT32, 2)
            pv_power_w = regs_to_s32_be(pv_regs)

            batt_regs = await self.client.read_holding_registers(self.unit_id, REG_BATTERY_POWER_W_INT32, 2)
            battery_power_w = regs_to_s32_be(batt_regs)  # negative=charging

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

            # --- GRID IMPORT/EXPORT ---
            # Positive grid power = importing, negative = exporting
            grid_import_w = max(0, grid_power_total_w)
            grid_export_w = max(0, -grid_power_total_w)

            # --- ENERGY ACCUMULATION ---
            now = time.monotonic()
            self._integrate_energy(pv_power_w, battery_power_w, grid_power_total_w, now)

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
                "grid_import_w": grid_import_w,
                "grid_export_w": grid_export_w,

                # energy (monotonic, kWh)
                "pv_energy_kwh": round(self._energy.pv_kwh, 3),
                "battery_charge_energy_kwh": round(self._energy.battery_charge_kwh, 3),
                "battery_discharge_energy_kwh": round(self._energy.battery_discharge_kwh, 3),
                "grid_import_energy_kwh": round(self._energy.grid_import_kwh, 3),
                "grid_export_energy_kwh": round(self._energy.grid_export_kwh, 3),
            }

        except Exception as err:
            raise UpdateFailed(str(err)) from err
