# BMZ Power2Grid Home Assistant Integration

A native Home Assistant integration for **BMZ Power2Grid inverters** and **BMZ Hyperion battery systems**, based on **Modbus RTU over TCP**.

This integration was developed by reverse-engineering the local inverter communication and does **not rely on cloud services**.

---

## ✨ Features

- Local, fast and reliable polling (no cloud, no vendor lock-in)
- Supports:
  - BMZ Power2Grid inverter
  - BMZ Hyperion battery systems (e.g. 20 kWh)
- Full Home Assistant sensor support
- Compatible with the **Energy Dashboard**
- No external dependencies (no `pymodbus`)
- Designed for **Modbus RTU over TCP** (as implemented by BMZ)

---

## 📡 Communication Details

- **Protocol:** Modbus RTU over TCP (raw RTU frames, no MBAP)
- **Default Port:** `5743`
- **Slave ID:** `252`
- **Connection:** Direct TCP socket per poll cycle

This matches the real implementation used by BMZ devices and avoids common Modbus-TCP issues.

---

## 📊 Available Sensors

### Battery
- Battery Power (charge / discharge)
- Battery State of Charge (SOC)
- Battery State of Health (SOH)
- Battery Temperature
- BMS Status

### Inverter
- Inverter Power
- Inverter Temperature
- Operating Status

### PV
- PV Total Power
- PV Channel Power (if available)

### Grid
- Grid Voltage (L1 / L2 / L3)
- Grid Current (L1 / L2 / L3)
- Grid Frequency
- Grid Power (import / export)

All sensors are exposed with proper units and state classes for Home Assistant.

---

## ⚡ Energy Dashboard Support

The integration provides:
- Power sensors (`W`) with `state_class: measurement`
- Energy sensors (`kWh`) with `state_class: total_increasing`

This allows direct use in:
- **Solar Production**
- **Battery Storage**
- **Grid Import / Export**
- **Energy Consumption**

No additional YAML templates required.

---

## 🚀 Installation (via HACS)

1. Install **HACS** in Home Assistant
2. Go to **HACS → Integrations → Custom repositories**
3. Add this repository URL
4. Category: **Integration**
5. Install **BMZ Power2Grid**
6. Restart Home Assistant

---

## 🔧 Configuration

After installation:

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Select **BMZ Power2Grid Inverter**
4. Enter:
   - Inverter IP address
   - Port (default: `5743`)
   - Slave ID (default: `252`)

No YAML configuration required.

---

## 🧪 Status

This integration is currently in **early development** but already usable for monitoring and energy tracking.

Tested with:
- BMZ Power2Grid inverter
- BMZ Hyperion battery (20 kWh)

---

## ⚠️ Disclaimer

This is an **unofficial** integration.
BMZ does not provide public Modbus documentation for these devices.

Use at your own risk.

---

## 🤝 Contributing

Contributions are welcome:
- Additional register mappings
- Multi-battery setups
- Write support (advanced users)
- Documentation improvements

Please open an issue or pull request.

---

## 📄 License

MIT License

---

## 🙏 Acknowledgements

Special thanks to the Home Assistant community and everyone reverse-engineering real-world energy systems.