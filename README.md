# BMZ Power2Grid Home Assistant Integration

A native Home Assistant integration for **BMZ Power2Grid / Solinteg hybrid inverters** and **BMZ Hyperion battery systems**, using **Modbus RTU over TCP**.

Based on the **official Solinteg Modbus RTU Protocol v00.02** documentation.

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)

---

## Features

- Local, fast and reliable polling (no cloud, no vendor lock-in)
- Based on official Solinteg Modbus protocol documentation
- Native energy counters from device (no manual calculation)
- Full Home Assistant Energy Dashboard support
- No external dependencies (no `pymodbus`)

---

## Communication Details

| Setting | Default |
|---------|---------|
| Protocol | Modbus RTU over TCP |
| Port | `5743` |
| Unit ID | `252` |

---

## Available Sensors

### Power (Instantaneous)

| Sensor | Description | Unit |
|--------|-------------|------|
| Total PV Input Power | Solar panel power output | W |
| Battery P | Battery power (positive=discharge, negative=charge) | W |
| Battery Charge Power | Power flowing into battery | W |
| Battery Discharge Power | Power flowing from battery | W |
| Pmeter Total | Grid meter total (positive=export, negative=import) | W |
| Pmeter Phase A/B/C | Grid meter per phase | W |
| Grid Import Power | Power drawn from grid | W |
| Grid Export Power | Power fed to grid | W |

### Battery State

| Sensor | Description | Unit |
|--------|-------------|------|
| SOC | State of Charge | % |
| SOH | State of Health | % |
| Battery V | Battery voltage | V |
| Battery I | Battery current (positive=discharge, negative=charge) | A |

### Grid

| Sensor | Description | Unit |
|--------|-------------|------|
| Phase A/B/C Voltage | Grid voltage per phase | V |
| Phase A/B/C Current | Grid current per phase | A |
| Grid Frequency | Grid frequency | Hz |

### Temperatures

| Sensor | Description | Unit |
|--------|-------------|------|
| Inverter Temp | Inverter temperature | °C |
| BMS Pack Temperature | Battery pack temperature | °C |

### Energy Totals (Lifetime)

These are native counters from the device - they persist across restarts.

| Sensor | Description | Unit |
|--------|-------------|------|
| Total PV Generation | Lifetime solar energy produced | kWh |
| Total Battery Charging Energy | Lifetime energy charged into battery | kWh |
| Total Battery Discharging Energy | Lifetime energy discharged from battery | kWh |
| Total Purchased Energy from Grid | Lifetime energy imported from grid | kWh |
| Total Energy Injected into Grid | Lifetime energy exported to grid | kWh |
| Total Load Consumption | Lifetime energy consumed by loads | kWh |

### Daily Energy (Resets at Midnight)

| Sensor | Description | Unit |
|--------|-------------|------|
| Daily PV Generation | Today's solar energy | kWh |
| Daily Battery Charging Energy | Today's battery charge energy | kWh |
| Daily Battery Discharging Energy | Today's battery discharge energy | kWh |
| Daily Purchased Energy | Today's grid import energy | kWh |
| Daily Energy Injected to Grid | Today's grid export energy | kWh |
| Daily Load Consumption | Today's load consumption | kWh |

---

## Understanding the Values

### Sign Conventions

**Battery Power (Battery P):**
- **Positive** = Battery is discharging (providing power)
- **Negative** = Battery is charging (consuming power)

**Grid Meter Power (Pmeter):**
- **Positive** = Exporting to grid (selling power)
- **Negative** = Importing from grid (buying power)

### Example Scenarios

| Scenario | Battery P | Pmeter Total |
|----------|-----------|--------------|
| Sunny day, battery charging, exporting to grid | -2000 W | +3000 W |
| Night, battery discharging, no grid usage | +1500 W | 0 W |
| Night, battery empty, importing from grid | 0 W | -2000 W |
| Cloudy, battery discharging + importing | +1000 W | -500 W |

---

## Energy Dashboard Setup

All energy sensors use `state_class: total_increasing` and can be directly used in the Home Assistant Energy Dashboard:

| Dashboard Section | Sensor to Use |
|-------------------|---------------|
| Solar Production | Total PV Generation |
| Grid Consumption | Total Purchased Energy from Grid |
| Return to Grid | Total Energy Injected into Grid |
| Battery Storage (In) | Total Battery Charging Energy |
| Battery Storage (Out) | Total Battery Discharging Energy |

---

## Installation (via HACS)

1. Install **HACS** in Home Assistant
2. Go to **HACS > Integrations > Custom repositories**
3. Add this repository URL
4. Category: **Integration**
5. Install **BMZ Power2Grid**
6. Restart Home Assistant

---

## Configuration

1. Go to **Settings > Devices & Services**
2. Click **Add Integration**
3. Select **BMZ Power2Grid**
4. Enter:
   - Inverter IP address
   - Port (default: `5743`)
   - Unit ID (default: `252`)
   - Scan interval in seconds (default: `5`)

---

## Register Map

Based on official Solinteg Modbus RTU Protocol v00.02 (2022-12-06).

| Register | Description | Type | Scale |
|----------|-------------|------|-------|
| 11028 | Total PV Input Power | U32 | /1000 kW |
| 30258 | Battery P | I32 | /1000 kW |
| 30254 | Battery V | U16 | /10 V |
| 30255 | Battery I | I16 | /10 A |
| 33000 | SOC | U16 | /100 % |
| 33001 | SOH | U16 | /100 % |
| 10994-11001 | Pmeter (per phase + total) | I32 | /1000 kW |
| 11009-11015 | Grid V/A/Hz | U16 | /10, /100 |
| 11032 | Inverter Temp | I16 | /10 °C |
| 33003 | BMS Pack Temperature | U16 | /10 °C |
| 31102-31115 | Total Energy Counters | U32 | /10 kWh |
| 31000-31006 | Daily Energy Counters | U16 | /10 kWh |

---

## Tested With

- BMZ Power2Grid inverter
- BMZ Hyperion battery (20 kWh)
- Solinteg MHT series hybrid inverters

---

## Disclaimer

This is an **unofficial** integration. Use at your own risk.

---

## License

MIT License
