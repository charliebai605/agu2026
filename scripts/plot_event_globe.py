#!/usr/bin/env python3
"""plot_event_globe.py
Spherical (orthographic) globe map of the 15 USGS M6.5+ events used in the
Hole A depth-RMS overlay analysis, via obspy.core.event.catalog.Catalog.plot()
(https://docs.obspy.org/packages/autogen/obspy.core.event.catalog.Catalog.plot.html).
Hole A's location (the MiDAS station) is marked with a red star for reference.

A single ortho globe only shows the near-side hemisphere -- 6 of the 15
events (Peru, Colombia, Mexico, the two Venezuela events, Mid-Atlantic Ridge)
are >90 deg from Hole A and would be hidden on the far side. So this makes
TWO globes: near-side (auto-centered on the near-side events' mean, which
ends up close to Hole A) and far-side (auto-centered on the far-side events'
mean), so all 15 events are visible somewhere.

Usage: python3 plot_event_globe.py
Output: agu2026/globe_map/usgs_M6.5plus_globe_nearside.png
        agu2026/globe_map/usgs_M6.5plus_globe_farside.png
"""
import os

import cartopy.crs as ccrs
import numpy as np
import pandas as pd
from obspy import UTCDateTime
from obspy.core.event import Catalog, Event, Magnitude, Origin

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG_CSV = os.path.join(HERE, "..", "usgs_catalog_M6.5plus_202606-202608.csv")
OUT_DIR = os.path.join(HERE, "..", "globe_map")

# MiDAS Hole A (station used for the depth-RMS overlay / IASP91 predictions)
HOLE_A_LAT, HOLE_A_LON = 24.02304, 121.63015


def great_circle_deg(lat0, lon0, lat, lon):
    lat0r, lon0r = np.radians(lat0), np.radians(lon0)
    latr, lonr = np.radians(lat), np.radians(lon)
    cosval = (np.sin(lat0r) * np.sin(latr) +
              np.cos(lat0r) * np.cos(latr) * np.cos(lonr - lon0r))
    return np.degrees(np.arccos(np.clip(cosval, -1, 1)))


def build_catalog(df):
    cat = Catalog()
    for _, row in df.iterrows():
        origin = Origin(
            time=UTCDateTime(row["time"]),
            latitude=row["latitude"],
            longitude=row["longitude"],
            depth=row["depth"] * 1000.0,  # USGS csv is km; QuakeML Origin.depth is meters
        )
        magnitude = Magnitude(mag=row["mag"], magnitude_type=row["magType"])
        event = Event(
            origins=[origin],
            magnitudes=[magnitude],
            event_descriptions=[{"text": row["place"]}],
        )
        cat.append(event)
    return cat


def plot_side(df_side, title, out_png, mark_hole_a):
    cat = build_catalog(df_side)
    fig = cat.plot(
        projection="ortho",
        resolution="l",
        label=None,
        color="date",
        method="cartopy",
        title=f"{title} ({len(cat)} events)",
        show=False,
    )
    if mark_hole_a:
        ax = fig.axes[0]
        ax.plot(HOLE_A_LON, HOLE_A_LAT, marker="*", markersize=18, color="red",
                markeredgecolor="black", markeredgewidth=0.8,
                transform=ccrs.PlateCarree(), zorder=10)
        ax.text(HOLE_A_LON, HOLE_A_LAT - 8, "Hole A\n(Hualien)", fontsize=8,
                color="red", ha="center", va="top", fontweight="bold",
                transform=ccrs.PlateCarree(), zorder=10)
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    print(f"Saved {out_png}  ({len(cat)} events)")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    df = pd.read_csv(CATALOG_CSV)
    dist = great_circle_deg(HOLE_A_LAT, HOLE_A_LON, df["latitude"], df["longitude"])
    near = df[dist <= 90].reset_index(drop=True)
    far = df[dist > 90].reset_index(drop=True)
    print(f"{len(near)} near-side (<=90 deg), {len(far)} far-side (>90 deg) events")

    plot_side(near, "USGS M6.5+ events, 2026-06~08 -- near-side hemisphere\n"
                     "vs. MiDAS Hole A (Hualien, Taiwan)",
              os.path.join(OUT_DIR, "usgs_M6.5plus_globe_nearside.png"),
              mark_hole_a=True)
    plot_side(far, "USGS M6.5+ events, 2026-06~08 -- far-side hemisphere\n"
                    "(>90° from Hole A, antipodal region)",
              os.path.join(OUT_DIR, "usgs_M6.5plus_globe_farside.png"),
              mark_hole_a=False)


if __name__ == "__main__":
    main()
