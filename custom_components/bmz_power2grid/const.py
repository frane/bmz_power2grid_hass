from __future__ import annotations

DOMAIN = "bmz_power2grid"

DEFAULT_PORT = 5743
DEFAULT_UNIT_ID = 252
DEFAULT_SCAN_INTERVAL = 5  # seconds

PLATFORMS: list[str] = ["sensor"]

# Use homeassistant.const for CONF_HOST and CONF_PORT
# Only define custom config keys here
CONF_UNIT_ID = "unit_id"
CONF_SCAN_INTERVAL = "scan_interval"

# =============================================================================
# REGISTER MAP - Based on official Solinteg Modbus Protocol v00.02 (2022-12-06)
# =============================================================================

# --- PV POWER ---
REG_PV_POWER_KW_U32 = 11028           # Total PV Input Power (U32, kW, /1000)

# --- BATTERY ---
REG_BATTERY_POWER_KW_I32 = 30258      # Battery_P (I32, kW, /1000) - positive=discharge, negative=charge
REG_BATTERY_VOLTAGE_U16 = 30254       # Battery_V (U16, V, /10)
REG_BATTERY_CURRENT_I16 = 30255       # Battery_I (I16, A, /10)
REG_BATTERY_MODE_U16 = 30256          # Battery_Mode (U16: 0=discharge, 1=charge)
REG_BATTERY_SOC_U16 = 33000           # SOC (U16, %, /100)
REG_BATTERY_SOH_U16 = 33001           # SOH (U16, %, /100)

# --- GRID METER POWER (from smart meter, signed: positive=export, negative=import) ---
REG_GRID_METER_L1_KW_I32 = 10994      # Pmeter on phase A (I32, kW, /1000)
REG_GRID_METER_L2_KW_I32 = 10996      # Pmeter on phase B (I32, kW, /1000)
REG_GRID_METER_L3_KW_I32 = 10998      # Pmeter on phase C (I32, kW, /1000)
REG_GRID_METER_TOTAL_KW_I32 = 11000   # Pmeter of three phases (I32, kW, /1000)

# --- GRID VOLTAGE/CURRENT/FREQUENCY (actual grid connection) ---
REG_GRID_L1_VOLTAGE_U16 = 11009       # Phase A Voltage (U16, V, /10)
REG_GRID_L1_CURRENT_U16 = 11010       # Phase A Current (U16, A, /10)
REG_GRID_L2_VOLTAGE_U16 = 11011       # Phase B Voltage (U16, V, /10)
REG_GRID_L2_CURRENT_U16 = 11012       # Phase B Current (U16, A, /10)
REG_GRID_L3_VOLTAGE_U16 = 11013       # Phase C Voltage (U16, V, /10)
REG_GRID_L3_CURRENT_U16 = 11014       # Phase C Current (U16, A, /10)
REG_GRID_FREQUENCY_U16 = 11015        # Grid Frequency (U16, Hz, /100)

# --- INVERTER AC POWER ---
REG_PAC_KW_I32 = 11016                # P_AC total (I32, kW, /1000)
REG_INVT_L1_POWER_KW_I32 = 30236      # Invt_A_P (I32, kW, /1000)
REG_INVT_L2_POWER_KW_I32 = 30242      # Invt_B_P (I32, kW, /1000)
REG_INVT_L3_POWER_KW_I32 = 30248      # Invt_C_P (I32, kW, /1000)

# --- TEMPERATURES ---
REG_INVERTER_TEMP_I16 = 11032         # Temp.1 - Inverter (I16, °C, /10)
REG_BATTERY_TEMP_U16 = 33003          # BMS Pack Temperature (U16, °C, /10)

# --- NATIVE ENERGY COUNTERS (use these instead of calculating!) ---
# Grid energy on meter (higher precision: /100)
REG_METER_EXPORT_ENERGY_U32 = 11002   # Total Grid-Injection Energy on Meter (U32, kWh, /100)
REG_METER_IMPORT_ENERGY_U32 = 11004   # Total Purchasing Energy from Grid on Meter (U32, kWh, /100)

# Inverter-side energy totals (/10 precision)
REG_TOTAL_GRID_EXPORT_U32 = 31102     # Total Energy Injected into Grid (U32, kWh, /10)
REG_TOTAL_GRID_IMPORT_U32 = 31104     # Total Purchased Energy from Grid (U32, kWh, /10)
REG_TOTAL_BATTERY_CHARGE_U32 = 31108  # Total Battery Charging Energy (U32, kWh, /10)
REG_TOTAL_BATTERY_DISCHARGE_U32 = 31110  # Total Battery Discharging Energy (U32, kWh, /10)
REG_TOTAL_PV_GENERATION_U32 = 31112   # Total PV Generation (U32, kWh, /10)
REG_TOTAL_LOAD_U32 = 31114            # Total Load Consumption (U32, kWh, /10)

# Daily energy counters (/10 precision)
REG_DAILY_GRID_EXPORT_U16 = 31000     # Daily Energy Injected to Grid (U16, kWh, /10)
REG_DAILY_GRID_IMPORT_U16 = 31001     # Daily Purchased Energy (U16, kWh, /10)
REG_DAILY_BATTERY_CHARGE_U16 = 31003  # Daily Battery Charging Energy (U16, kWh, /10)
REG_DAILY_BATTERY_DISCHARGE_U16 = 31004  # Daily Battery Discharging Energy (U16, kWh, /10)
REG_DAILY_PV_GENERATION_U16 = 31005   # Daily PV Generation (U16, kWh, /10)
REG_DAILY_LOAD_U16 = 31006            # Daily Load Consumption (U16, kWh, /10)

# --- SCALING FACTORS ---
SCALE_KW_TO_W = 1000                  # kW values from device need *1000 for W
SCALE_VOLTAGE = 0.1                   # /10 for V
SCALE_CURRENT = 0.1                   # /10 for A
SCALE_FREQUENCY = 0.01                # /100 for Hz
SCALE_TEMPERATURE = 0.1               # /10 for °C
SCALE_PERCENT = 0.01                  # /100 for %
SCALE_ENERGY_10 = 0.1                 # /10 for kWh
SCALE_ENERGY_100 = 0.01               # /100 for kWh