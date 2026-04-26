# Cadillac F1 — 2026 Miami Grand Prix Strategy Report

A race strategy prediction tool built for the 2026 Miami Grand Prix, 
focused on tyre degradation modelling and pit stop strategy optimisation 
for the Cadillac Formula 1 Team.

## Context & Motivation

I've built this project as part of my application to be Cadillac Formula 1
Team's Race Strategy & Tyre Performance placement student for the 2026-27 cycle.

Miami 2026 is an important race for Cadillac, as it's their first showing at home 
as an American team on an American circuit, making it the most commercially 
and emotionally important weekend of their debut season. I wanted take that 
into account and ingrain the importance of personalisation to my application. 

The project was built with AI assistance (Claude) for code architecture, comments, 
and debugging support. I have picked data, its sources, its uses, and modelled 
degradation with my own chosen assumptions to make this report within a day.

## What it does

- Loads and processes 3,369 real laps of FastF1 timing data from Miami 
  2022–2025 to calibrate compound-specific tyre degradation rates
- Fetches a live race weekend weather forecast from the Open-Meteo API
- Applies 2026 regulation adjustments (narrower tyre dimensions, active 
  aero load profiles) to historical deg rates
- Simulates full 57-lap race time for six viable tyre strategies across 
  dry, safety car, and rain scenarios
- Models driver-specific tyre management (Perez vs Bottas)
- Generates a four-page PDF report with degradation curves, strategy 
  comparison charts, and pit window visualisations

## Methodology

Tyre degradation is modelled as a linear function of tyre age:

    lap_time(n) = base_pace + pace_delta + deg_rate × n + heat_modifier × track_temp

Deg rates are calibrated from FastF1 median stint data per compound, 
then adjusted upward by 7% for 2026 narrower tyre construction and by 
a track temperature modifier above a 40°C baseline.

Strategy simulation runs the full race distance for each compound 
combination, adds a 22s pit loss per stop (based on Miami historical 
data), and ranks strategies by total race time.

## Key findings — Miami 2026

- 1-stop strategies dominate, consistent with all four previous Miami 
  editions (28 of 30 points finishes were 1-stoppers)
- Perez optimal dry: Hard → Medium (pit lap 28)
- Bottas optimal dry: Medium → Hard (pit lap 25)
- Under Safety Car: both drivers benefit from extending to lap 30+ 
  before pitting
- Rain risk (29% probability, 100% cloud cover) is the biggest wildcard

## Data sources

- Lap timing data: FastF1 (Ergast + F1 live timing)
- Weather forecast: Open-Meteo API (no key required)
- Compound parameters: Pirelli official race weekend preview
- 2026 regulation data: FIA technical regulations, Pirelli press release

## Setup

```bash
git clone https://github.com/Arnavgt-04/2026-Miami-Race-Strategy-Cadillac
cd 2026-Miami-Race-Strategy-Cadillac
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

First run downloads FastF1 session data into the cache folder (~500MB). 
Subsequent runs use the local cache and take under 30 seconds.

## Limitations

- Linear deg model does not capture tyre cliff behaviour or graining
- Base pace estimate for Cadillac is extrapolated from Japan 2026 results
- 2026 regulation thermal multiplier (7%) is an assumption, not measured data
- Safety car probability and timing based on historical Miami averages

## Author

Built as a practical demonstration of race strategy analysis methods,
using publicly available motorsport data tools.