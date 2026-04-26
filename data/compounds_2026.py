# data/compounds_2026.py
# Pirelli compound parameters for Miami 2026
# Allocation confirmed: C3 (Hard) / C4 (Medium) / C5 (Soft)

RACE_LAPS = 57
PIT_LOSS_SECONDS = 22  # average pit lane time loss at Miami

COMPOUNDS = {
    "SOFT": {
        "pirelli_name": "C5",
        "colour": "#E8002D",       # Pirelli red
        "pace_delta": 0.0,         # seconds slower than soft on lap 1 (soft is baseline)
        "deg_rate": 0.085,         # seconds lost per lap (will be refined by FastF1 fit)
        "thermal_cliff_lap": 16,   # tyre typically falls off a cliff around here in Miami heat
        "max_stint": 18,
    },
    "MEDIUM": {
        "pirelli_name": "C4",
        "colour": "#FFF200",       # Pirelli yellow
        "pace_delta": 0.55,
        "deg_rate": 0.042,
        "thermal_cliff_lap": 30,
        "max_stint": 35,
    },
    "HARD": {
        "pirelli_name": "C3",
        "colour": "#FFFFFF",       # Pirelli white
        "pace_delta": 0.90,
        "deg_rate": 0.021,
        "thermal_cliff_lap": 50,
        "max_stint": 57,
    },
}

# 2026 regulation adjustment
# Narrower tyres = smaller contact patch = more thermal load per unit area
# Applied as a multiplier on top of deg_rate above
REG_2026_THERMAL_MULTIPLIER = 1.07  # 7% higher deg than 2025 historical baseline

# Miami-specific heat modifier
# Each degree above 40C track temp adds this many seconds of extra deg per lap
HEAT_DEG_MODIFIER = 0.003

# Expected Miami 2026 conditions (from Open-Meteo forecast)
FORECAST = {
    "air_temp_c": 31,
    "track_temp_c": 52,      # estimate: air temp + ~21C for tarmac in direct sun
    "humidity_pct": 41,
    "rain_probability": {
        "friday_practice": 0.05,
        "saturday_sprint": 0.20,
        "sunday_race": 0.25,
    }
}