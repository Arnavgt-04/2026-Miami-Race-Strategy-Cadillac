# data/weather.py
# Fetches real Miami race weekend forecast from Open-Meteo API
# No API key needed, completely free

import requests
from datetime import datetime

# Miami Gardens coordinates (Hard Rock Stadium)
LAT = 25.958
LON = -80.239

def get_race_weekend_forecast():
    """
    Fetches hourly forecast for the Miami GP weekend (May 1-3 2026)
    Returns a dictionary of session-specific conditions
    """

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": [
            "temperature_2m",
            "precipitation_probability",
            "relativehumidity_2m",
            "windspeed_10m",
            "cloudcover",
        ],
        "timezone": "America/New_York",
        "start_date": "2026-05-01",
        "end_date": "2026-05-03",
        "wind_speed_unit": "mph",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        raw = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Weather fetch failed: {e}")
        print("Falling back to forecast estimates from compounds_2026.py")
        return None

    hourly = raw["hourly"]
    times  = hourly["time"]

    # Build a simple lookup: time string -> all variables
    by_hour = {}
    for i, t in enumerate(times):
        by_hour[t] = {
            "air_temp_c":        hourly["temperature_2m"][i],
            "rain_prob_pct":     hourly["precipitation_probability"][i],
            "humidity_pct":      hourly["relativehumidity_2m"][i],
            "wind_mph":          hourly["windspeed_10m"][i],
            "cloud_cover_pct":   hourly["cloudcover"][i],
        }

    # Key session start times (local Miami time, 24hr)
    # Friday  May 1  - Practice 1:        17:00
    # Friday  May 1  - Sprint Qualifying:  21:30
    # Saturday May 2 - Sprint Race:        17:00
    # Saturday May 2 - Qualifying:         21:00
    # Sunday  May 3  - Grand Prix:         21:00

    sessions = {
        "Practice 1":        "2026-05-01T17:00",
        "Sprint Qualifying":  "2026-05-01T21:00",
        "Sprint Race":        "2026-05-02T17:00",
        "Qualifying":         "2026-05-02T21:00",
        "Grand Prix":         "2026-05-03T21:00",
    }

    session_conditions = {}
    for session_name, time_key in sessions.items():
        if time_key in by_hour:
            data = by_hour[time_key].copy()

            # Estimate track temp from air temp
            # Night sessions: air temp + ~8C
            # Day sessions:   air temp + ~21C
            hour = int(time_key.split("T")[1].split(":")[0])
            if hour >= 18:
                data["track_temp_c"] = round(data["air_temp_c"] + 8, 1)
            else:
                data["track_temp_c"] = round(data["air_temp_c"] + 21, 1)

            session_conditions[session_name] = data
        else:
            print(f"  No forecast data found for {session_name} at {time_key}")

    return session_conditions


def print_forecast(conditions):
    """Pretty prints the session forecast to console"""
    if not conditions:
        print("No forecast data available")
        return

    print("\n" + "="*60)
    print("  MIAMI GP 2026 — WEEKEND WEATHER FORECAST")
    print("="*60)

    for session, data in conditions.items():
        print(f"\n  {session}")
        print(f"    Air Temp:      {data['air_temp_c']}°C")
        print(f"    Track Temp:    {data['track_temp_c']}°C")
        print(f"    Humidity:      {data['humidity_pct']}%")
        print(f"    Rain Prob:     {data['rain_prob_pct']}%")
        print(f"    Wind:          {data['wind_mph']} mph")
        print(f"    Cloud Cover:   {data['cloud_cover_pct']}%")

    print("\n" + "="*60 + "\n")


# Run directly to test
if __name__ == "__main__":
    print("Fetching Miami 2026 race weekend forecast...")
    conditions = get_race_weekend_forecast()
    print_forecast(conditions)