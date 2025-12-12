from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
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


# -----------------------------------------------------------------------------
# NOTE:
# - Power (W) sensors use state_class=measurement.
# - Energy (kWh) sensors MUST be total_increasing for HA Energy Dashboard.
# - coordinator.data MUST provide these keys. If a key is missing, entity shows None.
# -----------------------------------------------------------------------------

SENSORS: tuple[BmzSensorDef, ...] = (
    # -------------------------
    # Instant power (W)
    # -------------------------
    BmzSensorDef(
        "pv_power_w",
        "PV Power",
        "W",
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
    ),
    BmzSensorDef(
        "battery_power_w",
        "Battery Power",
        "W",
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
    ),
    BmzSensorDef(
        "battery_charge_w",
        "Battery Charge Power",
        "W",
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
    ),
    BmzSensorDef(
        "battery_discharge_w",
        "Battery Discharge Power",
        "W",
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
    ),
    BmzSensorDef(
        "grid_power_w",
        "Grid Power",
        "W",
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
    ),
    BmzSensorDef(
        "grid_import_w",
        "Grid Import Power",
        "W",
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
    ),
    BmzSensorDef(
        "grid_export_w",
        "Grid Export Power",
        "W",
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
    ),

    # -------------------------
    # Energy dashboard (kWh) - MUST be total_increasing
    # These are the ones you select in Energy Dashboard.
    # -------------------------
    BmzSensorDef(
        "pv_energy_kwh",
        "PV Energy",
        "kWh",
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
    ),
    BmzSensorDef(
        "grid_import_energy_kwh",
        "Grid Import Energy",
        "kWh",
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
    ),
    BmzSensorDef(
        "grid_export_energy_kwh",
        "Grid Export Energy",
        "kWh",
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
    ),
    BmzSensorDef(
        "battery_charge_energy_kwh",
        "Battery Charge Energy",
        "kWh",
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
    ),
    BmzSensorDef(
        "battery_discharge_energy_kwh",
        "Battery Discharge Energy",
        "kWh",
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
    ),

    # -------------------------
    # Battery metrics
    # -------------------------
    BmzSensorDef(
        "battery_soc_pct",
        "Battery State of Charge",
        "%",
        SensorDeviceClass.BATTERY,
        SensorStateClass.MEASUREMENT,
    ),
    BmzSensorDef(
        "battery_soh_pct",
        "Battery State of Health",
        "%",
        None,
        SensorStateClass.MEASUREMENT,
    ),

    # -------------------------
    # Temperatures
    # -------------------------
    BmzSensorDef(
        "inverter_temp_c",
        "Inverter Temperature",
        "°C",
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    BmzSensorDef(
        "battery_temp_c",
        "Battery Temperature",
        "°C",
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),

    # -------------------------
    # Grid electrical parameters (L1/L2/L3)
    # -------------------------
    BmzSensorDef(
        "grid_l1_v",
        "Grid L1 Voltage",
        "V",
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
    ),
    BmzSensorDef(
        "grid_l1_a",
        "Grid L1 Current",
        "A",
        SensorDeviceClass.CURRENT,
        SensorStateClass.MEASUREMENT,
    ),
    BmzSensorDef(
        "grid_l1_hz",
        "Grid Frequency (L1)",
        "Hz",
        SensorDeviceClass.FREQUENCY,
        SensorStateClass.MEASUREMENT,
    ),

    BmzSensorDef(
        "grid_l2_v",
        "Grid L2 Voltage",
        "V",
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
    ),
    BmzSensorDef(
        "grid_l2_a",
        "Grid L2 Current",
        "A",
        SensorDeviceClass.CURRENT,
        SensorStateClass.MEASUREMENT,
    ),
    BmzSensorDef(
        "grid_l2_hz",
        "Grid Frequency (L2)",
        "Hz",
        SensorDeviceClass.FREQUENCY,
        SensorStateClass.MEASUREMENT,
    ),

    # L3 (added)
    BmzSensorDef(
        "grid_l3_v",
        "Grid L3 Voltage",
        "V",
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
    ),
    BmzSensorDef(
        "grid_l3_a",
        "Grid L3 Current",
        "A",
        SensorDeviceClass.CURRENT,
        SensorStateClass.MEASUREMENT,
    ),
    BmzSensorDef(
        "grid_l3_hz",
        "Grid Frequency (L3)",
        "Hz",
        SensorDeviceClass.FREQUENCY,
        SensorStateClass.MEASUREMENT,
    ),
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

        # If you already expose manufacturer/model/firmware in coordinator.data,
        # you can wire it here later via device_info "sw_version"/"hw_version".
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="BMZ Power2Grid Inverter",
            manufacturer="BMZ",
            model="Power2Grid / Hyperion",
        )

    @property
    def native_value(self) -> Any:
        # coordinator.data should contain numeric values (float/int) for each key.
        # Return None when missing => HA shows Unavailable/Unknown.
        return self.coordinator.data.get(self._def.key)