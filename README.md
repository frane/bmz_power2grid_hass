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

| Sensor | Modbus Spec Name | Description | Unit |
|--------|------------------|-------------|------|
| Solar Power | Total PV Input Power | Solar panel output | W |
| Battery Power | Battery_P | Net battery power (+discharge, -charge) | W |
| Battery Charging | - | Power flowing into battery | W |
| Battery Discharging | - | Power flowing from battery | W |
| Grid Power | Pmeter | Net grid power (+export, -import) | W |
| Grid Power L1/L2/L3 | Pmeter Phase A/B/C | Grid power per phase | W |
| Grid Import | - | Power drawn from grid | W |
| Grid Export | - | Power fed to grid | W |

### Battery State

| Sensor | Modbus Spec Name | Description | Unit |
|--------|------------------|-------------|------|
| Battery Level | SOC | State of Charge | % |
| Battery Health | SOH | State of Health | % |
| Battery Voltage | Battery_V | Battery voltage | V |
| Battery Current | Battery_I | Battery current (+discharge, -charge) | A |

### Grid

| Sensor | Description | Unit |
|--------|-------------|------|
| Grid Voltage L1/L2/L3 | Grid voltage per phase | V |
| Grid Current L1/L2/L3 | Grid current per phase | A |
| Grid Frequency | Grid frequency | Hz |

### Temperatures

| Sensor | Modbus Spec Name | Description | Unit |
|--------|------------------|-------------|------|
| Inverter Temperature | Inverter inner temp | Inverter temperature | °C |
| Battery Temperature | Pack temperature | Battery pack temperature | °C |

### Energy Totals (Lifetime)

Native counters from the device - persist across restarts.

| Sensor | Modbus Spec Name | Unit |
|--------|------------------|------|
| Total Solar Energy | Total PV generation | kWh |
| Total Battery Charged | Total battery charging energy | kWh |
| Total Battery Discharged | Total battery discharging energy | kWh |
| Total Grid Import | Total purchased energy | kWh |
| Total Grid Export | Total energy injected to grid | kWh |
| Total Consumption | Total load consumption | kWh |

### Daily Energy (Resets at Midnight)

| Sensor | Modbus Spec Name | Unit |
|--------|------------------|------|
| Today Solar Energy | Daily PV generation | kWh |
| Today Battery Charged | Daily battery charging energy | kWh |
| Today Battery Discharged | Daily battery discharging energy | kWh |
| Today Grid Import | Daily purchased energy | kWh |
| Today Grid Export | Daily energy injected to grid | kWh |
| Today Consumption | Daily load consumption | kWh |

---

## Understanding the Values

### Sign Conventions

**Battery Power:**
- **Positive** = Battery is discharging (providing power)
- **Negative** = Battery is charging (consuming power)

**Grid Power:**
- **Positive** = Exporting to grid (selling power)
- **Negative** = Importing from grid (buying power)

### Example Scenarios

| Scenario | Battery Power | Grid Power |
|----------|---------------|----------|
| Sunny day, battery charging, exporting to grid | -2000 W | +3000 W |
| Night, battery discharging, no grid usage | +1500 W | 0 W |
| Night, battery empty, importing from grid | 0 W | -2000 W |
| Cloudy, battery discharging + importing | +1000 W | -500 W |

---

## Energy Dashboard Setup

All energy sensors use `state_class: total_increasing` and can be directly used in the Home Assistant Energy Dashboard:

| Dashboard Section | Sensor to Use |
|-------------------|---------------|
| Solar Production | Total Solar Energy |
| Grid Consumption | Total Grid Import |
| Return to Grid | Total Grid Export |
| Battery Storage (In) | Total Battery Charged |
| Battery Storage (Out) | Total Battery Discharged |

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

| Register | Spec Name | Sensor | Type | Scale |
|----------|-----------|--------|------|-------|
| 11028 | Total PV Input Power | Solar Power | U32 | W |
| 30258 | Battery_P | Battery Power | I32 | W |
| 30254 | Battery_V | Battery Voltage | U16 | /10 V |
| 30255 | Battery_I | Battery Current | I16 | /10 A |
| 33000 | SOC | Battery Level | U16 | /100 % |
| 33001 | SOH | Battery Health | U16 | /100 % |
| 10994-11001 | Pmeter | Grid Power (per phase + total) | I32 | W |
| 11009-11015 | Grid V/A/Hz | Grid Voltage/Current/Frequency | U16 | /10, /100 |
| 11032 | Inverter inner temp | Inverter Temperature | I16 | /10 °C |
| 33003 | Pack temperature | Battery Temperature | U16 | /10 °C |
| 31102-31115 | Total energy counters | Total Energy sensors | U32 | /10 kWh |
| 31000-31006 | Daily energy counters | Today Energy sensors | U16 | /10 kWh |

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
