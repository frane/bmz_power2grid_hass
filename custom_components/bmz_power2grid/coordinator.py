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
    # Register addresses
    REG_PV_POWER_KW_U32,
    REG_BATTERY_POWER_KW_I32,
    REG_BATTERY_VOLTAGE_U16,
    REG_BATTERY_CURRENT_I16,
    REG_BATTERY_SOC_U16,
    REG_BATTERY_SOH_U16,
    REG_GRID_METER_L1_KW_I32,
    REG_GRID_METER_TOTAL_KW_I32,
    REG_GRID_L1_VOLTAGE_U16,
    REG_GRID_FREQUENCY_U16,
    REG_INVERTER_TEMP_I16,
    REG_BATTERY_TEMP_U16,
    # Native energy counters
    REG_TOTAL_GRID_EXPORT_U32,
    REG_TOTAL_GRID_IMPORT_U32,
    REG_TOTAL_BATTERY_CHARGE_U32,
    REG_TOTAL_BATTERY_DISCHARGE_U32,
    REG_TOTAL_PV_GENERATION_U32,
    REG_TOTAL_LOAD_U32,
    REG_DAILY_GRID_EXPORT_U16,
    REG_DAILY_GRID_IMPORT_U16,
    REG_DAILY_BATTERY_CHARGE_U16,
    REG_DAILY_BATTERY_DISCHARGE_U16,
    REG_DAILY_PV_GENERATION_U16,
    REG_DAILY_LOAD_U16,
    # Scaling
    SCALE_VOLTAGE,
    SCALE_CURRENT,
    SCALE_FREQUENCY,
    SCALE_TEMPERATURE,
    SCALE_PERCENT,
    SCALE_ENERGY_10,
)

from .modbus_client import RtuOverTcpClient, regs_to_s32_be, regs_to_u32_be, regs_to_s16

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
            # === PV POWER ===
            # Register 11028: Total PV Input Power (U32, kW, /1000)
            pv_regs = await self.client.read_holding_registers(self.unit_id, REG_PV_POWER_KW_U32, 2)
            pv_power_w = regs_to_u32_be(pv_regs)  # Already in W (kW * 1000 = W, but /1000 means raw is in W)

            # === BATTERY POWER ===
            # Register 30258: Battery_P (I32, kW, /1000) - positive=discharge, negative=charge
            batt_regs = await self.client.read_holding_registers(self.unit_id, REG_BATTERY_POWER_KW_I32, 2)
            battery_power_w = regs_to_s32_be(batt_regs)  # Already in W

            battery_charge_w = max(0, -battery_power_w)
            battery_discharge_w = max(0, battery_power_w)

            # === BATTERY VOLTAGE/CURRENT ===
            # Registers 30254-30255: Battery V/I
            batt_vi = await self.client.read_holding_registers(self.unit_id, REG_BATTERY_VOLTAGE_U16, 2)
            battery_voltage = round(batt_vi[0] * SCALE_VOLTAGE, 1)
            battery_current = round(regs_to_s16(batt_vi[1]) * SCALE_CURRENT, 1)

            # === BATTERY SOC/SOH ===
            # Registers 33000-33001: SOC/SOH (U16, %, /100)
            soc_soh = await self.client.read_holding_registers(self.unit_id, REG_BATTERY_SOC_U16, 2)
            battery_soc_pct = round(soc_soh[0] * SCALE_PERCENT, 2)
            battery_soh_pct = round(soc_soh[1] * SCALE_PERCENT, 2)

            # === GRID METER POWER ===
            # Registers 10994-11001: Per-phase and total grid meter power (I32, kW, /1000)
            # positive = exporting to grid, negative = importing from grid
            grid_regs = await self.client.read_holding_registers(self.unit_id, REG_GRID_METER_L1_KW_I32, 8)
            grid_l1_w = regs_to_s32_be(grid_regs[0:2])
            grid_l2_w = regs_to_s32_be(grid_regs[2:4])
            grid_l3_w = regs_to_s32_be(grid_regs[4:6])
            grid_power_total_w = regs_to_s32_be(grid_regs[6:8])

            # Grid import/export (positive values)
            grid_import_w = max(0, -grid_power_total_w)  # negative meter = importing
            grid_export_w = max(0, grid_power_total_w)   # positive meter = exporting

            # === GRID VOLTAGE/CURRENT/FREQUENCY ===
            # Registers 11009-11015: V/A per phase + frequency
            grid_vaf = await self.client.read_holding_registers(self.unit_id, REG_GRID_L1_VOLTAGE_U16, 7)
            grid_l1_v = round(grid_vaf[0] * SCALE_VOLTAGE, 1)
            grid_l1_a = round(grid_vaf[1] * SCALE_CURRENT, 2)
            grid_l2_v = round(grid_vaf[2] * SCALE_VOLTAGE, 1)
            grid_l2_a = round(grid_vaf[3] * SCALE_CURRENT, 2)
            grid_l3_v = round(grid_vaf[4] * SCALE_VOLTAGE, 1)
            grid_l3_a = round(grid_vaf[5] * SCALE_CURRENT, 2)
            grid_frequency = round(grid_vaf[6] * SCALE_FREQUENCY, 2)

            # === TEMPERATURES ===
            # Register 11032: Inverter temp (I16, °C, /10)
            inv_temp_raw = (await self.client.read_holding_registers(self.unit_id, REG_INVERTER_TEMP_I16, 1))[0]
            inverter_temp_c = round(regs_to_s16(inv_temp_raw) * SCALE_TEMPERATURE, 1)

            # Register 33003: Battery temp (U16, °C, /10)
            bat_temp_raw = (await self.client.read_holding_registers(self.unit_id, REG_BATTERY_TEMP_U16, 1))[0]
            battery_temp_c = round(bat_temp_raw * SCALE_TEMPERATURE, 1)

            # === NATIVE ENERGY COUNTERS (TOTAL) ===
            # These are from the device itself - much more accurate than calculating!
            # Registers 31102-31115: Total energy counters (U32, kWh, /10)
            energy_totals = await self.client.read_holding_registers(self.unit_id, REG_TOTAL_GRID_EXPORT_U32, 14)
            total_grid_export_kwh = round(regs_to_u32_be(energy_totals[0:2]) * SCALE_ENERGY_10, 1)
            total_grid_import_kwh = round(regs_to_u32_be(energy_totals[2:4]) * SCALE_ENERGY_10, 1)
            # Skip 31106-31107 (backup port energy)
            total_battery_charge_kwh = round(regs_to_u32_be(energy_totals[6:8]) * SCALE_ENERGY_10, 1)
            total_battery_discharge_kwh = round(regs_to_u32_be(energy_totals[8:10]) * SCALE_ENERGY_10, 1)
            total_pv_kwh = round(regs_to_u32_be(energy_totals[10:12]) * SCALE_ENERGY_10, 1)
            total_load_kwh = round(regs_to_u32_be(energy_totals[12:14]) * SCALE_ENERGY_10, 1)

            # === NATIVE ENERGY COUNTERS (DAILY) ===
            # Registers 31000-31006: Daily energy counters (U16, kWh, /10)
            daily_energy = await self.client.read_holding_registers(self.unit_id, REG_DAILY_GRID_EXPORT_U16, 7)
            daily_grid_export_kwh = round(daily_energy[0] * SCALE_ENERGY_10, 1)
            daily_grid_import_kwh = round(daily_energy[1] * SCALE_ENERGY_10, 1)
            # Skip 31002 (backup port)
            daily_battery_charge_kwh = round(daily_energy[3] * SCALE_ENERGY_10, 1)
            daily_battery_discharge_kwh = round(daily_energy[4] * SCALE_ENERGY_10, 1)
            daily_pv_kwh = round(daily_energy[5] * SCALE_ENERGY_10, 1)
            daily_load_kwh = round(daily_energy[6] * SCALE_ENERGY_10, 1)

            return {
                # Power (instantaneous, in W)
                "pv_power_w": pv_power_w,
                "battery_power_w": battery_power_w,
                "battery_charge_w": battery_charge_w,
                "battery_discharge_w": battery_discharge_w,
                "grid_power_total_w": grid_power_total_w,
                "grid_l1_w": grid_l1_w,
                "grid_l2_w": grid_l2_w,
                "grid_l3_w": grid_l3_w,
                "grid_import_w": grid_import_w,
                "grid_export_w": grid_export_w,

                # Battery state
                "battery_soc_pct": battery_soc_pct,
                "battery_soh_pct": battery_soh_pct,
                "battery_voltage": battery_voltage,
                "battery_current": battery_current,

                # Grid V/A/Hz
                "grid_l1_v": grid_l1_v,
                "grid_l1_a": grid_l1_a,
                "grid_l2_v": grid_l2_v,
                "grid_l2_a": grid_l2_a,
                "grid_l3_v": grid_l3_v,
                "grid_l3_a": grid_l3_a,
                "grid_frequency": grid_frequency,

                # Temperatures
                "inverter_temp_c": inverter_temp_c,
                "battery_temp_c": battery_temp_c,

                # Energy totals (from device, kWh) - for Energy Dashboard
                "total_pv_energy_kwh": total_pv_kwh,
                "total_battery_charge_kwh": total_battery_charge_kwh,
                "total_battery_discharge_kwh": total_battery_discharge_kwh,
                "total_grid_import_kwh": total_grid_import_kwh,
                "total_grid_export_kwh": total_grid_export_kwh,
                "total_load_kwh": total_load_kwh,

                # Daily energy (from device, kWh)
                "daily_pv_energy_kwh": daily_pv_kwh,
                "daily_battery_charge_kwh": daily_battery_charge_kwh,
                "daily_battery_discharge_kwh": daily_battery_discharge_kwh,
                "daily_grid_import_kwh": daily_grid_import_kwh,
                "daily_grid_export_kwh": daily_grid_export_kwh,
                "daily_load_kwh": daily_load_kwh,
            }

        except Exception as err:
            raise UpdateFailed(str(err)) from err
