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


def scatter_with_events(bg, ev, ycol, ylabel, title, out_png, log_y=False):
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    ax.scatter(bg["ref_rms"], bg[ycol], s=14, alpha=0.35,
               c="lightgray", edgecolor="none", zorder=1, label="all hours")
    ax.scatter(ev["ref_rms"], ev[ycol], s=55, alpha=0.9,
               c="crimson", edgecolor="black", linewidth=0.6, zorder=3)

    # stack labels for points sharing the same (date, hour) -- vertical offset
    ev = ev.copy()
    ev["dup_rank"] = ev.groupby(["date", "hour"]).cumcount()
    for _, row in ev.iterrows():
        dy = 1 + row["dup_rank"] * 0.35
        ax.annotate(str(int(row["n"])), (row["ref_rms"], row[ycol]),
                    xytext=(6, 6 + row["dup_rank"] * 11), textcoords="offset points",
                    fontsize=8, fontweight="bold", color="crimson", zorder=4)

    ax.set_xscale("log")
    if log_y:
        ax.set_yscale("log")
    ax.set_xlabel("Bottom reference-segment average RMS\n"
                   "(strain rate, 1/s; depth_rms ref.csv, log scale)", fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.grid(lw=0.3, alpha=0.5)

    legend_lines = [f"{int(r['n']):2d}  {r['date'][:4]}-{r['date'][4:6]}-{r['date'][6:]}  {r['label']}"
                     for _, r in ev.iterrows()]
    fig.subplots_adjust(right=0.62)
    fig.text(0.65, 0.90, "\n".join(legend_lines), fontsize=7.5, family="monospace",
              va="top", ha="left")
    fig.text(0.65, 0.90 - (len(legend_lines) + 1.5) * 0.021,
              "(points 6-8 coincide: all three\n6/24 events fall in UTC hour 22)",
              fontsize=7.5, style="italic", va="top", ha="left")

    fig.savefig(out_png, dpi=150)
    print(f"Saved {out_png}")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    bg = load_all()
    ev = load_events()
    print(ev[["n", "date", "label", "hour"]].to_string(index=False))

    scatter_with_events(bg, ev, "rms_damage", "Damage zone (DZ) RMS (strain rate, 1/s)",
                         "DZ RMS vs. bottom reference RMS -- 15 global events highlighted",
                         os.path.join(OUT_DIR, "dz_vs_ref_rms_events.png"), log_y=True)
    scatter_with_events(bg, ev, "rms_fault", "Fault zone (FZ) RMS (strain rate, 1/s)",
                         "FZ RMS vs. bottom reference RMS -- 15 global events highlighted",
                         os.path.join(OUT_DIR, "fz_vs_ref_rms_events.png"), log_y=True)
    scatter_with_events(bg, ev, "fz_dz_ratio", "FZ / DZ RMS ratio",
                         "FZ/DZ ratio vs. bottom reference RMS -- 15 global events highlighted",
                         os.path.join(OUT_DIR, "fz_dz_ratio_vs_ref_rms_events.png"), log_y=False)


if __name__ == "__main__":
    main()
