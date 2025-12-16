from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .coordinator import BmzCoordinator


@dataclass(frozen=True)
class BmzSensorDef:
    key: str
    name: str
    unit: str | None
    device_class: SensorDeviceClass | None
    state_class: SensorStateClass | None
    icon: str | None = None


SENSORS: tuple[BmzSensorDef, ...] = (
    # === POWER (instantaneous) - from Solinteg docs ===
    BmzSensorDef("pv_power_w", "Total PV Input Power", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    BmzSensorDef("battery_power_w", "Battery P", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    BmzSensorDef("battery_charge_w", "Battery Charge Power", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    BmzSensorDef("battery_discharge_w", "Battery Discharge Power", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_power_total_w", "Pmeter Total", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l1_w", "Pmeter Phase A", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l2_w", "Pmeter Phase B", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l3_w", "Pmeter Phase C", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_import_w", "Grid Import Power", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_export_w", "Grid Export Power", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),

    # === BATTERY STATE - from Solinteg docs ===
    BmzSensorDef("battery_soc_pct", "SOC", "%", SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT),
    BmzSensorDef("battery_soh_pct", "SOH", "%", None, SensorStateClass.MEASUREMENT),
    BmzSensorDef("battery_voltage", "Battery V", "V", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    BmzSensorDef("battery_current", "Battery I", "A", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),

    # === GRID V/A/Hz - from Solinteg docs ===
    BmzSensorDef("grid_l1_v", "Phase A Voltage", "V", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l1_a", "Phase A Current", "A", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l2_v", "Phase B Voltage", "V", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l2_a", "Phase B Current", "A", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l3_v", "Phase C Voltage", "V", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l3_a", "Phase C Current", "A", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_frequency", "Grid Frequency", "Hz", SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT),

    # === TEMPERATURES - from Solinteg docs ===
    BmzSensorDef("inverter_temp_c", "Inverter Temp", "°C", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
    BmzSensorDef("battery_temp_c", "BMS Pack Temperature", "°C", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),

    # === ENERGY TOTALS - from Solinteg docs ===
    BmzSensorDef("total_pv_energy_kwh", "Total PV Generation", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    BmzSensorDef("total_battery_charge_kwh", "Total Battery Charging Energy", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    BmzSensorDef("total_battery_discharge_kwh", "Total Battery Discharging Energy", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    BmzSensorDef("total_grid_import_kwh", "Total Purchased Energy from Grid", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    BmzSensorDef("total_grid_export_kwh", "Total Energy Injected into Grid", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    BmzSensorDef("total_load_kwh", "Total Load Consumption", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),

    # === DAILY ENERGY - from Solinteg docs ===
    BmzSensorDef("daily_pv_energy_kwh", "Daily PV Generation", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    BmzSensorDef("daily_battery_charge_kwh", "Daily Battery Charging Energy", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    BmzSensorDef("daily_battery_discharge_kwh", "Daily Battery Discharging Energy", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    BmzSensorDef("daily_grid_import_kwh", "Daily Purchased Energy", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    BmzSensorDef("daily_grid_export_kwh", "Daily Energy Injected to Grid", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    BmzSensorDef("daily_load_kwh", "Daily Load Consumption", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: BmzCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BmzSensor(coordinator, entry, s) for s in SENSORS])


class BmzSensor(CoordinatorEntity[BmzCoordinator], SensorEntity):
    def __init__(self, coordinator: BmzCoordinator, entry, definition: BmzSensorDef) -> None:
        super().__init__(coordinator)
        self._def = definition

        self._attr_name = definition.name
        self._attr_unique_id = f"{entry.entry_id}_{definition.key}"
        self._attr_native_unit_of_measurement = definition.unit
        self._attr_device_class = definition.device_class
        self._attr_state_class = definition.state_class
        self._attr_icon = definition.icon

        # Energy Dashboard wants higher precision for energy sensors
        if definition.device_class == SensorDeviceClass.ENERGY:
            self._attr_suggested_display_precision = 1

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="BMZ Power2Grid Inverter",
            manufacturer="BMZ / Solinteg",
            model="Power2Grid / Hyperion",
        )

    @property
    def native_value(self) -> Any:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._def.key)
