from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .modbus_client import RtuOverTcpClient, regs_to_s32_be
from .const import DOMAIN

LOGGER = logging.getLogger(__name__)


@dataclass
class EnergyAccumulators:
    """
    Persisted in the sensor entities (RestoreEntity), but computed here.
    Values are in kWh and monotonically increasing.
    """
    pv_kwh: float = 0.0
    battery_charge_kwh: float = 0.0
    battery_discharge_kwh: float = 0.0


class BmzCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, host: str, port: int, unit: int, scan_interval_s: int = 5) -> None:
        self.hass = hass
        self.host = host
        self.port = port
        self.unit = unit
        self.client = RtuOverTcpClient(host=host, port=port, timeout=3.0)

        self._last_ts: float | None = None
        self._energy = EnergyAccumulators()

        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=f"{DOMAIN} ({host})",
            update_interval=None,  # we schedule via async_add_job in __init__.py or set below
        )

        # HA wants timedelta normally; we can keep it simple:
        from datetime import timedelta
        self.update_interval = timedelta(seconds=scan_interval_s)

    def set_energy_state(self, pv_kwh: float | None, chg_kwh: float | None, dis_kwh: float | None) -> None:
        """Called by RestoreEntity sensors after restore."""
        if pv_kwh is not None:
            self._energy.pv_kwh = float(pv_kwh)
        if chg_kwh is not None:
            self._energy.battery_charge_kwh = float(chg_kwh)
        if dis_kwh is not None:
            self._energy.battery_discharge_kwh = float(dis_kwh)

    def _integrate_energy(self, pv_w: float | None, batt_w: float | None, now: float) -> None:
        """
        Integrate power -> energy:
        - PV energy: only positive generation (>=0)
        - Battery:
            battery_power_w is signed:
              * negative = charging (you observed this)
              * positive = discharging
            We create two monotonic counters: charge_kWh and discharge_kWh.
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
            self._energy.pv_kwh += (pv_pos_w * dt_s) / 3600_000.0  # W*s -> kWh

        # Battery
        if batt_w is not None:
            bw = float(batt_w)
            if bw < 0:  # charging (your device)
                self._energy.battery_charge_kwh += ((-bw) * dt_s) / 3600_000.0
            elif bw > 0:  # discharging
                self._energy.battery_discharge_kwh += (bw * dt_s) / 3600_000.0

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            # ---- Core reads we actually know from your reverse engineering ----

            # PV total power (W): 0x2B14/2 int32 BE
            pv_regs = await self.client.read_holding_registers(self.unit, 0x2B14, 2)
            pv_power_w = regs_to_s32_be(pv_regs)

            # Battery power (W): 0x2AF8/2 int32 BE (negative while charging)
            batt_regs = await self.client.read_holding_registers(self.unit, 0x2AF8, 2)
            battery_power_w = regs_to_s32_be(batt_regs)

            # SOC: 0x80E8 u16, scale /100 => percent (e.g., 1900 => 19.00%)
            soc_regs = await self.client.read_holding_registers(self.unit, 0x80E8, 1)
            battery_soc_pct = soc_regs[0] / 100.0

            # SOH: 0x80E9 u16, scale /100 => percent (9900 => 99.00%)
            soh_regs = await self.client.read_holding_registers(self.unit, 0x80E9, 1)
            battery_soh_pct = soh_regs[0] / 100.0

            # Battery temp: 0x80EB u16 /10 => °C (280 => 28.0)
            batt_temp_regs = await self.client.read_holding_registers(self.unit, 0x80EB, 1)
            battery_temp_c = batt_temp_regs[0] / 10.0

            # Inverter temp: 0x2B18 u16 /10 => °C (398 => 39.8)
            inv_temp_regs = await self.client.read_holding_registers(self.unit, 0x2B18, 1)
            inverter_temp_c = inv_temp_regs[0] / 10.0

            # Grid phase blocks:
            # L1: 0x75F8/3 => [V*10, A*100, Hz*100]
            # L2: 0x7602/3 => [V*10, A*100, Hz*100]
            # L3: 0x760C/3 => [V*10, A*100, Hz*100]  (logical + observed in your dumps)
            l1 = await self.client.read_holding_registers(self.unit, 0x75F8, 3)
            l2 = await self.client.read_holding_registers(self.unit, 0x7602, 3)
            l3 = await self.client.read_holding_registers(self.unit, 0x760C, 3)

            grid_l1_v = l1[0] / 10.0
            grid_l1_a = l1[1] / 100.0
            grid_l1_hz = l1[2] / 100.0

            grid_l2_v = l2[0] / 10.0
            grid_l2_a = l2[1] / 100.0
            grid_l2_hz = l2[2] / 100.0

            grid_l3_v = l3[0] / 10.0
            grid_l3_a = l3[1] / 100.0
            grid_l3_hz = l3[2] / 100.0

            # Derived battery charge/discharge power (W)
            battery_charge_w = max(0.0, -float(battery_power_w))
            battery_discharge_w = max(0.0, float(battery_power_w))

            # Update kWh accumulators (for Energy Dashboard)
            now = time.time()
            self._integrate_energy(pv_w=float(pv_power_w), batt_w=float(battery_power_w), now=now)

            # Data dict consumed by sensors
            return {
                # Power
                "pv_power_w": float(pv_power_w),
                "battery_power_w": float(battery_power_w),
                "battery_charge_w": float(battery_charge_w),
                "battery_discharge_w": float(battery_discharge_w),

                # Battery health
                "battery_soc_pct": float(battery_soc_pct),
                "battery_soh_pct": float(battery_soh_pct),

                # Temps
                "inverter_temp_c": float(inverter_temp_c),
                "battery_temp_c": float(battery_temp_c),

                # Grid L1/L2/L3
                "grid_l1_v": float(grid_l1_v),
                "grid_l1_a": float(grid_l1_a),
                "grid_l1_hz": float(grid_l1_hz),
                "grid_l2_v": float(grid_l2_v),
                "grid_l2_a": float(grid_l2_a),
                "grid_l2_hz": float(grid_l2_hz),
                "grid_l3_v": float(grid_l3_v),
                "grid_l3_a": float(grid_l3_a),
                "grid_l3_hz": float(grid_l3_hz),

                # Energy (kWh) - plugin-provided (TOTAL_INCREASING)
                "pv_energy_kwh": float(self._energy.pv_kwh),
                "battery_charge_energy_kwh": float(self._energy.battery_charge_kwh),
                "battery_discharge_energy_kwh": float(self._energy.battery_discharge_kwh),
            }

        except Exception as err:
            raise UpdateFailed(str(err)) from err