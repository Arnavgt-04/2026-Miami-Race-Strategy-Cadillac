# report/generate_pdf.py
# Generates charts and assembles the final 4-page PDF report
# Run this file directly to produce the report

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from reportlab.platypus import KeepTogether
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, Image, PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from data.compounds_2026 import COMPOUNDS, FORECAST
from data.weather import get_race_weekend_forecast
from models.deg_model import build_full_deg_model, predict_lap_times
from models.strategy_sim import run_full_simulation

# Output paths
CHARTS_DIR  = os.path.join(os.path.dirname(__file__), '..', 'cache')
OUTPUT_PDF  = os.path.join(os.path.dirname(__file__), '..', 'Cadillac_Miami_2026_Strategy_Report.pdf')

# Brand colours
CADILLAC_BLACK  = colors.HexColor('#0A0A0A')
CADILLAC_GOLD   = colors.HexColor('#B8952A')
CADILLAC_WHITE  = colors.white
ACCENT_GREY     = colors.HexColor('#2A2A2A')
LIGHT_GREY      = colors.HexColor('#F5F5F5')


# ─────────────────────────────────────────────
#  CHART 1 — Tyre Degradation Curves
# ─────────────────────────────────────────────

def make_deg_curves_chart(deg_rates):
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('#0A0A0A')
    ax.set_facecolor('#0A0A0A')

    base_pace   = 92.0
    compound_styles = {
        'SOFT':   {'colour': '#E8002D', 'laps': 22},
        'MEDIUM': {'colour': '#FFD700', 'laps': 35},
        'HARD':   {'colour': '#CCCCCC', 'laps': 50},
    }

    for compound, style in compound_styles.items():
        num_laps  = style['laps']
        lap_times = predict_lap_times(compound, num_laps, base_pace, deg_rates)
        laps      = list(range(1, num_laps + 1))

        ax.plot(
            laps, lap_times,
            color=style['colour'],
            linewidth=2.5,
            label=f"{compound} (C{'5' if compound=='SOFT' else '4' if compound=='MEDIUM' else '3'})"
        )

        # Mark thermal cliff
        cliff = COMPOUNDS[compound]['thermal_cliff_lap']
        if cliff <= num_laps:
            ax.axvline(
                x=cliff, color=style['colour'],
                linestyle='--', alpha=0.4, linewidth=1
            )

    ax.set_xlabel('Tyre Age (Laps)', color='white', fontsize=11)
    ax.set_ylabel('Predicted Lap Time (s)', color='white', fontsize=11)
    ax.set_title(
        'Tyre Degradation Curves — Miami 2026 (Race Conditions)',
        color='white', fontsize=13, fontweight='bold', pad=15
    )
    ax.tick_params(colors='white')
    ax.spines['bottom'].set_color('#444444')
    ax.spines['left'].set_color('#444444')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(
        facecolor='#1A1A1A', labelcolor='white',
        edgecolor='#444444', fontsize=10
    )
    ax.grid(True, alpha=0.15, color='white')

    path = os.path.join(CHARTS_DIR, 'chart_deg_curves.png')
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='#0A0A0A')
    plt.close()
    print(f"  Saved: {path}")
    return path


# ─────────────────────────────────────────────
#  CHART 2 — Strategy Comparison Bar Chart
# ─────────────────────────────────────────────

def make_strategy_comparison_chart(perez_dry, perez_sc, bottas_dry):
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    fig.patch.set_facecolor('#0A0A0A')

    datasets = [
        (axes[0], perez_dry,  "Perez — Dry Race",        '#B8952A'),
        (axes[1], perez_sc,   "Perez — Safety Car",       '#E8002D'),
        (axes[2], bottas_dry, "Bottas — Dry Race",        '#4A90D9'),
    ]

    for ax, results, title, bar_colour in datasets:
        ax.set_facecolor('#0A0A0A')

        names = [r['strategy'].replace('1-Stop: ', '').replace('2-Stop: ', '')
                 for r in results]
        times = [r['total_time_s'] for r in results]

        # Normalise to show delta from fastest
        min_time = min(times)
        deltas   = [t - min_time for t in times]

        bars = ax.barh(
            names, deltas,
            color=bar_colour, alpha=0.85, edgecolor='#333333'
        )

        # Label each bar with delta
        for bar, delta in zip(bars, deltas):
            ax.text(
                bar.get_width() + 0.1,
                bar.get_y() + bar.get_height() / 2,
                f'+{delta:.1f}s',
                va='center', color='white', fontsize=8
            )

        ax.set_title(title, color='white', fontsize=10, fontweight='bold')
        ax.set_xlabel('Time Delta vs Optimal (s)', color='white', fontsize=9)
        ax.tick_params(colors='white', labelsize=8)
        ax.spines['bottom'].set_color('#444444')
        ax.spines['left'].set_color('#444444')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, alpha=0.15, color='white', axis='x')
        ax.invert_yaxis()

    plt.suptitle(
        'Strategy Comparison — Time Delta from Optimal',
        color='white', fontsize=13, fontweight='bold', y=1.02
    )

    path = os.path.join(CHARTS_DIR, 'chart_strategy_comparison.png')
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='#0A0A0A')
    plt.close()
    print(f"  Saved: {path}")
    return path


# ─────────────────────────────────────────────
#  CHART 3 — Pit Window Timing
# ─────────────────────────────────────────────

def make_pit_window_chart():
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor('#0A0A0A')
    ax.set_facecolor('#0A0A0A')

    strategies = {
        'Perez: H-M (Optimal Dry)':        (1,  28, 57, ['HARD', 'MEDIUM']),
        'Perez: M-H (Alt Dry)':             (1,  25, 57, ['MEDIUM', 'HARD']),
        'Both: M-H Late (SC Optimal)':      (1,  30, 57, ['MEDIUM', 'HARD']),
        'Bottas: M-H (Optimal Dry)':        (1,  25, 57, ['MEDIUM', 'HARD']),
        '2-Stop: S-M-H':                    (1,  15, 37, ['SOFT', 'MEDIUM', 'HARD']),
    }

    compound_colours = {
        'SOFT':   '#E8002D',
        'MEDIUM': '#FFD700',
        'HARD':   '#CCCCCC',
    }

    y_positions = list(range(len(strategies)))

    for y, (label, (start, pit1, end, compounds)) in zip(
        y_positions, strategies.items()
    ):
        if len(compounds) == 2:
            # Stint 1
            ax.barh(
                y, pit1 - start, left=start,
                color=compound_colours[compounds[0]],
                edgecolor='#0A0A0A', height=0.5, alpha=0.9
            )
            # Stint 2
            ax.barh(
                y, end - pit1, left=pit1,
                color=compound_colours[compounds[1]],
                edgecolor='#0A0A0A', height=0.5, alpha=0.9
            )
            # Pit marker
            ax.axvline(x=pit1, color='white', linestyle=':', alpha=0.5, linewidth=1)

        elif len(compounds) == 3:
            pit2 = 37
            ax.barh(
                y, 15, left=start,
                color=compound_colours[compounds[0]],
                edgecolor='#0A0A0A', height=0.5, alpha=0.9
            )
            ax.barh(
                y, 22, left=15,
                color=compound_colours[compounds[1]],
                edgecolor='#0A0A0A', height=0.5, alpha=0.9
            )
            ax.barh(
                y, 20, left=37,
                color=compound_colours[compounds[2]],
                edgecolor='#0A0A0A', height=0.5, alpha=0.9
            )
            ax.axvline(x=15, color='white', linestyle=':', alpha=0.5, linewidth=1)
            ax.axvline(x=37, color='white', linestyle=':', alpha=0.5, linewidth=1)

    ax.set_yticks(y_positions)
    ax.set_yticklabels(list(strategies.keys()), color='white', fontsize=9)
    ax.set_xlabel('Lap Number', color='white', fontsize=10)
    ax.set_title(
        'Pit Stop Windows — Miami 2026 (57 Laps)',
        color='white', fontsize=12, fontweight='bold', pad=12
    )
    ax.set_xlim(0, 57)
    ax.tick_params(colors='white')
    ax.spines['bottom'].set_color('#444444')
    ax.spines['left'].set_color('#444444')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, alpha=0.15, color='white', axis='x')

    # Legend
    legend_patches = [
        mpatches.Patch(color='#E8002D', label='Soft (C5)'),
        mpatches.Patch(color='#FFD700', label='Medium (C4)'),
        mpatches.Patch(color='#CCCCCC', label='Hard (C3)'),
    ]
    ax.legend(
        handles=legend_patches, facecolor='#1A1A1A',
        labelcolor='white', edgecolor='#444444',
        fontsize=9, loc='lower right'
    )

    path = os.path.join(CHARTS_DIR, 'chart_pit_windows.png')
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='#0A0A0A')
    plt.close()
    print(f"  Saved: {path}")
    return path


# ─────────────────────────────────────────────
#  PDF ASSEMBLY
# ─────────────────────────────────────────────

def build_pdf(chart_deg, chart_strategy, chart_pit, weather, perez_dry, perez_sc, bottas_dry):

    doc   = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=A4,
        leftMargin=15*mm,
        rightMargin=15*mm,
        topMargin=12*mm,
        bottomMargin=12*mm,
    )
    story = []
    W     = A4[0] - 30*mm  # usable page width

    # ── Styles ──
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CadillacTitle',
        fontSize=22, fontName='Helvetica-Bold',
        textColor=CADILLAC_GOLD, alignment=TA_CENTER,
        spaceAfter=6*mm,
    )
    subtitle_style = ParagraphStyle(
        'CadillacSub',
        fontSize=11, fontName='Helvetica',
        textColor=colors.HexColor('#333333'),  # was colors.white
        alignment=TA_CENTER,
        spaceAfter=1*mm,
    )
    section_style = ParagraphStyle(
        'CadillacSection',
        fontSize=13, fontName='Helvetica-Bold',
        textColor=CADILLAC_GOLD, spaceBefore=4*mm, spaceAfter=2*mm,
    )
    body_style = ParagraphStyle(
        'CadillacBody',
        fontSize=9, fontName='Helvetica',
        textColor=colors.black, spaceAfter=2*mm, leading=14,
    )
    small_style = ParagraphStyle(
        'CadillacSmall',
        fontSize=8, fontName='Helvetica',
        textColor=colors.grey, spaceAfter=1*mm,
    )
    bold_style = ParagraphStyle(
        'CadillacBold',
        fontSize=9, fontName='Helvetica-Bold',
        textColor=colors.black, spaceAfter=1*mm,
    )

    def gold_rule():
        return HRFlowable(
            width='100%', thickness=1.5,
            color=CADILLAC_GOLD, spaceAfter=3*mm, spaceBefore=1*mm
        )

    def grey_rule():
        return HRFlowable(
            width='100%', thickness=0.5,
            color=colors.lightgrey, spaceAfter=2*mm, spaceBefore=1*mm
        )

    # ════════════════════════════════════════
    #  PAGE 1 — Context & Inputs
    # ════════════════════════════════════════

    story.append(Paragraph("CADILLAC FORMULA 1 TEAM", title_style))
    story.append(Paragraph("2026 Miami Grand Prix — Race Strategy Report", subtitle_style))
    story.append(Paragraph("Round 4 | Miami International Autodrome | Sprint Weekend", subtitle_style))
    story.append(Spacer(1, 2*mm))
    story.append(gold_rule())

    # Team snapshot table
    story.append(Paragraph("TEAM SNAPSHOT", section_style))

    team_data = [
        ['', 'Sergio Perez (#11)', 'Valtteri Bottas (#77)'],
        ['Season Best',       'P17 (Japan — on lead lap)', 'P13 (Australia)'],
        ['Current Standing',  'P19 in WDC',               'P20 in WDC'],
        ['Tyre Strength',     'Elite management, long stints', 'Technical feedback, consistency'],
        ['Japan Strategy',    'Medium start',              'Hard start (underperformed)'],
        ['Miami Upgrade',     'First aero package confirmed for this weekend', ''],
    ]

    team_table = Table(team_data, colWidths=[35*mm, 75*mm, 65*mm])
    team_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  CADILLAC_BLACK),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  CADILLAC_GOLD),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 8),
        ('BACKGROUND',    (0, 1), (-1, -1), LIGHT_GREY),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('SPAN',          (1, 5), (2, 5)),
    ]))
    story.append(team_table)
    story.append(Spacer(1, 3*mm))

    # Weather table
    story.append(grey_rule())
    story.append(Paragraph("WEEKEND WEATHER FORECAST", section_style))
    story.append(Paragraph(
        "Source: Open-Meteo API | Miami Gardens (25.958°N, 80.239°W) | Fetched live",
        small_style
    ))

    sessions_to_show = ['Practice 1', 'Sprint Race', 'Qualifying', 'Grand Prix']
    weather_header   = ['Session', 'Air Temp', 'Track Temp', 'Humidity', 'Rain %', 'Wind']
    weather_data     = [weather_header]

    if weather:
        for s in sessions_to_show:
            if s in weather:
                d = weather[s]
                rain = d['rain_prob_pct']
                rain_str = f"{rain}% ⚠" if rain >= 20 else f"{rain}%"
                weather_data.append([
                    s,
                    f"{d['air_temp_c']}°C",
                    f"{d['track_temp_c']}°C",
                    f"{d['humidity_pct']}%",
                    rain_str,
                    f"{d['wind_mph']} mph",
                ])
    else:
        weather_data.append(['Data unavailable', '', '', '', '', ''])

    weather_table = Table(weather_data, colWidths=[40*mm, 25*mm, 27*mm, 25*mm, 22*mm, 26*mm])
    weather_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  CADILLAC_BLACK),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  CADILLAC_GOLD),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ALIGN',         (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TEXTCOLOR',     (4, 4), (4, 4),   colors.HexColor('#CC0000')),
    ]))
    story.append(weather_table)
    story.append(Spacer(1, 3*mm))

    # Compound table
    story.append(grey_rule())
    story.append(Paragraph("TYRE COMPOUND ALLOCATION — MIAMI 2026", section_style))
    story.append(Paragraph(
        "Pirelli confirmed allocation: C3 (Hard) / C4 (Medium) / C5 (Soft). "
        "Softest available range chosen for Miami's smooth, thermally demanding surface.",
        body_style
    ))

    compound_data = [
        ['Compound', 'Pirelli', 'Pace Delta', 'Deg Rate (adj.)', 'Thermal Cliff', 'Max Stint'],
        ['SOFT',   'C5', 'Baseline', '0.0560s/lap', 'Lap 16', '~18 laps'],
        ['MEDIUM', 'C4', '+0.55s',   '0.0493s/lap', 'Lap 30', '~35 laps'],
        ['HARD',   'C3', '+0.90s',   '0.0318s/lap', 'Lap 50', '~57 laps'],
    ]

    comp_colours = ['#E8002D', '#FFD700', '#AAAAAA']
    compound_table = Table(compound_data, colWidths=[28*mm, 22*mm, 25*mm, 32*mm, 30*mm, 28*mm])
    compound_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  CADILLAC_BLACK),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  CADILLAC_GOLD),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ALIGN',         (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND',    (0, 1), (0, 1),   colors.HexColor('#E8002D')),
        ('BACKGROUND',    (0, 2), (0, 2),   colors.HexColor('#FFD700')),
        ('BACKGROUND',    (0, 3), (0, 3),   colors.HexColor('#AAAAAA')),
        ('TEXTCOLOR',     (0, 1), (0, 3),   colors.white),
    ]))
    story.append(compound_table)
    story.append(Paragraph(
        "Deg rates calibrated from 3,369 clean laps of FastF1 Miami data (2022–2025), "
        "then adjusted +7% for 2026 narrower tyre construction and track temperature delta.",
        small_style
    ))

    story.append(PageBreak())

    # ════════════════════════════════════════
    #  PAGE 2 — Degradation Analysis
    # ════════════════════════════════════════

    story.append(Paragraph("TYRE DEGRADATION ANALYSIS", title_style))
    story.append(Spacer(1, 3*mm))
    story.append(gold_rule())

    story.append(Paragraph("DEGRADATION CURVES — MIAMI 2026 RACE CONDITIONS", section_style))
    story.append(Paragraph(
        "Predicted lap times per compound based on FastF1-calibrated deg rates. "
        "Dashed vertical lines mark estimated thermal cliff points where deg accelerates. "
        "Base pace set to 92.0s for visualisation. Track temp: 36.6°C (race night forecast).",
        body_style
    ))

    story.append(Image(chart_deg, width=W, height=W * 0.5))
    story.append(Spacer(1, 3*mm))

    # Key observations
    story.append(Paragraph("KEY OBSERVATIONS", section_style))

    obs = [
        ["1.", "Miami favours 1-stop strategies in all four previous editions. "
               "28 of 30 points-scoring finishes from 2022-2025 were 1-stoppers."],
        ["2.", "The C5 Soft is fastest early but reaches its thermal cliff by lap 16 "
               "in Miami's heat. Useful for qualifying simulation and SC restarts only."],
        ["3.", "The C4 Medium is the workhorse compound — preferred opening stint tyre "
               "for 15 of 20 drivers in 2025. Manages heat well up to ~30 laps."],
        ["4.", "The C3 Hard shows remarkably flat degradation under race conditions "
               "and is the preferred closing stint tyre for 1-stop strategies."],
        ["5.", "2026 regulation adjustment: narrower tyres (25mm front, 30mm rear) "
               "reduce contact patch area, increasing thermal load per unit area. "
               "A 7% upward multiplier is applied to all historical deg rates."],
        ["6.", "Race night conditions (36.6°C track vs 52°C daytime) significantly "
               "reduce thermal deg vs Sprint Race. 1-stop strategies become more viable "
               "in cooler evening temperatures."],
    ]

    for num, text in obs:
        row_data = [[Paragraph(num, bold_style), Paragraph(text, body_style)]]
        obs_table = Table(row_data, colWidths=[8*mm, W - 8*mm])
        obs_table.setStyle(TableStyle([
            ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING',    (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        story.append(obs_table)

    story.append(PageBreak())

    # ════════════════════════════════════════
    #  PAGE 3 — Strategy Recommendations
    # ════════════════════════════════════════

    story.append(Paragraph("RACE STRATEGY RECOMMENDATIONS", title_style))
    story.append(Spacer(1, 3*mm))
    story.append(gold_rule())

    story.append(Paragraph("STRATEGY SIMULATION RESULTS", section_style))
    story.append(Paragraph(
        "57-lap race simulation run for all viable compound combinations. "
        "Pit loss: 22s. Perez deg advantage: 10% reduction applied to all compounds. "
        "SC scenario assumes deployment laps 28-31 (consistent with Miami history).",
        body_style
    ))

    story.append(Image(chart_strategy, width=W, height=W * 0.42))
    story.append(Spacer(1, 2*mm))

    story.append(Paragraph("PIT STOP TIMING WINDOWS", section_style))
    story.append(Image(chart_pit, width=W, height=W * 0.38))
    story.append(Spacer(1, 3*mm))

    story.append(grey_rule())

    # Final recommendations table
    story.append(Paragraph("RECOMMENDED STRATEGIES", section_style))

    rec_data = [
    [
        Paragraph('<b>Driver</b>', small_style),
        Paragraph('<b>Scenario</b>', small_style),
        Paragraph('<b>Recommended Strategy</b>', small_style),
        Paragraph('<b>Pit Lap</b>', small_style),
        Paragraph('<b>Rationale</b>', small_style),
    ],
    [
        Paragraph('Perez', body_style),
        Paragraph('Dry Race', body_style),
        Paragraph('Hard → Medium', body_style),
        Paragraph('Lap 28', body_style),
        Paragraph('Perez tyre management extends Hard stint. Fresher Mediums in traffic.', body_style),
    ],
    [
        Paragraph('Perez', body_style),
        Paragraph('Safety Car', body_style),
        Paragraph('Medium → Hard (late)', body_style),
        Paragraph('Lap 30+', body_style),
        Paragraph('Extend Medium stint, pit under SC to emerge on fresh Hards.', body_style),
    ],
    [
        Paragraph('Bottas', body_style),
        Paragraph('Dry Race', body_style),
        Paragraph('Medium → Hard', body_style),
        Paragraph('Lap 25', body_style),
        Paragraph('Classic Miami 1-stop. Hard carries to the flag with flat deg.', body_style),
    ],
    [
        Paragraph('Bottas', body_style),
        Paragraph('Safety Car', body_style),
        Paragraph('Medium → Hard (late)', body_style),
        Paragraph('Lap 30+', body_style),
        Paragraph('Mirror Perez — opportunistic SC pit maximises position gain.', body_style),
    ],
    [
        Paragraph('Both', body_style),
        Paragraph('Rain (29% risk)', body_style),
        Paragraph('Pit for Inters immediately', body_style),
        Paragraph('On request', body_style),
        Paragraph('100% cloud cover race night. First team to react gains 5-8 positions.', body_style),
    ],
]

    col_widths = [18*mm, 22*mm, 38*mm, 20*mm, 67*mm]
    rec_table  = Table(rec_data, colWidths=col_widths)
    rec_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  CADILLAC_BLACK),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  CADILLAC_GOLD),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 7.5),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND',    (0, 5), (-1, 5),  colors.HexColor('#FFF3CD')),
    ]))
    story.append(rec_table)
    story.append(Spacer(1, 3*mm))

    # Risk matrix
    risk_data = [
        ['Factor', 'Probability', 'Impact', 'Cadillac Action'],
        ['Safety Car',           'High (65%)',   'High',   'Stay out if on Medium, pit immediately if on Hard'],
        ['Rain during race',     'Medium (29%)', 'High',   'Pre-position Inters on pitlane wall from lap 20'],
        ['Rival 2-stop bluff',   'Medium',       'Medium', 'Hold 1-stop unless deg cliff materialises early'],
        ['Upgrade underperforms','Low',          'Medium', 'Revert to conservative pace management'],
        ['Track evolution',      'Certain',      'Low',    'Expect 0.5-1.0s natural improvement by lap 20'],
    ]

    risk_table = Table(risk_data, colWidths=[45*mm, 30*mm, 22*mm, 78*mm])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  CADILLAC_BLACK),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  CADILLAC_GOLD),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 7.5),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    story.append(KeepTogether([
        grey_rule(),
        Paragraph("RISK & OPPORTUNITY MATRIX", section_style),
        risk_table,
    ]))

    story.append(Spacer(1, 4*mm))
    story.append(grey_rule())
    story.append(Paragraph(
        
        "Report generated programmatically using FastF1 telemetry data (2022-2025), "
        "Open-Meteo live forecast API, and a linear tyre degradation simulation model. "
        "Assumptions: 22s pit loss, 57-lap race distance, Perez 10% deg management advantage. "
        "Author: Arnav Timmapur | github.com/Arnavgt-04/2026-Miami-Race-Strategy-Cadillac",
        small_style
    ))

    doc.build(story)
    print(f"\n  PDF saved to: {OUTPUT_PDF}")


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\nGenerating Cadillac Miami 2026 Strategy Report...")

    race_track_temp = 36.6

    print("\n[1/5] Calibrating deg model...")
    deg_rates = build_full_deg_model(track_temp_c=race_track_temp)

    print("\n[2/5] Running strategy simulations...")
    perez_dry  = run_full_simulation('perez',  race_track_temp, include_sc=False)
    perez_sc   = run_full_simulation('perez',  race_track_temp, include_sc=True)
    bottas_dry = run_full_simulation('bottas', race_track_temp, include_sc=False)

    print("\n[3/5] Fetching weather forecast...")
    weather = get_race_weekend_forecast()

    print("\n[4/5] Generating charts...")
    chart_deg      = make_deg_curves_chart(deg_rates)
    chart_strategy = make_strategy_comparison_chart(perez_dry, perez_sc, bottas_dry)
    chart_pit      = make_pit_window_chart()

    print("\n[5/5] Building PDF...")
    build_pdf(chart_deg, chart_strategy, chart_pit, weather, perez_dry, perez_sc, bottas_dry)

    print("\nDone. Check the project root folder for the PDF.")