#!/usr/bin/env python3
"""Build the AGU global-event index: a single page linking each of the 13
UTC event days directly to its full daily report on midas-daily-2026h1/h2.

Superseded a per-day interactive Plotly overlay (red/blue/orange arrows
simulated via a secondary axis) -- the arrow markers didn't line up cleanly
against the wiggle traces (Plotly has no true twin-axis+annotate
equivalent), so per user request (2026-09-08) that page was dropped in
favor of linking straight to the real daily report, which already has the
Hole A/B depth overlay, zone RMS, RMS timeseries, and waterfalls.
"""
import os

OUT_REPO = "/Users/bai/Documents/github/agu-global-event"

# date -> one-line label for the index row (main global event(s) that day)
DATES = {
    "20260607": "M7.8 Philippines",
    "20260608": "M6.5 Philippines",
    "20260616": "M6.7 Indonesia",
    "20260617": "M6.6 Mid-Atlantic Ridge",
    "20260619": "M6.6 Russia Kamchatka",
    "20260624": "M7.2 + M7.5 Venezuela, M6.9 Japan",
    "20260626": "M6.5 Philippines",
    "20260717": "M7.3 Mexico",
    "20260728": "M6.8 Japan Kumamoto",
    "20260810": "M7.4 Colombia",
    "20260814": "M7.8 Indonesia Ende",
    "20260815": "M6.9 Indonesia",
    "20260820": "M6.7 Peru",
}


def midas_daily_url(date_str):
    """Full daily-report URL for a YYYYMMDD date, matching daily_blog.py's
    repo routing (H1=01-06, H2=07-12; only 2026 dates expected here)."""
    y, m, d = date_str[:4], date_str[4:6], date_str[6:]
    half = "h1" if int(m) <= 6 else "h2"
    return f"https://charliebai605.github.io/midas-daily-{y}{half}/{y}/{m}/{date_str}/"


def main():
    os.makedirs(OUT_REPO, exist_ok=True)
    dates_sorted = sorted(DATES)
    rows = "\n".join(
        f'<li><a href="{midas_daily_url(d)}">{d[:4]}-{d[4:6]}-{d[6:]}</a>'
        f' — {DATES[d]}</li>'
        for d in dates_sorted
    )
    root_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AGU 2026 -- Global M6.5+ events, Hole A depth RMS overlay</title>
<style>
 body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:0;padding:1.5rem;background:#fafafa;color:#222;}}
 ul{{line-height:2.2;font-size:1.1rem;}}
 a{{color:#0066cc;text-decoration:none;}} a:hover{{text-decoration:underline;}}
</style></head><body>
<h1>AGU 2026 -- Global M6.5+ events, Hole A depth RMS overlay</h1>
<p>The 13 UTC days containing the 15 USGS M6.5+ events in
<code>usgs_catalog_M6.5plus_202606-202608.csv</code>. Each link goes straight
to that day's full MiDAS daily report (Hole A/B depth RMS overlay, zone RMS,
RMS timeseries, waterfalls).</p>
<p><a href="https://charliebai605.github.io/midas-daily/">&larr; MiDAS Hole A 每日報告首頁</a></p>
<ul>
{rows}
</ul>
</body></html>
"""
    with open(os.path.join(OUT_REPO, "index.html"), "w") as f:
        f.write(root_html)
    print(f"wrote {OUT_REPO}/index.html")


if __name__ == "__main__":
    main()
