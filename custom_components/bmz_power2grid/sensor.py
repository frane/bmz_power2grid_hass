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

SENSORS: tuple[BmzSensorDef, ...] = (
    BmzSensorDef("pv_power_w", "PV Power", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    BmzSensorDef("battery_power_w", "Battery Power", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    BmzSensorDef("battery_charge_w", "Battery Charge Power", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    BmzSensorDef("battery_discharge_w", "Battery Discharge Power", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),

    BmzSensorDef("battery_soc_pct", "Battery State of Charge", "%", SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT),
    BmzSensorDef("battery_soh_pct", "Battery State of Health", "%", None, SensorStateClass.MEASUREMENT),

    BmzSensorDef("inverter_temp_c", "Inverter Temperature", "°C", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
    BmzSensorDef("battery_temp_c", "Battery Temperature", "°C", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),

    BmzSensorDef("grid_l1_v", "Grid L1 Voltage", "V", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l1_a", "Grid L1 Current", "A", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l1_hz", "Grid Frequency (L1)", "Hz", SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT),

    BmzSensorDef("grid_l2_v", "Grid L2 Voltage", "V", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l2_a", "Grid L2 Current", "A", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l2_hz", "Grid Frequency (L2)", "Hz", SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT),
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

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="BMZ Power2Grid Inverter",
            manufacturer="BMZ",
            model="Power2Grid / Hyperion",
        )

    @property
    def native_value(self) -> Any:
        return self.coordinator.data.get(self._def.key)