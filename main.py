# main.py
# Entry point — run this to generate the full Cadillac Miami 2026 strategy report

from models.deg_model import build_full_deg_model
from models.strategy_sim import run_full_simulation
from data.weather import get_race_weekend_forecast, print_forecast
from report.generate_pdf import (
    make_deg_curves_chart,
    make_strategy_comparison_chart,
    make_pit_window_chart,
    build_pdf,
)

if __name__ == "__main__":
    race_track_temp = 36.6

    print("\n[1/5] Calibrating deg model from FastF1 data...")
    deg_rates = build_full_deg_model(track_temp_c=race_track_temp)

    print("\n[2/5] Running strategy simulations...")
    perez_dry  = run_full_simulation('perez',  race_track_temp, include_sc=False)
    perez_sc   = run_full_simulation('perez',  race_track_temp, include_sc=True)
    bottas_dry = run_full_simulation('bottas', race_track_temp, include_sc=False)

    print("\n[3/5] Fetching live weather forecast...")
    weather = get_race_weekend_forecast()
    print_forecast(weather)

    print("\n[4/5] Generating charts...")
    chart_deg      = make_deg_curves_chart(deg_rates)
    chart_strategy = make_strategy_comparison_chart(perez_dry, perez_sc, bottas_dry)
    chart_pit      = make_pit_window_chart()

    print("\n[5/5] Building PDF...")
    build_pdf(chart_deg, chart_strategy, chart_pit,
              weather, perez_dry, perez_sc, bottas_dry)

    print("\nDone.")