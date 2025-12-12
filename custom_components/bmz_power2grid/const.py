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

# Register map (from what you already validated)
REG_PV_POWER_W_INT32 = 0x2B14        # 11028
REG_BATTERY_POWER_W_INT32 = 0x2AF8   # 11000  (signed; negative = charging)
REG_INVERTER_TEMP_C_U16 = 0x2B18     # 11032  (scale 0.1)
REG_BATTERY_TEMP_C_U16 = 0x80EB      # 33003  (scale 0.1)
REG_BATTERY_SOH_PCT_U16 = 0x80E9     # 33001  (scale 0.01 => 9900 => 99.00%)

# Battery SOC
# Verified on your captures: 0x80E8 returns e.g. 1500 when the app shows 15.00%.
REG_BATTERY_SOC_PCT_U16 = 0x80E8     # 33000 (scale 0.01 => 1500 => 15.00%)

# Grid blocks (raw): Voltage/Current/Frequency (3 x u16 per phase)
REG_GRID_L1_BLOCK_U16 = 0x75F8       # 30200  (V*10, A*100, Hz*100)
REG_GRID_L2_BLOCK_U16 = 0x7602       # 30210  (V*10, A*100, Hz*100)
REG_GRID_L3_BLOCK_U16 = 0x760C       # 30220  (V*10, A*100, Hz*100)

# Grid power per phase (3 x int32 in one block): [L1_W, L2_W, L3_W]
# Your captures: 0x7A44/6 -> [0,685, 0,656, 0,895] which matches the app's per-phase grid kW magnitude.
REG_GRID_POWER_L123_W_INT32 = 0x7A44  # 31300, count=6 (int32 x3)

# The app shows grid power as negative when importing (night). Default to invert.
GRID_POWER_SIGN = -1

# Scaling assumptions (adjust later if you want exact)
SCALE_INVERTER_TEMP = 0.1
SCALE_BATTERY_TEMP = 0.1
SCALE_SOH = 0.01
SCALE_SOC = 0.01

SCALE_GRID_V = 0.1
SCALE_GRID_A = 0.01
SCALE_GRID_HZ = 0.01