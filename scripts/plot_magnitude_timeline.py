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
LABELS_CSV = os.path.join(HERE, "..", "globalq_iasp91_arrivals.csv")
OUT_PNG = os.path.join(HERE, "..", "usgs_M6.5plus_magnitude_timeline.png")


def main():
    df = pd.read_csv(CATALOG_CSV)
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").reset_index(drop=True)

    # short place tag (e.g. "Venezuela", "Indonesia Ende") from the curated
    # label column, stripping the leading "M#.# " magnitude prefix
    labels = pd.read_csv(LABELS_CSV)[["usgs_id", "label"]]
    labels["place_tag"] = labels["label"].str.replace(r"^M[\d.]+\s+", "", regex=True)
    df = df.merge(labels, left_on="id", right_on="usgs_id", how="left")

    fig, ax = plt.subplots(figsize=(12, 5.5))
    colors = plt.cm.viridis((df["mag"] - df["mag"].min()) /
                            (df["mag"].max() - df["mag"].min() + 1e-9))
    bars = ax.bar(df["time"], df["mag"], width=1.2, color=colors,
                   edgecolor="black", linewidth=0.6)

    for i, (x, m, place_tag) in enumerate(zip(df["time"], df["mag"], df["place_tag"])):
        offset = 0.32 if i % 2 else 0.05  # stagger closely-spaced labels
        ax.text(x, m + offset, f"M{m}  {place_tag}", ha="left", va="bottom",
                 fontsize=8, rotation=30, rotation_mode="anchor")

    ax.set_ylim(6.0, 8.8)
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
