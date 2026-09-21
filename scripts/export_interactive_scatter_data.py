#!/usr/bin/env python3
"""export_interactive_scatter_data.py
Load all clean days (June-August 58 days + September 1-20, 78 total, see
bottom_rms_baseline_investigation.md section 8 for how June-August was fixed) via
plot_hourly_scatter_combined.load_day(), and dump to a single JSON file consumed by
the interactive Plotly page (hourly_scatter_interactive/index.html).

Usage: python3 export_interactive_scatter_data.py --dates 20260607,...,20260920 --out ../hourly_scatter_interactive/data.json
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_hourly_scatter_combined import load_day  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dates", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    dates_in = [d.strip() for d in args.dates.split(",")]
    records = []
    bad = []
    dates_with_data = []
    for d in dates_in:
        try:
            df = load_day(d)
        except Exception as e:
            bad.append((d, str(e)))
            continue
        n_before = len(records)
        for _, row in df.iterrows():
            vals = (row["ref_rms"], row["rms_damage"], row["rms_fault"], row["fz_dz_ratio"])
            if any(v != v or v <= 0 for v in vals):  # NaN or non-positive (log axes need >0)
                continue
            records.append({
                "date": d,
                "hour": int(row["hour"]),
                "ref": row["ref_rms"],
                "dz": row["rms_damage"],
                "fz": row["rms_fault"],
                "ratio": row["fz_dz_ratio"],
            })
        if len(records) > n_before:
            dates_with_data.append(d)
        else:
            print(f"  {d}: 0 valid hours, dropped from date list (source data all-NaN)", file=sys.stderr)

    if bad:
        print("FAILED to load:", bad, file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump({"dates": dates_with_data, "records": records}, f)
    print(f"Saved {args.out}: {len(dates_with_data)}/{len(dates_in)} dates, {len(records)} hourly points")


if __name__ == "__main__":
    main()
