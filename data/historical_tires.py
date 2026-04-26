# data/historical_tires.py
# Loads real Miami GP lap data from FastF1 for 2022-2024
# 2025 data included if available in FastF1's database
# First run will be slow - FastF1 downloads and caches the session data
# Subsequent runs are fast because it reads from the cache folder

import fastf1
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Point FastF1 at our cache folder so it doesn't re-download every time
fastf1.Cache.enable_cache('../cache')

# Years to pull Miami data from
YEARS = [2022, 2023, 2024, 2025]

def load_miami_laps(years=YEARS):
    """
    Loads race lap data for Miami GP across multiple seasons.
    Returns a single combined DataFrame with all laps.
    """

    all_laps = []

    for year in years:
        print(f"  Loading Miami {year}...")
        try:
            session = fastf1.get_session(year, 'Miami', 'R')
            session.load(telemetry=False, weather=False, messages=False)

            laps = session.laps[[
                'Driver',
                'Team',
                'LapNumber',
                'LapTime',
                'Compound',
                'TyreLife',
                'Stint',
                'PitOutTime',
                'PitInTime',
                'IsAccurate',
            ]].copy()

            # Convert LapTime from timedelta to seconds
            laps['LapTimeSeconds'] = laps['LapTime'].dt.total_seconds()

            # Only keep accurate laps (removes in/out laps, SC laps etc)
            laps = laps[laps['IsAccurate'] == True]

            # Drop rows missing the key columns we need
            laps = laps.dropna(subset=['LapTimeSeconds', 'Compound', 'TyreLife'])

            # Tag which season this lap came from
            laps['Year'] = year

            all_laps.append(laps)
            print(f"    Got {len(laps)} clean laps from Miami {year}")

        except Exception as e:
            print(f"    Could not load Miami {year}: {e}")
            continue

    if not all_laps:
        print("No data loaded at all - check your internet connection")
        return None

    combined = pd.concat(all_laps, ignore_index=True)
    print(f"\n  Total clean laps loaded: {len(combined)}")
    return combined


def get_stint_summary(laps_df):
    """
    Summarises each stint: driver, year, compound, stint length,
    average lap time, and deg rate (seconds lost per lap).
    """

    summaries = []

    # Group by year, driver, and stint number
    grouped = laps_df.groupby(['Year', 'Driver', 'Stint'])

    for (year, driver, stint_num), stint_laps in grouped:
        if len(stint_laps) < 3:
            # Too short to be meaningful
            continue

        stint_laps = stint_laps.sort_values('LapNumber')
        compound   = stint_laps['Compound'].iloc[0]
        length     = len(stint_laps)
        avg_time   = stint_laps['LapTimeSeconds'].mean()

        # Deg rate: fit a simple linear regression to lap time vs tyre age
        # slope = how many seconds slower per lap as the tyre wears
        if length >= 4:
            import numpy as np
            tyre_ages  = stint_laps['TyreLife'].values
            lap_times  = stint_laps['LapTimeSeconds'].values
            slope, intercept = np.polyfit(tyre_ages, lap_times, 1)
        else:
            slope = None

        summaries.append({
            'Year':         year,
            'Driver':       driver,
            'Team':         stint_laps['Team'].iloc[0],
            'Stint':        stint_num,
            'Compound':     compound,
            'StintLength':  length,
            'AvgLapTime':   round(avg_time, 3),
            'DegRate':      round(slope, 4) if slope is not None else None,
        })

    return pd.DataFrame(summaries)


def get_compound_deg_stats(stint_summary_df):
    """
    Averages deg rate and stint length per compound across all years.
    This is what we use to calibrate our deg model.
    """

    stats = (
        stint_summary_df
        .groupby('Compound')
        .agg(
            AvgDegRate    = ('DegRate',     'mean'),
            MedianDegRate = ('DegRate',     'median'),
            AvgStintLen   = ('StintLength', 'mean'),
            MaxStintLen   = ('StintLength', 'max'),
            SampleSize    = ('DegRate',     'count'),
        )
        .round(4)
        .reset_index()
    )

    return stats


def print_compound_stats(stats_df):
    """Pretty prints compound stats to console"""
    print("\n" + "="*60)
    print("  MIAMI HISTORICAL TYRE DEG (2022-2025)")
    print("="*60)
    print(stats_df.to_string(index=False))
    print("="*60 + "\n")


# Run directly to test
if __name__ == "__main__":
    print("Loading Miami GP historical lap data via FastF1...")
    print("First run will take a few minutes to download - grab a coffee\n")

    laps    = load_miami_laps()

    if laps is not None:
        stints  = get_stint_summary(laps)
        stats   = get_compound_deg_stats(stints)
        print_compound_stats(stats)

        # Save for use by other modules
        laps.to_csv('../cache/miami_laps.csv', index=False)
        stints.to_csv('../cache/miami_stints.csv', index=False)
        print("  Raw data saved to cache/ for use by deg model")