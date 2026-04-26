# models/strategy_sim.py
# Simulates full 57-lap race time for different tyre strategies
# Compares 1-stop and 2-stop options under dry and rain/SC scenarios
# Includes Perez-specific tyre management advantage

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data.compounds_2026 import RACE_LAPS, PIT_LOSS_SECONDS
from models.deg_model import predict_lap_times, build_full_deg_model

# Cadillac estimated base pace for Miami 2026
# Japan 2026: Perez finished P17, approx 4.5s/lap off race leaders
# Upgrade package expected to close ~0.3s, so conservative estimate:
BASE_PACE_PEREZ  = 94.5   # seconds per lap
BASE_PACE_BOTTAS = 95.0   # Bottas slightly off Perez pace this season

# Perez tyre management advantage — well documented across his career
# Reduces effective deg rate by ~10%
PEREZ_DEG_ADVANTAGE = 0.90

# Safety car probability and typical deployment lap based on Miami history
SC_PROBABILITY   = 0.65   # Miami has had SC in 3 of 4 races
SC_LAP           = 28     # typical SC window based on historical data
SC_LAP_TIME      = 120.0  # neutralised lap under SC


def apply_driver_advantage(deg_rates, driver='perez'):
    """
    Applies driver-specific tyre management to deg rates.
    Perez is historically one of the best tyre managers on the grid.
    """
    adjusted = deg_rates.copy()
    if driver == 'perez':
        for compound in adjusted:
            adjusted[compound] = round(adjusted[compound] * PEREZ_DEG_ADVANTAGE, 4)
        print(f"  Perez deg advantage applied: rates reduced by 10%")
    return adjusted


def simulate_race(strategy, base_pace, deg_rates, sc_laps=None):
    """
    Simulates a full race for a given strategy.

    strategy: list of tuples (compound, stint_length)
              e.g. [('MEDIUM', 28), ('HARD', 29)]
              stint lengths must sum to RACE_LAPS (57)

    Returns total race time in seconds and a lap-by-lap breakdown.
    """

    total_time  = 0
    lap_times   = []
    current_lap = 1

    for i, (compound, stint_length) in enumerate(strategy):
        stint_times = predict_lap_times(
            compound, stint_length, base_pace, deg_rates
        )

        for lap_time in stint_times:
            # Apply SC neutralisation if applicable
            if sc_laps and current_lap in sc_laps:
                lap_time = SC_LAP_TIME

            total_time += lap_time
            lap_times.append({
                'lap':      current_lap,
                'compound': compound,
                'lap_time': round(lap_time, 3),
            })
            current_lap += 1

        # Add pit stop time loss (not after the final stint)
        if i < len(strategy) - 1:
            total_time += PIT_LOSS_SECONDS

    return round(total_time, 1), lap_times


def build_strategies():
    """
    Defines all viable strategy combinations for Miami 2026.
    Stint lengths must sum to 57 laps.
    """
    return {
        # 1-stop strategies
        "1-Stop: M-H":   [('MEDIUM', 25), ('HARD',   32)],
        "1-Stop: H-M":   [('HARD',   28), ('MEDIUM', 29)],
        "1-Stop: M-H late pit": [('MEDIUM', 30), ('HARD', 27)],

        # 2-stop strategies
        "2-Stop: S-M-H": [('SOFT',   15), ('MEDIUM', 22), ('HARD', 20)],
        "2-Stop: M-H-M": [('MEDIUM', 20), ('HARD',   22), ('MEDIUM', 15)],
        "2-Stop: M-M-H": [('MEDIUM', 18), ('MEDIUM', 20), ('HARD',  19)],
    }


def run_full_simulation(driver='perez', track_temp_c=36.6, include_sc=False):
    """
    Runs all strategies for a given driver and conditions.
    Returns results sorted by total race time (fastest first).
    """

    print(f"\n{'='*60}")
    print(f"  STRATEGY SIMULATION — {driver.upper()}")
    print(f"  Track temp: {track_temp_c}°C | SC scenario: {include_sc}")
    print(f"{'='*60}")

    # Build deg rates from FastF1 data
    deg_rates = build_full_deg_model(track_temp_c=track_temp_c)

    # Apply driver-specific tyre management
    deg_rates = apply_driver_advantage(deg_rates, driver=driver)

    # Set base pace
    base_pace = BASE_PACE_PEREZ if driver == 'perez' else BASE_PACE_BOTTAS

    # SC laps to neutralise if SC scenario enabled
    sc_laps = list(range(SC_LAP, SC_LAP + 4)) if include_sc else None

    strategies  = build_strategies()
    results     = []

    for name, strategy in strategies.items():
        # Validate stint lengths sum to race distance
        total_laps = sum(s[1] for s in strategy)
        if total_laps != RACE_LAPS:
            print(f"  WARNING: {name} sums to {total_laps} laps, skipping")
            continue

        race_time, lap_by_lap = simulate_race(
            strategy, base_pace, deg_rates, sc_laps=sc_laps
        )

        results.append({
            'strategy':     name,
            'total_time_s': race_time,
            'total_time':   format_time(race_time),
            'pit_stops':    len(strategy) - 1,
            'sc_scenario':  include_sc,
        })

    # Sort fastest to slowest
    results.sort(key=lambda x: x['total_time_s'])
    return results


def format_time(seconds):
    """Converts total seconds to h:mm:ss.s format"""
    hours   = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs    = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:05.2f}"


def print_results(results, scenario_label):
    """Pretty prints simulation results"""
    print(f"\n  Results — {scenario_label}")
    print(f"  {'Rank':<6} {'Strategy':<25} {'Total Time':<15} {'Stops'}")
    print(f"  {'-'*55}")
    for i, r in enumerate(results):
        print(f"  {i+1:<6} {r['strategy']:<25} {r['total_time']:<15} {r['pit_stops']}")


# Run directly to test
if __name__ == "__main__":

    print("\nRunning Cadillac Miami 2026 Strategy Simulation...")
    print("Race conditions: Sunday night, 36.6C track, 29% rain risk\n")

    # --- PEREZ ---
    # Dry race
    perez_dry = run_full_simulation(
        driver='perez',
        track_temp_c=36.6,
        include_sc=False
    )
    print_results(perez_dry, "Perez — Dry Race")

    # SC scenario
    perez_sc = run_full_simulation(
        driver='perez',
        track_temp_c=36.6,
        include_sc=True
    )
    print_results(perez_sc, "Perez — Safety Car around lap 28")

    # --- BOTTAS ---
    # Dry race
    bottas_dry = run_full_simulation(
        driver='bottas',
        track_temp_c=36.6,
        include_sc=False
    )
    print_results(bottas_dry, "Bottas — Dry Race")

    # SC scenario
    bottas_sc = run_full_simulation(
        driver='bottas',
        track_temp_c=36.6,
        include_sc=True
    )
    print_results(bottas_sc, "Bottas — Safety Car around lap 28")

    print("\n--- KEY INSIGHT ---")
    print(f"  Perez optimal: {perez_dry[0]['strategy']}")
    print(f"  Bottas optimal: {bottas_dry[0]['strategy']}")
    print(f"  Best SC opportunity: {perez_sc[0]['strategy']}")