from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.restore_state import RestoreEntity
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
    # --- Power ---
    BmzSensorDef("pv_power_w", "PV Power", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    BmzSensorDef("battery_power_w", "Battery Power", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    BmzSensorDef("battery_charge_w", "Battery Charge Power", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    BmzSensorDef("battery_discharge_w", "Battery Discharge Power", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),

    # --- Battery ---
    BmzSensorDef("battery_soc_pct", "Battery State of Charge", "%", SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT),
    BmzSensorDef("battery_soh_pct", "Battery State of Health", "%", None, SensorStateClass.MEASUREMENT),

    # --- Temperatures ---
    BmzSensorDef("inverter_temp_c", "Inverter Temperature", "°C", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
    BmzSensorDef("battery_temp_c", "Battery Temperature", "°C", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),

    # --- Grid ---
    BmzSensorDef("grid_l1_v", "Grid L1 Voltage", "V", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l1_a", "Grid L1 Current", "A", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l1_hz", "Grid Frequency (L1)", "Hz", SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT),

    BmzSensorDef("grid_l2_v", "Grid L2 Voltage", "V", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l2_a", "Grid L2 Current", "A", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l2_hz", "Grid Frequency (L2)", "Hz", SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT),

    BmzSensorDef("grid_l3_v", "Grid L3 Voltage", "V", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l3_a", "Grid L3 Current", "A", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),
    BmzSensorDef("grid_l3_hz", "Grid Frequency (L3)", "Hz", SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT),

    # --- Energy (Energy Dashboard compatible: kWh + total_increasing) ---
    BmzSensorDef("pv_energy_kwh", "PV Energy", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    BmzSensorDef("battery_charge_energy_kwh", "Battery Charge Energy", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    BmzSensorDef("battery_discharge_energy_kwh", "Battery Discharge Energy", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: BmzCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BmzSensor(coordinator, entry, s) for s in SENSORS])


class BmzSensor(CoordinatorEntity[BmzCoordinator], SensorEntity, RestoreEntity):
    def __init__(self, coordinator: BmzCoordinator, entry, definition: BmzSensorDef) -> None:
        super().__init__(coordinator)
        self._def = definition

        self._attr_name = definition.name
        self._attr_unique_id = f"{entry.entry_id}_{definition.key}"
        self._attr_native_unit_of_measurement = definition.unit
        self._attr_device_class = definition.device_class
        self._attr_state_class = definition.state_class
        self._attr_icon = definition.icon

        # Energy dashboard wants this on ENERGY sensors in newer HA versions
        if definition.device_class == SensorDeviceClass.ENERGY:
            self._attr_suggested_display_precision = 3

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="BMZ Power2Grid Inverter",
            manufacturer="BMZ",
            model="Power2Grid / Hyperion",
        )

    async def async_added_to_hass(self) -> None:
        # Restore monotonic counters so Energy Dashboard keeps history after restart.
        await super().async_added_to_hass()

        if self._def.key in ("pv_energy_kwh", "battery_charge_energy_kwh", "battery_discharge_energy_kwh"):
            last = await self.async_get_last_state()
            if last and last.state not in (None, "", "unknown", "unavailable"):
                try:
                    val = float(last.state)
                except ValueError:
                    val = None
            else:
                val = None

            # Push restored values into coordinator accumulator once (best-effort).
            # We do this from each energy sensor; coordinator will keep the last set values.
            if self._def.key == "pv_energy_kwh":
                self.coordinator.set_energy_state(pv_kwh=val, chg_kwh=None, dis_kwh=None)
            elif self._def.key == "battery_charge_energy_kwh":
                self.coordinator.set_energy_state(pv_kwh=None, chg_kwh=val, dis_kwh=None)
            elif self._def.key == "battery_discharge_energy_kwh":
                self.coordinator.set_energy_state(pv_kwh=None, chg_kwh=None, dis_kwh=val)

    @property
    def native_value(self) -> Any:
        # IMPORTANT: return None if key missing => HA shows 'Unavailable'.
        # In our coordinator we always provide all keys above; so 'Unknown' should stop.
        return self.coordinator.data.get(self._def.key)
