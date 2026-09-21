#!/usr/bin/env python3
"""plot_hourly_scatter_combined.py
Same X/Y as plot_hourly_scatter.py (X = bottom reference-segment RMS, Y = DZ RMS /
FZ RMS / FZ-DZ ratio) but overlays multiple days on one plot instead of one PNG per
day. Color still encodes hour (UTC+8), same viridis_r discrete colorbar as
plot_hourly_scatter.py; marker SHAPE encodes which day, so a day's 24-hour cluster
being offset along the X axis is directly visible — this is the same X quantity
(bottom reference RMS) as the baseline-shift investigation in
bottom_rms_baseline_investigation.md.

Generates all three (DZ, FZ, FZ_DZ) in one run with axis ranges/ticks aligned across
the three: X (bottom reference RMS) is identical in all three since it's the same
source data; Y is shared between DZ and FZ (both strain rate, same units) so the two
are directly comparable; FZ_DZ's Y (a dimensionless ratio) keeps its own range since
its unit isn't comparable to DZ/FZ's Y.

Usage:
  python3 plot_hourly_scatter_combined.py --dates 20260910,20260911,20260912,20260913,20260914,20260915,20260916
Output: agu2026/hourly_scatter/{DZ,FZ,FZ_DZ}/combined_{first}_{last}.png
"""
import argparse
import os
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator, MultipleLocator

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "_data")
OUT_BASE = os.path.join(HERE, "..", "hourly_scatter")

cmap = plt.cm.viridis_r
day_cmap = plt.cm.tab10
MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*", "h", "<"]
TICK_STEP = 0.5e-9  # shared tick spacing for the strain-rate axes (X always; Y for DZ/FZ)


def week_bucket(dates):
    """Bucket YYYYMMDD strings into Mon-Sun calendar weeks. Returns
    (week_index array aligned to dates, list of (label, color) per week in order)."""
    dts = [datetime.strptime(d, "%Y%m%d") for d in dates]
    mondays = sorted({dt - timedelta(days=dt.weekday()) for dt in dts})
    week_of = {mon: i for i, mon in enumerate(mondays)}
    idx = [week_of[dt - timedelta(days=dt.weekday())] for dt in dts]
    week_cmap = plt.cm.get_cmap("turbo", len(mondays))
    labels = [f"{mon:%Y-%m-%d} ~ {mon + timedelta(days=6):%Y-%m-%d}" for mon in mondays]
    return idx, labels, week_cmap

YCOLS = {
    "DZ": ("rms_damage", "Damage zone (DZ) RMS (strain rate, 1/s)", True),
    "FZ": ("rms_fault", "Fault zone (FZ) RMS (strain rate, 1/s)", True),
    "FZ_DZ": ("fz_dz_ratio", "FZ / DZ RMS ratio", False),
}


def _find(date, suffixes):
    for suf in suffixes:
        p = os.path.join(DATA_DIR, f"{date}{suf}")
        if os.path.exists(p):
            return p
    raise FileNotFoundError(f"none of {suffixes} found for {date} in {DATA_DIR}")


def load_day(date):
    ref = pd.read_csv(_find(date, ("_depth_rms_tdms_ref.csv", "_depth_rms_mseed_ref.csv")))
    zone = pd.read_csv(_find(date, ("_zone_rms_stream.csv", "_zone_rms_mseed_0p1-1p0Hz.csv")))
    df = ref.merge(zone, on="hour").sort_values("hour").reset_index(drop=True)
    df["fz_dz_ratio"] = df["rms_fault"] / df["rms_damage"]
    df["date"] = date
    return df


def make_plot(df, dates, sub, xlim, ylim, color_by="hour", week_info=None, scale="linear"):
    ycol, ylabel, y_is_strain_rate = YCOLS[sub]

    fig, ax = plt.subplots(figsize=(7.5, 6))
    if color_by == "week":
        week_idx, week_labels, week_cmap = week_info
        for wi in sorted(set(week_idx)):
            wdates = [d for d, w in zip(dates, week_idx) if w == wi]
            wdf = df[df["date"].isin(wdates)]
            ax.scatter(wdf["ref_rms"], wdf[ycol], c=[week_cmap(wi)] * len(wdf), marker="o",
                       s=55, edgecolor="black", linewidth=0.4, zorder=3, alpha=0.85)
    else:
        for i, d in enumerate(dates):
            day_df = df[df["date"] == d]
            if color_by == "day":
                colors = [day_cmap(i)] * len(day_df)
            else:
                colors = [cmap(h / 23) for h in day_df["hour"]]
            ax.scatter(day_df["ref_rms"], day_df[ycol], c=colors, marker=MARKERS[i], s=70,
                       edgecolor="black", linewidth=0.6, zorder=3)

    if scale == "log":
        ax.set_xscale("log")
        ax.set_xlim(xlim[0] if xlim[0] > 0 else None, xlim[1])
        if ylim is not None and y_is_strain_rate:
            ax.set_yscale("log")
            ax.set_ylim(ylim[0] if ylim[0] > 0 else None, ylim[1])
        elif ylim is not None:
            ax.set_ylim(*ylim)
    else:
        ax.set_xlim(*xlim)
        ax.xaxis.set_major_locator(MultipleLocator(TICK_STEP))
        ax.ticklabel_format(axis="x", style="sci", scilimits=(0, 0))
        if ylim is not None:
            ax.set_ylim(*ylim)
            ax.yaxis.set_major_locator(MultipleLocator(TICK_STEP) if y_is_strain_rate else MaxNLocator(7))
        if y_is_strain_rate:
            ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    ax.set_xlabel("Bottom reference-segment RMS (strain rate, 1/s)", fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_title(f"{dates[0][:4]}-{dates[0][4:6]}-{dates[0][6:]} ~ "
                 f"{dates[-1][:4]}-{dates[-1][4:6]}-{dates[-1][6:]}: "
                 f"{sub} RMS vs. bottom reference RMS ({scale} axes)", fontsize=11, fontweight="bold")
    ax.grid(lw=0.3, alpha=0.5, which="both")

    if color_by == "hour":
        discrete_cmap = ListedColormap([cmap(h / 23) for h in range(24)])
        bounds = np.arange(-0.5, 24.5, 1)
        norm = BoundaryNorm(bounds, discrete_cmap.N)
        sm = plt.cm.ScalarMappable(cmap=discrete_cmap, norm=norm)
        tick_hours = list(range(0, 24, 3))
        cbar = fig.colorbar(sm, ax=ax, pad=0.02, fraction=0.05, ticks=tick_hours, boundaries=bounds)
        cbar.ax.invert_yaxis()
        cbar.set_ticklabels([f"{(h + 8) % 24:02d}:00" for h in tick_hours])
        cbar.set_label("Local hour (UTC+8)", fontsize=8)
        legend_title = "Date (marker shape)"
        legend_handles = [Line2D([0], [0], marker=MARKERS[i], color="w", markerfacecolor="gray",
                                 markeredgecolor="black", markersize=8,
                                 label=f"{dates[i][:4]}-{dates[i][4:6]}-{dates[i][6:]}")
                          for i in range(len(dates))]
    elif color_by == "day":
        legend_title = "Date"
        legend_handles = [Line2D([0], [0], marker=MARKERS[i], color="w", markerfacecolor=day_cmap(i),
                                 markeredgecolor="black", markersize=9,
                                 label=f"{dates[i][:4]}-{dates[i][4:6]}-{dates[i][6:]}")
                          for i in range(len(dates))]
    else:  # week
        _, week_labels, week_cmap = week_info
        legend_title = "Week (Mon–Sun)"
        legend_handles = [Line2D([0], [0], marker="o", color="w", markerfacecolor=week_cmap(wi),
                                 markeredgecolor="black", markersize=9, label=label)
                          for wi, label in enumerate(week_labels)]

    ax.legend(handles=legend_handles, title=legend_title, loc="upper left",
              bbox_to_anchor=(1.18, 1.0), fontsize=8, title_fontsize=8)

    fig.tight_layout()
    out_dir = os.path.join(OUT_BASE, sub)
    os.makedirs(out_dir, exist_ok=True)
    color_suffix = "" if color_by == "hour" else f"_by{color_by}"
    scale_suffix = "" if scale == "linear" else "_log"
    out_png = os.path.join(out_dir, f"combined_{dates[0]}_{dates[-1]}{color_suffix}{scale_suffix}.png")
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    print(f"Saved {out_png}")


def pad_range(lo, hi, frac=0.05):
    span = hi - lo
    return lo - span * frac, hi + span * frac


def pad_range_log(lo, hi, factor=1.15):
    return lo / factor, hi * factor


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dates", required=True, help="comma-separated YYYYMMDD list")
    ap.add_argument("--color-by", default="hour", choices=["hour", "day", "week"],
                    help="hour (default): viridis colorbar, marker shape = day. "
                         "day: one solid color per day (tab10) + marker shape = day, no hour colorbar. "
                         "week: one solid color per Mon-Sun calendar week (no per-day marker/legend "
                         "entry) -- use this for date ranges longer than 10 days.")
    ap.add_argument("--scale", default="linear", choices=["linear", "log", "both"],
                    help="axis scale. both generates one linear + one log PNG per sub-plot.")
    args = ap.parse_args()

    dates = [d.strip() for d in args.dates.split(",")]
    if args.color_by in ("hour", "day") and len(dates) > len(MARKERS):
        raise SystemExit(f"only {len(MARKERS)} distinct markers defined for --color-by {args.color_by}, "
                          f"got {len(dates)} dates (use --color-by week for longer ranges)")

    df = pd.concat([load_day(d) for d in dates], ignore_index=True)

    x_lim = pad_range(df["ref_rms"].min(), df["ref_rms"].max())
    dz_fz_lim = pad_range(min(df["rms_damage"].min(), df["rms_fault"].min()),
                           max(df["rms_damage"].max(), df["rms_fault"].max()))
    x_lim_log = pad_range_log(df["ref_rms"].min(), df["ref_rms"].max())
    dz_fz_lim_log = pad_range_log(min(df["rms_damage"].min(), df["rms_fault"].min()),
                                   max(df["rms_damage"].max(), df["rms_fault"].max()))

    week_info = week_bucket(dates) if args.color_by == "week" else None

    scales = ["linear", "log"] if args.scale == "both" else [args.scale]
    for scale in scales:
        xl, dzfzl = (x_lim, dz_fz_lim) if scale == "linear" else (x_lim_log, dz_fz_lim_log)
        make_plot(df, dates, "DZ", xl, dzfzl, color_by=args.color_by, week_info=week_info, scale=scale)
        make_plot(df, dates, "FZ", xl, dzfzl, color_by=args.color_by, week_info=week_info, scale=scale)
        make_plot(df, dates, "FZ_DZ", xl, None, color_by=args.color_by, week_info=week_info, scale=scale)


if __name__ == "__main__":
    main()
