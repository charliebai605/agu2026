#!/usr/bin/env python3
"""plot_zone_vs_ref_scatter_events.py
Same three scatter plots as plot_zone_vs_ref_scatter.py (X = bottom
reference-segment average RMS, Y = DZ / FZ / FZ-DZ ratio), but this time
highlighting the specific hour each of the 15 global events' IASP91-predicted
P arrival falls in, numbered 1-15 (chronological), with a legend listing
number -> date + event. The background (all 312 hourly points, faint gray)
is kept for context.

Note: hourly resolution means events whose predicted arrival falls in the
same UTC hour of the same day land on the exact same point. All three
2026-06-24 events (M7.2/M7.5 Venezuela, M6.9 Japan) are within UTC hour 22,
so points 6/7/8 coincide -- 15 numbered events, but only 13 distinct dots.

Usage: python3 plot_zone_vs_ref_scatter_events.py
Output: agu2026/zone_vs_ref_scatter/{dz,fz,fz_dz_ratio}_vs_ref_rms_events.png
"""
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from plot_zone_vs_ref_scatter import DATES, load_all

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "_data")
EVENTS_CSV = os.path.join(HERE, "..", "globalq_iasp91_arrivals.csv")
OUT_DIR = os.path.join(HERE, "..", "zone_vs_ref_scatter")


def load_events():
    ev = pd.read_csv(EVENTS_CSV)
    ev["p_arrival_iasp91_utc"] = pd.to_datetime(ev["p_arrival_iasp91_utc"])
    ev["hour"] = ev["p_arrival_iasp91_utc"].dt.hour
    ev["date"] = ev["date_utc"].astype(str)
    ev = ev.sort_values("p_arrival_iasp91_utc").reset_index(drop=True)
    ev["n"] = ev.index + 1  # 1..15, chronological

    rows = []
    for d in DATES:
        ref = pd.read_csv(os.path.join(DATA_DIR, f"{d}_depth_rms_mseed_ref.csv"))
        zone = pd.read_csv(os.path.join(DATA_DIR, f"{d}_zone_rms_mseed_0p1-1p0Hz.csv"))
        m = ref.merge(zone, on="hour", how="inner")
        m["date"] = d
        rows.append(m)
    hourly = pd.concat(rows, ignore_index=True)
    hourly["fz_dz_ratio"] = hourly["rms_fault"] / hourly["rms_damage"]

    merged = ev.merge(hourly, on=["date", "hour"], how="left")
    return merged


N_EVENTS = 15
EVENT_COLORS = [plt.cm.tab20(i / 19) for i in range(N_EVENTS)]


def scatter_with_events(bg, ev, ycol, ylabel, title, out_png, log_y=False, xlim_hi=None, ylim_hi=None):
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    ax.scatter(bg["ref_rms"], bg[ycol], s=14, alpha=0.35,
               c="lightgray", edgecolor="none", zorder=1, label="all hours")

    ev = ev.copy()
    ev["dup_rank"] = ev.groupby(["date", "hour"]).cumcount()
    for _, row in ev.iterrows():
        color = EVENT_COLORS[int(row["n"]) - 1]
        ax.scatter(row["ref_rms"], row[ycol], s=60, alpha=0.95,
                   color=color, edgecolor="black", linewidth=0.6, zorder=3)
        ax.annotate(str(int(row["n"])), (row["ref_rms"], row[ycol]),
                    xytext=(6, 6 + row["dup_rank"] * 11), textcoords="offset points",
                    fontsize=8, fontweight="bold", color=color, zorder=4)

    ax.set_xscale("log")
    if log_y:
        ax.set_yscale("log")
    if xlim_hi is not None:
        lo, _ = ax.get_xlim()
        ax.set_xlim(lo, xlim_hi)
    if ylim_hi is not None:
        lo, _ = ax.get_ylim()
        ax.set_ylim(lo, ylim_hi)
    ax.set_xlabel("Bottom reference-segment average RMS\n"
                   "(strain rate, 1/s; depth_rms ref.csv, log scale)", fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.grid(lw=0.3, alpha=0.5)

    fig.subplots_adjust(right=0.62)
    y0 = 0.80
    for _, r in ev.iterrows():
        color = EVENT_COLORS[int(r["n"]) - 1]
        line = f"{int(r['n']):2d}  {r['date'][:4]}-{r['date'][4:6]}-{r['date'][6:]}  {r['label']}"
        fig.text(0.65, y0, line, fontsize=7.5, family="monospace",
                  va="top", ha="left", color=color, fontweight="bold")
        y0 -= 0.032
    fig.text(0.65, y0 - 0.01,
              "(points 6-8 coincide: all three\n6/24 events fall in UTC hour 22)",
              fontsize=7.5, style="italic", va="top", ha="left", color="black")

    fig.savefig(out_png, dpi=150)
    print(f"Saved {out_png}")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    bg = load_all()
    ev = load_events()
    print(ev[["n", "date", "label", "hour"]].to_string(index=False))

    scatter_with_events(bg, ev, "rms_damage", "Damage zone (DZ) RMS (strain rate, 1/s)",
                         "DZ RMS vs. bottom reference RMS -- 15 global events highlighted",
                         os.path.join(OUT_DIR, "dz_vs_ref_rms_events.png"), log_y=True,
                         xlim_hi=1e-7, ylim_hi=1e-7)
    scatter_with_events(bg, ev, "rms_fault", "Fault zone (FZ) RMS (strain rate, 1/s)",
                         "FZ RMS vs. bottom reference RMS -- 15 global events highlighted",
                         os.path.join(OUT_DIR, "fz_vs_ref_rms_events.png"), log_y=True,
                         xlim_hi=1e-7, ylim_hi=1e-7)
    scatter_with_events(bg, ev, "fz_dz_ratio", "FZ / DZ RMS ratio",
                         "FZ/DZ ratio vs. bottom reference RMS -- 15 global events highlighted",
                         os.path.join(OUT_DIR, "fz_dz_ratio_vs_ref_rms_events.png"), log_y=False,
                         xlim_hi=1e-7)


if __name__ == "__main__":
    main()
