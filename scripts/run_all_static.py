#!/usr/bin/env python3
"""Regenerate all 13 Hole A depth RMS overlay PNGs with red (RMS-detect up),
blue (CWA, from peaks.txt cwa_flag when available), and orange (global M6.5+
quakes, IASP91-predicted P arrival) arrows."""
import subprocess
import sys

SCRATCH = "/private/tmp/claude-501/-Users-bai-Documents-github-phasenetdas/c19fbb43-acec-430d-bf8f-cc535c856579/scratchpad/agu_batch"
PLOTTER = f"{SCRATCH}/plot_agu_overlay.py"
OUTDIR = "/Users/bai/Documents/github/agu2026/usgs_events_holeA_depth_rms"

# date -> (cwa_utc_csv or None, [(globalq_utc_iso, label), ...])
DATES = {
    "20260607": (None, [("2026-06-07T23:41:55", "M7.8 Philippines")]),
    "20260608": (None, [("2026-06-08T00:59:27", "M6.5 Philippines")]),
    "20260616": (None, [("2026-06-16T03:33:10", "M6.7 Indonesia")]),
    "20260617": (None, [("2026-06-17T19:13:23", "M6.6 Mid-Atlantic Ridge")]),
    "20260619": (None, [("2026-06-19T07:00:16", "M6.6 Russia Kamchatka")]),
    "20260624": ("2026-06-24T21:29:30", [
        ("2026-06-24T22:21:33", "M7.2 Venezuela"),
        ("2026-06-24T22:22:06", "M7.5 Venezuela"),
        ("2026-06-24T22:35:22", "M6.9 Japan"),
    ]),
    "20260626": (None, [("2026-06-26T11:38:59", "M6.5 Philippines")]),
    "20260717": ("2026-07-17T20:11:30", [("2026-07-17T15:04:30", "M7.3 Mexico")]),
    "20260728": (None, [("2026-07-28T07:30:01", "M6.8 Japan Kumamoto")]),
    "20260810": ("2026-08-10T13:33:30,2026-08-10T17:58:20",
                 [("2026-08-10T12:51:26", "M7.4 Colombia")]),
    "20260814": (None, [("2026-08-14T22:04:51", "M7.8 Indonesia Ende")]),
    "20260815": ("2026-08-15T11:28:30", [("2026-08-15T11:00:47", "M6.9 Indonesia")]),
    "20260820": (None, [("2026-08-20T18:20:08", "M6.7 Peru")]),
}

for date, (cwa, gq) in DATES.items():
    csv = f"{SCRATCH}/{date}_depth_rms_mseed.csv"
    peaks = f"{SCRATCH}/{date}_peaks.txt"
    cmd = [sys.executable, PLOTTER, "--date", date, "--hole", "A",
           "--csv", csv, "--peaks-txt", peaks, "--outdir", SCRATCH, "--tz8"]
    if cwa:
        cmd += ["--cwa", cwa]
    cmd += ["--globalq", ",".join(t for t, _ in gq)]
    cmd += ["--globalq-label", ",".join(lbl for _, lbl in gq)]
    print(f"=== {date} ===")
    print(" ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("FAILED:", r.stderr[-2000:])
        continue
    src = f"{SCRATCH}/{date}_depth_rms_overlay.png"
    dst = f"{OUTDIR}/{date}_depth_rms_overlay_globalq.png"
    subprocess.run(["cp", src, dst], check=True)
    print(f"-> {dst}")

print("ALL DONE")
