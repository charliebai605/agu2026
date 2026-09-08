#!/usr/bin/env python3
"""plot_magnitude_timeline.py
Bar chart: X axis = event origin time (UTC), Y axis = magnitude, one bar per
USGS M6.5+ event (15 total, from usgs_catalog_M6.5plus_202606-202608.csv).

Usage: python3 plot_magnitude_timeline.py
Output: agu2026/usgs_M6.5plus_magnitude_timeline.png
"""
import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG_CSV = os.path.join(HERE, "..", "usgs_catalog_M6.5plus_202606-202608.csv")
OUT_PNG = os.path.join(HERE, "..", "usgs_M6.5plus_magnitude_timeline.png")


def main():
    df = pd.read_csv(CATALOG_CSV)
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(11, 5))
    colors = plt.cm.viridis((df["mag"] - df["mag"].min()) /
                            (df["mag"].max() - df["mag"].min() + 1e-9))
    bars = ax.bar(df["time"], df["mag"], width=1.2, color=colors,
                   edgecolor="black", linewidth=0.6)

    for x, m, place in zip(df["time"], df["mag"], df["place"]):
        ax.text(x, m + 0.05, f"M{m}", ha="center", va="bottom", fontsize=8)

    ax.set_ylim(6.0, 8.2)
    ax.set_ylabel("Magnitude", fontsize=11)
    ax.set_xlabel("Origin time (UTC)", fontsize=11)
    ax.set_title(f"USGS M6.5+ events, 2026-06~08 ({len(df)} events)",
                 fontsize=12, fontweight="bold")
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    ax.grid(axis="y", lw=0.4, alpha=0.5, zorder=0)
    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150)
    print(f"Saved {OUT_PNG}")


if __name__ == "__main__":
    main()
