#!/usr/bin/env python3
"""plot_agu_overlay_interactive.py

Interactive (Plotly) version of the Hole A depth-RMS overlay, matching the
static plot_agu_overlay.py's three-color arrow scheme:
  red    = RMS-detect "up" events (from peaks.txt)
  blue   = CWA felt earthquakes (approximate time, see global_event_task_status.md)
  orange = global M6.5+ earthquakes, IASP91-predicted P arrival

Reuses daily_blog._depth_overlay_plotly() for the base 24-hour wiggle traces
(already UTC+8-labeled), then adds a secondary time-axis (yaxis2, overlaid,
right side) with one marker-trace per color, using "triangle-left" markers
as arrow-style pointers into the timeline -- same visual role as the static
plot's ax_time panel, without needing a second subplot.

Usage: see run_all_interactive.py for the per-date driver.
"""
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, "/Users/bai/Documents/github/phasenetdas/daily_report")
import daily_blog as B

TZ8 = timedelta(hours=8)


def _midas_daily_url(date_str):
    """Full daily-report URL for a YYYYMMDD date, matching daily_blog.py's
    repo routing (H1=01-06, H2=07-12; only 2026 dates expected here)."""
    y, m, d = date_str[:4], date_str[4:6], date_str[6:]
    half = "h1" if int(m) <= 6 else "h2"
    return f"https://charliebai605.github.io/midas-daily-{y}{half}/{y}/{m}/{date_str}/"


def _read_up_events_utc8(peaks_txt):
    """Return list of pd.Timestamp-free datetime (naive, UTC+8) for label=='up'
    rows in a peaks.txt file."""
    out = []
    if not peaks_txt or not os.path.exists(peaks_txt):
        return out
    started = False
    for line in open(peaks_txt, encoding="utf-8"):
        if line.startswith("---"):
            started = True
            continue
        if not started:
            continue
        parts = line.split()
        if len(parts) >= 5 and parts[0].isdigit() and parts[4] == "up":
            ts = datetime.strptime(parts[1] + " " + parts[2], "%Y-%m-%d %H:%M:%S")
            out.append(ts)
    return out


def build_page(date_str, csv_path, peaks_txt, cwa_utc_iso, globalq):
    """globalq: list of (utc_iso_str, label). cwa_utc_iso: list of utc_iso_str
    or []. Returns full HTML string for one date's interactive page."""
    traces, layout = B._depth_overlay_plotly(csv_path, "A")
    if traces is None:
        raise RuntimeError(f"no depth RMS data for {date_str}")

    date_obj = datetime.strptime(date_str, "%Y%m%d")
    t0 = date_obj + TZ8            # window top: 08:00 UTC+8
    t1 = t0 + timedelta(hours=24)  # window bottom: next-day 08:00 UTC+8

    xlim_hi = layout.get("xaxis", {}).get("range", [None, 0.8])[1] or 0.8
    arrow_x = xlim_hi * 0.94 if xlim_hi else 0.75

    def _iso8(dt_utc8):
        return dt_utc8.strftime("%Y-%m-%dT%H:%M:%S")

    # red: RMS-detect "up" events (peaks.txt already stores UTC+8 wall time)
    up_times = _read_up_events_utc8(peaks_txt)
    red_y = [_iso8(t) for t in up_times]

    # blue: CWA (given as UTC ISO strings -> convert to UTC+8 wall time)
    blue_y = [_iso8(datetime.fromisoformat(t) + TZ8) for t in cwa_utc_iso]

    # orange: global quakes (given as UTC ISO strings -> convert to UTC+8)
    orange_y = [_iso8(datetime.fromisoformat(t) + TZ8) for t, _ in globalq]
    orange_labels = [lbl for _, lbl in globalq]

    def _arrow_trace(y_vals, color, name, hover_labels=None):
        return {
            "type": "scatter", "mode": "markers",
            "x": [arrow_x] * len(y_vals), "y": y_vals,
            "xaxis": "x", "yaxis": "y2",
            "marker": {"symbol": "triangle-left", "size": 13, "color": color,
                       "line": {"width": 1, "color": "black"}},
            "name": name,
            "text": hover_labels if hover_labels else None,
            "hovertemplate": (("%{text}<br>" if hover_labels else "") +
                               "%{y}<extra></extra>"),
            "showlegend": len(y_vals) > 0,
        }

    layout["xaxis"]["range"] = [layout["xaxis"].get("range", [-0.2, 0.8])[0] or -0.2,
                                 xlim_hi]
    layout["yaxis2"] = {
        "overlaying": "y", "side": "right", "anchor": "x",
        "type": "date", "range": [t1.strftime("%Y-%m-%dT%H:%M:%S"),
                                   t0.strftime("%Y-%m-%dT%H:%M:%S")],
        "title": "Time (UTC+8)", "showgrid": False, "automargin": True,
    }
    layout["margin"]["r"] = 60

    all_traces = list(traces)
    all_traces.append(_arrow_trace(red_y, "red", f"RMS-detect up ({len(red_y)})"))
    all_traces.append(_arrow_trace(blue_y, "dodgerblue", f"CWA felt ({len(blue_y)})"))
    all_traces.append(_arrow_trace(orange_y, "orange",
                                    f"Global M6.5+ IASP91 P pred. ({len(orange_y)})",
                                    hover_labels=orange_labels))

    date_fmt = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    title = f"Hole A depth RMS overlay — {date_fmt} (UTC+8)"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
 body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:0;padding:1rem;background:#fafafa;color:#222;}}
 h1{{font-size:1.2rem;}}
 #plot{{width:100%;max-width:900px;height:800px;margin:0 auto;}}
 a.back{{font-size:.9rem;margin-right:1rem;}}
</style>
</head>
<body>
<a class="back" href="../index.html">&larr; all dates</a>
<a class="back" href="{_midas_daily_url(date_str)}">完整每日報告 (midas-daily) →</a>
<h1>{title}</h1>
<div id="plot"></div>
<script>
Plotly.newPlot('plot', {json.dumps(all_traces, ensure_ascii=False)},
  {json.dumps(layout, ensure_ascii=False)}, {{responsive: true}});
</script>
</body>
</html>
"""
    return html
