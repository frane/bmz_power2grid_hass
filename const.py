DOMAIN = "bmz_power2grid"

DEFAULT_PORT = 5743
DEFAULT_UNIT_ID = 252
DEFAULT_SCAN_INTERVAL = 5  # seconds

CONF_HOST = "host"
CONF_PORT = "port"
CONF_UNIT_ID = "unit_id"
CONF_SCAN_INTERVAL = "scan_interval"

# Register map (from what you already validated)
REG_PV_POWER_W_INT32 = 0x2B14        # 11028
REG_BATTERY_POWER_W_INT32 = 0x2AF8   # 11000  (signed; negative = charging)
REG_INVERTER_TEMP_C_U16 = 0x2B18     # 11032  (scale 0.1)
REG_BATTERY_TEMP_C_U16 = 0x80EB      # 33003  (scale 0.1)
REG_BATTERY_SOH_PCT_U16 = 0x80E9     # 33001  (scale 0.01 => 9900 => 99.00%)

# SOC is the only one you had conflicting observations for.
# Put the one you want as canonical here:
REG_BATTERY_SOC_PCT_U16 = 0xC350     # 50000 (scale? you must choose; below we treat it as 0.1)

# Grid blocks (raw)
REG_GRID_L1_BLOCK_U16 = 0x75F8       # 30200  (U, I, f)
REG_GRID_L2_BLOCK_U16 = 0x7602       # 30210  (U, I, f)

# Scaling assumptions (adjust later if you want exact)
SCALE_INVERTER_TEMP = 0.1
SCALE_BATTERY_TEMP = 0.1
SCALE_SOH = 0.01
SCALE_SOC = 0.1

SCALE_GRID_V = 0.1
SCALE_GRID_A = 0.01
SCALE_GRID_HZ = 0.01