#!/usr/bin/env python3
"""
plot_depth_rms_overlay.py
24 條 hourly wiggle trace 疊在同一張圖，viridis colormap 著色。
X 軸 = log₁₀(normalized RMS)，Y 軸 = 深度（向下，預設切掉地表前 25m）。
右側：viridis 小時色帶 + 外側小箭頭標出 up-going peaks（紅）與 CWA 事件（藍）。
用 --hole A（預設）或 --hole B 切換井別（深度範圍、normalize 段長、預設 CSV 都跟著換）。

Usage (on 202.121):
  python3 /data2/baidama_work/plot_depth_rms_overlay.py --date 20260607 \
    --cwa 11,17 --peaks-txt /data2/baidama_work/realtime_rms/20260607_peaks.txt --tz8
  python3 /data2/baidama_work/plot_depth_rms_overlay.py --date 20260706 --hole B
"""
import argparse, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D

RMS_DIR = "/data2/baidama_work/realtime_rms"
OUT_DIR = "/data2/baidama_work/realtime_rms"

# depth_max（正規化用最底段標示）＋ 預設 CSV 檔名，依井別而異
HOLE_CFG = {
    "A": dict(depth_bot=695.0, norm_label="100 m", default_csv_suffix="_depth_rms_mseed.csv"),
    "B": dict(depth_bot=497.0, norm_label="50 m",  default_csv_suffix="_depth_rms_tdms_holeB.csv"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYYMMDD")
    ap.add_argument("--hole", default="A", choices=sorted(HOLE_CFG),
                     help="井 A 或 B（預設 A）")
    ap.add_argument("--csv", default=None,
                    help="CSV 路徑（預設依 --hole 決定，見 HOLE_CFG）")
    ap.add_argument("--outdir", default=OUT_DIR)
    ap.add_argument("--xlim-lo",   type=float, default=-0.2)
    ap.add_argument("--xlim-hi",   type=float, default=0.6)
    ap.add_argument("--depth-top", type=float, default=25.0,
                    help="切掉地表前 N 公尺（預設 25）")
    ap.add_argument("--cwa", default="",
                    help="CWA 事件精確 UTC 時間戳記，逗號分隔"
                         "（如 '2026-07-21T11:53:08,2026-07-21T19:31:21'；"
                         "也接受純小時 '11,17' 以相容舊呼叫方式，會畫在整點）")
    ap.add_argument("--noise", default="",
                    help="big-noise UTC 小時（保留相容，目前不特別上色）")
    ap.add_argument("--philippines", default="",
                    help="菲律賓地震 UTC 小時，逗號分隔")
    ap.add_argument("--philippines-label", default="")
    ap.add_argument("--globalq", default="",
                    help="全球大地震 IASP91 預估抵達時間，精確 UTC 時間戳記，逗號分隔"
                         "（如 '2026-06-24T22:21:33,2026-06-24T22:35:22'），橘色箭頭")
    ap.add_argument("--globalq-label", default="",
                    help="逗號分隔，跟 --globalq 一一對應，用於圖例/annotate（如規模+地點）")
    ap.add_argument("--peaks-txt", default="",
                    help="peaks.txt 路徑（用於右側 up-going 箭頭）")
    ap.add_argument("--tz8", action="store_true",
                    help="時間軸顯示 UTC+8（08:00 → 隔天 08:00）")
    ap.add_argument("--linear", action="store_true",
                    help="X 軸用 normalized RMS（不取 log10）")
    args = ap.parse_args()

    hole_cfg  = HOLE_CFG[args.hole]
    DEPTH_BOT = hole_cfg["depth_bot"]

    def _hrs(s):
        return {int(float(x)) for x in s.split(",") if x.strip() != ""}

    def _parse_cwa_tokens(s):
        """回傳 list，每個元素是 pd.Timestamp（精確 UTC 時間）或 int（純小時，舊格式相容）。"""
        out = []
        for x in s.split(","):
            x = x.strip()
            if not x:
                continue
            try:
                out.append(int(float(x)))          # 舊格式：純小時
            except ValueError:
                out.append(pd.Timestamp(x))        # 新格式：精確 ISO 時間戳記
        return out

    cwa_tokens = _parse_cwa_tokens(args.cwa)
    hl_phil = _hrs(args.philippines)
    phil_label = args.philippines_label or "Philippines"
    HOFF = 8 if args.tz8 else 0
    TZL  = "UTC+8" if args.tz8 else "UTC"
    date_obj = pd.Timestamp(args.date)

    def _cwa_event_time(tok):
        """CWA 事件要畫在 y 軸的絕對時間（已套用 HOFF 校正）。
        tok 為 int：舊格式純小時，畫在該小時整點；
        tok 為 pd.Timestamp：新格式精確 UTC 時間戳記，畫在精確分鐘位置。"""
        if isinstance(tok, int):
            return date_obj + pd.Timedelta(hours=tok + HOFF)
        return tok + pd.Timedelta(hours=HOFF)

    cwa_times = [_cwa_event_time(t) for t in cwa_tokens]

    globalq_times = [pd.Timestamp(t) + pd.Timedelta(hours=HOFF)
                      for t in args.globalq.split(",") if t.strip()]
    globalq_labels = [s.strip() for s in args.globalq_label.split(",") if s.strip()]

    csv = args.csv or os.path.join(RMS_DIR, f"{args.date}{hole_cfg['default_csv_suffix']}")
    if not os.path.exists(csv):
        raise FileNotFoundError(f"CSV not found: {csv}")

    raw      = np.genfromtxt(csv, delimiter=",", skip_header=1)
    depths   = raw[:, 1]
    norm_rms = raw[:, 2:]

    mask     = depths >= args.depth_top
    depths   = depths[mask]
    norm_rms = norm_rms[mask, :]

    cmap = plt.cm.viridis_r

    # ── Figure: narrow portrait, two panels ──────────────────────────────────
    fig = plt.figure(figsize=(5, 9))
    gs  = GridSpec(1, 2, width_ratios=[3.5, 1.1], wspace=0.04)
    ax      = fig.add_subplot(gs[0, 0])
    ax_time = fig.add_subplot(gs[0, 1])

    # ── Main wiggle: viridis for normal hours, bold color for event hours ─────
    for h in range(24):
        col   = norm_rms[:, h]
        valid = ~np.isnan(col)
        if not valid.any():
            continue
        if args.linear:
            log_val = np.where(valid, col, np.nan)
        else:
            log_val = np.where(valid, np.log10(np.maximum(col, 1e-3)), np.nan)
        if h in hl_phil:
            color, lw, alpha, z = "gold", 2.2, 1.0, 6
        else:
            color, lw, alpha, z = cmap(h / 23), 0.8, 0.75, 2
        ax.plot(log_val, depths, color=color, lw=lw, alpha=alpha, zorder=z)

    hl = []
    if cwa_times:
        cwa_labels = sorted(t.strftime("%H:%M") for t in cwa_times)
        hl.append(Line2D([0], [0], color="dodgerblue", lw=1.5,
                         label="→ CWA ({TZL}): ".format(TZL=TZL) +
                               ", ".join(cwa_labels)))
    for h in sorted(hl_phil):
        hl.append(Line2D([0], [0], color="gold", lw=2.2, label=phil_label))
    if globalq_times:
        gq_labels = globalq_labels if len(globalq_labels) == len(globalq_times) else \
            [t.strftime("%H:%M") for t in sorted(globalq_times)]
        hl.append(Line2D([0], [0], color="orange", lw=1.5,
                         label="→ Global M6.5+ (IASP91 P pred., " + TZL + "): " +
                               ", ".join(gq_labels)))
    if hl:
        ax.legend(handles=hl, loc="lower right", fontsize=7, framealpha=0.85)

    if not args.linear:
        ax.axvline(0, color="gray", lw=0.8, ls="--", zorder=0)
    ax.set_xlim(args.xlim_lo, args.xlim_hi)
    ax.set_ylim(DEPTH_BOT + 10, args.depth_top)
    ax.set_xlabel("normalized RMS" if args.linear else "log₁₀(normalized RMS)", fontsize=9)
    ax.set_ylabel(f"Depth in Hole {args.hole} (m)", fontsize=9)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(100))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(50))
    ax.grid(axis="y", lw=0.3, alpha=0.5)
    date_fmt = f"{args.date[:4]}-{args.date[4:6]}-{args.date[6:]}"
    ax.set_title(
        f"Hole {args.hole} — 24-hr Overlay  |  BP 0.1–1 Hz\n"
        f"Norm by bottom {hole_cfg['norm_label']}  |  {date_fmt} {TZL}",
        fontsize=9, fontweight="bold"
    )

    # ── Right panel: viridis hour bands + event arrows ────────────────────────
    t0 = date_obj + pd.Timedelta(hours=HOFF)    # window top
    t1 = t0 + pd.Timedelta(hours=24)            # window bottom

    ax_time.set_ylim(t1, t0)       # time increases downward
    ax_time.set_xlim(0, 1.5)       # x=[0,1] for bands, x=[1,1.5] for arrows
    ax_time.set_xticks([])

    # Viridis colored band per UTC hour
    band_xmax = 1.0 / 1.5          # axes fraction of x=1.0 within xlim=[0,1.5]
    for h in range(24):
        t_s = date_obj + pd.Timedelta(hours=h + HOFF)
        t_e = t_s + pd.Timedelta(hours=1)
        ax_time.axhspan(t_s, t_e, xmin=0, xmax=band_xmax,
                        color=cmap(h / 23), alpha=0.55, zorder=1)

    ax_time.yaxis.set_major_locator(mdates.HourLocator(interval=4))
    def _time_fmt(x, pos):
        dt = mdates.num2date(x)
        if dt.hour == 8 and dt.minute == 0:
            return f"08:00\n{dt.strftime('%m/%d')}"
        return dt.strftime("%H:%M")
    ax_time.yaxis.set_major_formatter(plt.FuncFormatter(_time_fmt))
    ax_time.yaxis.tick_right()
    ax_time.tick_params(axis="y", labelsize=7)
    ax_time.set_title("Time", fontsize=8)
    ax_time.grid(axis="y", lw=0.3, alpha=0.35, zorder=0)
    for sp in ["top", "bottom", "left"]:
        ax_time.spines[sp].set_visible(False)

    # Up-going peaks: red arrows pointing left into the band
    ptxt = args.peaks_txt or os.path.join(RMS_DIR, f"{args.date}_peaks.txt")
    if os.path.exists(ptxt):
        with open(ptxt) as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 5 and parts[0].isdigit() and parts[4] == "up":
                    ts = pd.Timestamp(parts[1] + " " + parts[2])
                    ax_time.annotate(
                        "", xy=(1.0, ts), xytext=(1.42, ts),
                        arrowprops=dict(arrowstyle="->", color="red",
                                        lw=1.2, mutation_scale=7),
                    )

    # CWA events: dodgerblue arrows
    for t_ev in sorted(cwa_times):
        ax_time.annotate(
            "", xy=(1.0, t_ev), xytext=(1.42, t_ev),
            arrowprops=dict(arrowstyle="->", color="dodgerblue",
                            lw=1.5, mutation_scale=9),
        )

    # Philippines events: goldenrod arrows
    for h in sorted(hl_phil):
        t_ev = date_obj + pd.Timedelta(hours=h + HOFF)
        ax_time.annotate(
            "", xy=(1.0, t_ev), xytext=(1.42, t_ev),
            arrowprops=dict(arrowstyle="->", color="goldenrod",
                            lw=1.5, mutation_scale=9),
        )

    # Global large earthquakes: orange arrows, at IASP91-predicted P arrival time
    for t_ev in sorted(globalq_times):
        ax_time.annotate(
            "", xy=(1.0, t_ev), xytext=(1.42, t_ev),
            arrowprops=dict(arrowstyle="->", color="orange",
                            lw=1.5, mutation_scale=9),
        )

    tag = "" if args.hole == "A" else f"_hole{args.hole}"   # keep Hole A filenames unchanged
    out_png = os.path.join(args.outdir, f"{args.date}_depth_rms_overlay{tag}.png")
    plt.tight_layout()
    plt.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved {out_png}")


if __name__ == "__main__":
    main()
