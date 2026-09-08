#!/usr/bin/env python3
"""plot_zone_vs_ref_scatter.py
Three scatter plots (one PNG each), pooling every valid hour across the 13
AGU event days:
  X = bottom reference-segment average RMS (the depth_rms_tdms/mseed ref.csv
      value -- the black diamond on the daily report's zone RMS right axis)
  Y = damage zone (DZ) RMS / fault zone (FZ) RMS / FZ-DZ ratio, one plot each

Usage: python3 plot_zone_vs_ref_scatter.py
Output: agu2026/zone_vs_ref_scatter/{dz,fz,fz_dz_ratio}_vs_ref_rms.png
"""
import os

import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "_data")
OUT_DIR = os.path.join(HERE, "..", "zone_vs_ref_scatter")

DATES = ["20260607", "20260608", "20260616", "20260617", "20260619",
          "20260624", "20260626", "20260717", "20260728", "20260810",
          "20260814", "20260815", "20260820"]


def load_all():
    rows = []
    for d in DATES:
        ref_path = os.path.join(DATA_DIR, f"{d}_depth_rms_mseed_ref.csv")
        zone_path = os.path.join(DATA_DIR, f"{d}_zone_rms_mseed_0p1-1p0Hz.csv")
        if not (os.path.exists(ref_path) and os.path.exists(zone_path)):
            print(f"{d}: missing ref/zone csv, skipping")
            continue
        ref = pd.read_csv(ref_path)
        zone = pd.read_csv(zone_path)
        m = ref.merge(zone, on="hour", how="inner")
        m["date"] = d
        rows.append(m)
    df = pd.concat(rows, ignore_index=True)
    df = df.dropna(subset=["ref_rms", "rms_damage", "rms_fault"])
    df = df[(df["ref_rms"] > 0) & (df["rms_damage"] > 0) & (df["rms_fault"] > 0)]
    df["fz_dz_ratio"] = df["rms_fault"] / df["rms_damage"]
    return df


def scatter(df, ycol, ylabel, title, out_png, log_y=False, xlim_hi=None, ylim_hi=None):
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ax.scatter(df["ref_rms"], df[ycol], s=18, alpha=0.65,
               c="steelblue", edgecolor="black", linewidth=0.3)
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
    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    print(f"Saved {out_png}  (n={len(df)})")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    df = load_all()
    print(f"{len(df)} hourly points across {df['date'].nunique()} days")

    scatter(df, "rms_damage", "Damage zone (DZ) RMS (strain rate, 1/s)",
            "DZ RMS vs. bottom reference RMS",
            os.path.join(OUT_DIR, "dz_vs_ref_rms.png"), log_y=True,
            xlim_hi=1e-7, ylim_hi=1e-7)
    scatter(df, "rms_fault", "Fault zone (FZ) RMS (strain rate, 1/s)",
            "FZ RMS vs. bottom reference RMS",
            os.path.join(OUT_DIR, "fz_vs_ref_rms.png"), log_y=True,
            xlim_hi=1e-7, ylim_hi=1e-7)
    scatter(df, "fz_dz_ratio", "FZ / DZ RMS ratio",
            "FZ/DZ ratio vs. bottom reference RMS",
            os.path.join(OUT_DIR, "fz_dz_ratio_vs_ref_rms.png"), log_y=False,
            xlim_hi=1e-7)


if __name__ == "__main__":
    main()
