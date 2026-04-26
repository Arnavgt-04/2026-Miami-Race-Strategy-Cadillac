# models/deg_model.py
# Fits a degradation model to real FastF1 Miami lap data
# Outputs calibrated deg rates per compound, adjusted for 2026 regulations

import numpy as np
import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data.compounds_2026 import COMPOUNDS, REG_2026_THERMAL_MULTIPLIER, HEAT_DEG_MODIFIER


def load_cached_stints():
    """
    Loads the stint summary CSV saved by historical_tires.py
    """
    cache_path = os.path.join(os.path.dirname(__file__), '..', 'cache', 'miami_stints.csv')

    if not os.path.exists(cache_path):
        print("No cached stint data found - run historical_tires.py first")
        return None

    return pd.read_csv(cache_path)


def calibrate_deg_rates(stints_df):
    """
    Takes real FastF1 stint data and computes median deg rate per compound.
    Filters out outliers (crashes, SC laps that slipped through, etc.)
    Returns a dictionary of calibrated deg rates.
    """

    calibrated = {}

    for compound in ['SOFT', 'MEDIUM', 'HARD']:
        subset = stints_df[
            (stints_df['Compound'] == compound) &
            (stints_df['DegRate'].notna())
        ]['DegRate']

        if len(subset) == 0:
            print(f"  No data for {compound}, using default from compounds_2026.py")
            calibrated[compound] = COMPOUNDS[compound]['deg_rate']
            continue

        # Use median to avoid outliers skewing the result
        median_deg = subset.median()

        # FastF1 deg rates from Miami come out negative because drivers
        # manage tyres and lap times improve slightly early in stint.
        # We take the absolute value and floor at 0.01 to keep it physical.
        calibrated[compound] = max(abs(median_deg), 0.01)

        print(f"  {compound}: raw median deg = {median_deg:.4f}s/lap "
              f"-> calibrated = {calibrated[compound]:.4f}s/lap")

    return calibrated


def apply_2026_adjustments(calibrated_rates, track_temp_c):
    """
    Applies two adjustments to the historical deg rates:
    1. 2026 regulation multiplier (narrower tyres = more thermal load)
    2. Track temperature modifier (hotter = more deg)
    """

    adjusted = {}
    baseline_track_temp = 40  # degrees C, our baseline assumption

    temp_delta        = max(track_temp_c - baseline_track_temp, 0)
    heat_extra_deg    = temp_delta * HEAT_DEG_MODIFIER

    for compound, rate in calibrated_rates.items():
        reg_adjusted  = rate * REG_2026_THERMAL_MULTIPLIER
        final_rate    = reg_adjusted + heat_extra_deg
        adjusted[compound] = round(final_rate, 4)

        print(f"  {compound}: historical {rate:.4f} "
              f"-> +2026 regs {reg_adjusted:.4f} "
              f"-> +heat {final_rate:.4f}s/lap")

    return adjusted


def predict_lap_times(compound, num_laps, base_pace, deg_rates):
    """
    Predicts lap time for each lap of a stint.

    compound:   'SOFT', 'MEDIUM', or 'HARD'
    num_laps:   how many laps the stint runs
    base_pace:  the theoretical fastest lap time in seconds (fuel corrected)
    deg_rates:  dictionary of adjusted deg rates from apply_2026_adjustments()

    Returns a list of predicted lap times.
    """

    pace_delta  = COMPOUNDS[compound]['pace_delta']
    deg_rate    = deg_rates[compound]
    lap_times   = []

    for lap in range(num_laps):
        lap_time = base_pace + pace_delta + (deg_rate * lap)
        lap_times.append(round(lap_time, 3))

    return lap_times


def build_full_deg_model(track_temp_c=52.0):
    """
    Master function that runs the full pipeline:
    1. Load cached FastF1 data
    2. Calibrate deg rates from real data
    3. Apply 2026 regulation and heat adjustments
    Returns final adjusted deg rates ready for strategy simulation
    """

    print("\n--- Calibrating deg model from FastF1 data ---")
    stints = load_cached_stints()

    if stints is None:
        print("Using default compound values from compounds_2026.py")
        return {c: COMPOUNDS[c]['deg_rate'] for c in COMPOUNDS}

    print("\nRaw historical deg rates:")
    calibrated = calibrate_deg_rates(stints)

    print(f"\nApplying 2026 adjustments (track temp: {track_temp_c}°C):")
    adjusted = apply_2026_adjustments(calibrated, track_temp_c)

    print("\nFinal adjusted deg rates for Miami 2026:")
    for compound, rate in adjusted.items():
        print(f"  {compound}: {rate:.4f}s/lap")

    return adjusted


# Run directly to test
if __name__ == "__main__":
    # Use race night track temp from our weather forecast
    race_track_temp = 36.6

    deg_rates = build_full_deg_model(track_temp_c=race_track_temp)

    # Show what predicted lap times look like over a 30 lap stint
    print("\n--- Sample predicted lap times (base pace = 92.0s) ---")
    base_pace = 92.0

    for compound in ['SOFT', 'MEDIUM', 'HARD']:
        times = predict_lap_times(compound, 20, base_pace, deg_rates)
        print(f"\n  {compound} (first 20 laps):")
        for i, t in enumerate(times):
            print(f"    Lap {i+1:2d}: {t:.3f}s")