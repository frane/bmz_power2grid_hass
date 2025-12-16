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
    # === POWER (instantaneous) ===
    # Spec: "Total PV Input Power" (reg 11028)
    BmzSensorDef("pv_power_w", "Solar Power", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    # Spec: "Battery_P" (reg 30258) - positive=discharge, negative=charge
    BmzSensorDef("battery_power_w", "Battery Power", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    BmzSensorDef("battery_charge_w", "Battery Charging", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    BmzSensorDef("battery_discharge_w", "Battery Discharging", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    # Spec: "Pmeter" (reg 10994-11001) - positive=export, negative=import
    BmzSensorDef("grid_power_total_w", "Grid Power", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l1_w", "Grid Power L1", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l2_w", "Grid Power L2", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l3_w", "Grid Power L3", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_import_w", "Grid Import", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_export_w", "Grid Export", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),

    # === BATTERY STATE ===
    # Spec: "SOC" (reg 33000), "SOH" (reg 33001)
    BmzSensorDef("battery_soc_pct", "Battery Level", "%", SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT),
    BmzSensorDef("battery_soh_pct", "Battery Health", "%", None, SensorStateClass.MEASUREMENT),
    # Spec: "Battery_V" (reg 30254), "Battery_I" (reg 30255)
    BmzSensorDef("battery_voltage", "Battery Voltage", "V", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    BmzSensorDef("battery_current", "Battery Current", "A", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),

    # === GRID V/A/Hz ===
    # Spec: registers 11009-11015
    BmzSensorDef("grid_l1_v", "Grid Voltage L1", "V", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l1_a", "Grid Current L1", "A", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l2_v", "Grid Voltage L2", "V", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l2_a", "Grid Current L2", "A", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l3_v", "Grid Voltage L3", "V", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l3_a", "Grid Current L3", "A", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_frequency", "Grid Frequency", "Hz", SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT),

    # === TEMPERATURES ===
    # Spec: "Inverter inner temp" (reg 11032), "Pack temperature" (reg 33003)
    BmzSensorDef("inverter_temp_c", "Inverter Temperature", "°C", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
    BmzSensorDef("battery_temp_c", "Battery Temperature", "°C", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),

    # === ENERGY TOTALS (lifetime) ===
    # Spec: registers 31102-31115
    BmzSensorDef("total_pv_energy_kwh", "Total Solar Energy", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    BmzSensorDef("total_battery_charge_kwh", "Total Battery Charged", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    BmzSensorDef("total_battery_discharge_kwh", "Total Battery Discharged", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    BmzSensorDef("total_grid_import_kwh", "Total Grid Import", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    BmzSensorDef("total_grid_export_kwh", "Total Grid Export", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    BmzSensorDef("total_load_kwh", "Total Consumption", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),

    # === DAILY ENERGY (resets at midnight) ===
    # Spec: registers 31000-31006
    BmzSensorDef("daily_pv_energy_kwh", "Today Solar Energy", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    BmzSensorDef("daily_battery_charge_kwh", "Today Battery Charged", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    BmzSensorDef("daily_battery_discharge_kwh", "Today Battery Discharged", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    BmzSensorDef("daily_grid_import_kwh", "Today Grid Import", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    BmzSensorDef("daily_grid_export_kwh", "Today Grid Export", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    BmzSensorDef("daily_load_kwh", "Today Consumption", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
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
