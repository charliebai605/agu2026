#!/usr/bin/env python3
"""plot_event_globe.py
One spherical (orthographic) globe map per USGS M6.5+ event (15 total), via
obspy.core.event.catalog.Catalog.plot()
(https://docs.obspy.org/packages/autogen/obspy.core.event.catalog.Catalog.plot.html).
Each globe auto-centers on that single event (ortho projection centers on
the mean lat/lon of whatever's in the Catalog -- with one event that's just
the event itself). MiDAS Hole A is marked with a red star where it falls on
the visible hemisphere; for events >90 deg from Hole A the station is on the
far side of the globe and won't appear -- that's geometrically real, not a
bug (it's exactly the same 6 events flagged in the earlier near/far-side
version: Peru, Colombia, Mexico, the two Venezuela events, Mid-Atlantic
Ridge).

Usage: python3 plot_event_globe.py
Output: agu2026/globe_map/{date}_{mag}_{place_slug}.png  (15 files)
"""
import os
import re

import cartopy.crs as ccrs
import pandas as pd
from obspy import UTCDateTime
from obspy.core.event import Catalog, Event, Magnitude, Origin

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG_CSV = os.path.join(HERE, "..", "usgs_catalog_M6.5plus_202606-202608.csv")
OUT_DIR = os.path.join(HERE, "..", "globe_map")

# MiDAS Hole A (station used for the depth-RMS overlay / IASP91 predictions)
HOLE_A_LAT, HOLE_A_LON = 24.02304, 121.63015


def slugify(text, maxlen=30):
    s = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return s[:maxlen]


def build_catalog(row):
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
    cat = Catalog(events=[event])
    return cat


def plot_event(row, out_png):
    cat = build_catalog(row)
    date_str = row["time"][:10]
    title = f"{date_str}  M{row['mag']} {row['place']}"
    fig = cat.plot(
        projection="ortho",
        resolution="l",
        label=None,
        color="depth",
        method="cartopy",
        title=title,
        show=False,
    )
    ax = fig.axes[0]
    ax.plot(HOLE_A_LON, HOLE_A_LAT, marker="*", markersize=18, color="red",
            markeredgecolor="black", markeredgewidth=0.8,
            transform=ccrs.PlateCarree(), zorder=10)
    ax.text(HOLE_A_LON, HOLE_A_LAT - 8, "Hole A", fontsize=8,
            color="red", ha="center", va="top", fontweight="bold",
            transform=ccrs.PlateCarree(), zorder=10)
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    print(f"Saved {out_png}")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    df = pd.read_csv(CATALOG_CSV).sort_values("time").reset_index(drop=True)
    print(f"{len(df)} events")
    for _, row in df.iterrows():
        date_str = row["time"][:10].replace("-", "")
        fname = f"{date_str}_M{row['mag']}_{slugify(row['place'])}.png"
        plot_event(row, os.path.join(OUT_DIR, fname))


if __name__ == "__main__":
    main()
