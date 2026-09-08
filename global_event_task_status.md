# AGU global-event Hole A depth RMS overlay — 任務狀態

**這份文件的目的**：記錄目前為止做過什麼、方法細節、跟接下來 3 個待辦，避免對話 compact 後細節遺失。

## 背景

USGS catalog（15 筆 M6.5+ 全球地震，2026-06 ~ 2026-08）存在
`agu2026/usgs_catalog_M6.5plus_202606-202608.csv`。這些事件落在 13 個不重複 UTC 日期
（2026-06-07/08/16/17/19/24/26、07-17/28、08-10/14/15/20），2026-06-24 一天有 3 筆事件
（2 個委內瑞拉 doublet + 1 個日本）。

已經做完的：把這 13 天的 **Hole A depth RMS overlay 靜態 PNG** 重新畫過，加上橘色箭頭標示
「用 IASP91 model 算出來的全球地震 P 波預估抵達時間」，疊在原本就有的紅色（RMS-detect up 事件）
跟藍色（CWA 有感地震）箭頭上面。存在 `agu2026/usgs_events_holeA_depth_rms/{date}_depth_rms_overlay_globalq.png`
（13 張，舊版不帶 globalq 的已經刪除）。

## 方法細節（給之後接手/回頭檢查用）

- **測站座標**：Hole A = 24.02304°N, 121.63015°E（來源：`phasenetdas/待處理點子.md`）
- **IASP91 計算**：`obspy.taup.TauPyModel(model="iasp91")` + `obspy.geodetics.locations2degrees`，
  `get_travel_times(source_depth_in_km=<事件深度>, distance_in_degree=<測站-震央距離>, phase_list=["P","Pdiff","PKP","PKIKP"])`，
  取回傳第一筆 arrival（依距離自動落在對的 phase：<100° 用 P，100-140°附近用 Pdiff，>~145°可能是 PKP/PKIKP）。
  預估抵達時間 = 事件 origin time + travel time。15 個事件全部驗證過，預估抵達都落在同一個 UTC 日期
  （沒有跨日的邊界情況要處理）。
- **15 個事件的 IASP91 預估抵達時間+CWA 時間，正式記錄在
  `agu2026/globalq_iasp91_arrivals.csv`**（欄位：`date_utc, usgs_id, mag, place,
  origin_time_utc, p_arrival_iasp91_utc, label, cwa_arrival_utc`；`cwa_arrival_utc`
  多筆時用 `;` 分隔，如 20260810）。這份是權威資料來源，之後要重跑/重繪/引用都直接讀這個
  檔案，不用重新用 obspy 算一次或去翻 `run_all_static.py`／`run_all_interactive.py`
  裡各自謄一份的 DATES dict（那兩個 dict 內容應該要跟這個 CSV 一致，如果之後改了其中一邊
  記得同步）。
- **CWA 藍色箭頭**：CWA 官網「近期」有感地震列表只回溯到約 2026-08-19，更早的日期查不到。
  對這 13 天，是從 `{date}_peaks.txt` 裡 `cwa_flag=1` 那欄反推近似時間（找到 flag=1 的那組
  RMS peak 时间戳记，取中點，UTC+8 轉回 UTC）。**20260607/08/16/19/626/728/814/820 這幾天
  沒有找到任何 flag=1 的列**（可能是規模太小/太遠沒被 STA/LTA 抓到），CSV 裡這些列的
  `cwa_arrival_utc` 留空，不是遺漏，是真的沒有可靠時間資料。
- **繪圖腳本**：`--globalq`／`--globalq-label` 參數（跟既有 `--cwa` 一樣接受精確 ISO
  時間戳記，逗號分隔）**已經正式加進 production 的 `daily_report/plot_depth_rms_overlay.py`**
  （2026-09-08，之前只在 `agu2026/scripts/plot_agu_overlay.py` 複本裡，這次確認產生 production
  daily report 也需要橘色箭頭後，補進本體並部署到 server）。這 13 天的
  `midas-daily-2026h1`/`h2` 上的 `depth_rms_overlay.png` 已經用這個 CSV 的資料重繪過，
  橘色箭頭+圖例已經在線上。
- **驅動腳本**：`agu2026/scripts/run_all_static.py`，需要本地已有這 13 天的
  `{date}_depth_rms_mseed.csv` + `{date}_peaks.txt`（原本是從 192.168.202.121 的
  `/data2/baidama_work/realtime_rms/` scp 下來，暫存在session-specific scratchpad，
  **這次 session 結束後那份 scratchpad 會消失**，重跑前要重新 scp 一份，或修改腳本改成
  直接從 server 讀）。

## 進度更新（2026-09-08）

- **Task 3 已完成**：`daily_blog.py` 的 `_depth_overlay_plotly()` 已改成 legend/hover 顯示
  UTC+8（trace name 從 `h{h:02d}` 改成 `h{(h+8)%24:02d}`，legend title 改成 `Hour (UTC+8)`，
  顏色配置不變，因為 `+8` 只是常數位移，viridis 漸層順序不受影響）。已本地測試驗證
  （h=0 UTC → 顯示 "h08"，h=16 UTC → 顯示 "h00"），已部署到 server 並 diff 確認一致。
- **Task 1+2 已完成**：使用者確認要把三色箭頭也加進互動版（不是只做 UTC+8）。
  - 新增 `agu2026/scripts/plot_agu_overlay_interactive.py`：重用
    `daily_blog._depth_overlay_plotly()` 產生的 24 條 UTC+8 wiggle trace，
    另外疊加一個 `yaxis2`（overlaying，右側，type=date，範圍 08:00→隔天08:00 UTC+8，
    時間增加方向朝下，跟靜態圖一致），用三條 `triangle-left` marker scatter trace
    （紅/藍/橘）畫在 `yaxis2` 上模擬「箭頭指向時間軸」的視覺效果，取代 matplotlib
    版原本用的 `ax.annotate` 真箭頭（Plotly 沒有等價的簡單雙軸+annotate 組合，這個
    marker 方案是判斷過後的簡化實作，效果上一致：hover 可看到規模+地點）。
  - 新增 `agu2026/scripts/run_all_interactive.py`：13 天的 driver，日期→CWA/globalq
    對照表跟 `run_all_static.py` 相同資料重新謄一份（格式稍微不同：CWA 改成 list 而不是
    逗號字串，因為互動版要能一次畫多個 CWA 箭頭）。
  - **新 GitHub repo**：`https://github.com/charliebai605/agu-global-event`（public，
    已開 GitHub Pages，legacy build，`source=main:/`）。本地 checkout 在
    `/Users/bai/Documents/github/agu-global-event/`，跟 `agu2026`／`phasenetdas` 都是
    各自獨立的 git repo。內容：13 個日期資料夾 + 根目錄 `index.html`（列出全部 13 天的
    連結）。已 push、已驗證建置成功。
  - **資料相依性**：`run_all_interactive.py` 需要的 13 天 `_depth_rms_mseed.csv` +
    `_peaks.txt` 現在存在 `agu2026/scripts/_data/`（從 session scratchpad 複製過來，
    這次是**永久保存**了，不是暫存路徑，之後要重跑不用再重新 scp）。

## 進度更新（2026-09-08 第二輪）：13 天完整每日報告補齊

使用者要求「補上目前 pipeline 中所有的圖」，確認做法是連結到既有的完整每日報告
（`midas-daily-2026h1`/`h2`），但發現這 13 天裡有 9 天的報告內容用的是舊版 pipeline
（缺 Hole B 深度剖面、zone RMS FZ/DZ 面板、up-only histogram）：

- **7 個 6 月事件日**（0607/0608/0616/0617/0619/0624/0626）：完全沒有 Hole B、zone RMS、
  up-only histogram（這些功能是 7/12 之後才加入 pipeline，6 月時還不存在）。
- **2 個 7 月事件日**（0717/0728）：已有 Hole B/zone RMS 面板，但 zone RMS 右軸的深部
  參考值（`_depth_rms_mseed_ref.csv`）是 7/30 DAS_SENSITIVITY 校正之前算的，單位是
  raw count 不是 strain rate（差 ~7e8 倍）。
- **4 個 8 月事件日**（0810/0814/0815/0820）：已經是當時最新版 pipeline 產出，不需改動。

**關鍵技術問題與解法**：
- 這 13 天的原始 1000Hz TDMS 檔案早已從 rolling buffer 清掉（`realtime_tdms/` 沒有任何
  檔案），無法用現在的 `depth_rms_tdms.py`/`zone_rms_daily.py` 本地 TDMS 路線重算。改用
  `depth_rms_mseed.py`/`zone_rms_mseed.py`（MiniSEED via midas-datasrv CephFS archive）
  ——8/23 那次 Ceph 權限問題（見 `midas_datsrv_ceph_incident_20260823.md`）目前已恢復
  正常（`df` 可以正常讀取 archive），確認可用。
- **重大風險（已避開）**：`classify_noise_from_tdms()`（up/down/noise 的 f-k 分類）
  也需要原始 TDMS，對這些歷史日期一樣拿不到，會靜默回傳 `[False]*N`（不是字串
  `'noise'`，是 Python bool），導致 up-only histogram 空白、且第一次嘗試已經把
  20260607 的 `peaks.txt` 覆蓋成全部 label=False 的壞檔（即時分類結果被清空且無法復原，
  因為原始 TDMS 波形已不存在，事後無法重新分類）。**發現後立刻從 session 稍早備份
  （`agu2026/scripts/_data/*_peaks.txt`，AGU 工作一開始就 scp 下來的原始版本）復原**，
  之後 9 個日期的重跑都改成：RMS 數值/時間戳記重新算（純用已存在的 `_energy.csv`，
  不需要 TDMS），但 fk_label 分類直接沿用備份檔案裡當年即時運算的結果（用 median
  ratio 對到 1/DAS_SENSITIVITY 驗證兩邊事件數與對應順序完全一致才採用）。
- 一次性腳本 `regen_historical_day.py`（未提交進 repo，跑完後已從 server 清除）：讀
  `_energy.csv` 重算 RMS 時序/histogram、呼叫現版 `plot_depth_rms_overlay.py`/
  `zone_rms_daily.py` 重繪 PNG、呼叫 `daily_blog.build_and_publish(..., do_push=True)`
  重建整頁並推送到既有的 `midas-daily-2026h1`/`h2` repo——**刻意不呼叫 `send_email()`**，
  不會觸發補寄信件。
- 平行跑 6 個日期的 midas-datasrv 運算時觸發過一次 SSH 連線被重置（太多平行 proxy-jump
  連線），2 個日期失敗，改成序列重跑後成功；之後全部改序列執行。

**結果**：13 個事件日的完整每日報告現在都已對齊當前 pipeline（Hole A/B 深度剖面、
zone RMS FZ/DZ 面板含正確單位的深部參考值、up-only histogram 全部到位），peaks.txt
的 up 事件數量與內容跟原始版本逐一核對一致（例如 20260607：15 個 up 事件，改前改後
相同），AGU 圖表（`agu2026/usgs_events_holeA_depth_rms/`、`agu-global-event`）用的紅色
箭頭事件數不受影響、不需要重繪。

## 進度更新（2026-09-08 第三輪）：拿掉互動版三色箭頭頁、橘色箭頭補進 production

- **`agu-global-event` 的 13 個互動版 Plotly 頁面已經刪除**：使用者反映箭頭標記位置對不齊
  （Plotly 沒有真正的雙軸+annotate 機制，用 `yaxis2` + `triangle-left` marker 模擬箭頭的
  做法視覺上會飄，跟旁邊的深度剖面線對不上）。改成 `agu-global-event/index.html` 每個日期
  直接連到 `midas-daily-2026h1`/`h2` 上對應的完整每日報告，不再維護自己的一份深度剖面圖。
  下面第 117 行開始「使用者這次的新需求」段落裡描述的 Task 1（開 repo 放互動版）已被這次
  決定取代，那段記錄留著只是歷史脈絡，不代表現在的架構。
- **橘色箭頭（IASP91 預估抵達）正式加進 production 的 `daily_report/plot_depth_rms_overlay.py`**
  （`--globalq`/`--globalq-label` 參數），因為現在使用者是直接看 `midas-daily` 上的完整報告，
  所以這 13 天 `midas-daily-2026h1`/`h2` 上的 Hole A `depth_rms_overlay.png` 都已經用
  `globalq_iasp91_arrivals.csv` 的資料重繪，橘色箭頭+圖例（「→ Global M6.5+ (IASP91 P
  pred., UTC+8): ...」）已經在線上，跟原本就有的紅色（RMS-detect up）、藍色（CWA）疊在
  同一張圖。已下載 20260607、20260624 兩天的線上圖片實際核對過。

## 使用者這次的新需求（3 件，全部已完成，見上方「進度更新」，Task 1 已被第三輪取代）

1. **在 GitHub 上開一個新 repo**，名稱暫定 `agu-global-event`（GitHub repo 名稱不能有空格，
   使用者說的「AGU global event」直接照講會是這個轉寫），用來放這批 global-event 資料。
   使用者給的截圖是**互動版 Plotly 深度剖面圖**（`daily_blog.py` 的 `_depth_overlay_plotly()`
   產生的那種，右側圖例是 `Hour (UTC)` 下拉式的 h00-h23），不是靜態 PNG——代表這個新 repo
   應該是要放**互動版**（可能是 GitHub Pages 網站，比照 `midas-daily-*` 那套架構），不是
   只塞 PNG 檔。**還沒決定**：這個 repo 要不要用 `gh repo create` 建、要不要開 GitHub Pages、
   要用什麼樣的 HTML 外殼（可以參考 `daily_report/daily_blog.py` 的 `_DAY_TMPL`）。
2. **這 13 天的資料全部重跑**——目前解讀是：不只重畫靜態 PNG（已經做過了），還要**重新產生
   互動版 HTML**（含橘色/紅色/藍色三色標記），因為新 repo 要放的是互動版。
3. **互動版深度剖面圖的「Hour」選項，要從 UTC 改成 UTC+8**——對應
   `daily_report/daily_blog.py` 的 `_depth_overlay_plotly()` 函式（約在檔案 1030-1090 行附近，
   搜尋 `def _depth_overlay_plotly`），目前 `for h in range(min(24, norm_rms.shape[1]))`，
   trace name 寫死 `f"h{h:02d}"`（h00-h23，UTC）。要改成顯示 UTC+8：h 對應到的實際 UTC+8
   小時 = `(h + 8) % 24`，圖例文字要顯示轉換後的小時（例如原本 h00 UTC → 顯示 h08，
   或者直接顯示 08:00 這種格式），還要注意**排序**：CSV 欄位 h00-h23 仍然是照 UTC 儲存
   （這是 `depth_rms_tdms.py` 產生的，不會因為這個純顯示層的改動而變動），只有畫圖時的
   label／排序需要換算成 UTC+8。**這是 `daily_blog.py` 的改動，是雙方（跟 peer session）
   共用的 production 檔案**，改完要照 `daily_report/scripts_overview.md` 記錄的維運注意事項，
   確認部署前後跟 server 上版本 diff 一致，避免蓋掉對方的修改（可參考這次 session 稍早做
   repo 拆分時的部署流程）。**這個改動只影響顯示，不影響任何既有計算邏輯或 production 資料**，
   但因為是共用檔案，部署前還是要走一次 diff 確認的流程。

## 接下來建議的執行順序

1. 先做 Task 3（`daily_blog.py` 的 UTC+8 顯示改動）——範圍最小、最明確，做完在本地測試
   `_depth_overlay_plotly()` 輸出正確後才部署到 server。
2. 決定 Task 1 的新 repo 要不要開 Pages、HTML 外殼怎麼設計（可以直接問使用者，或參考
   `_DAY_TMPL` 簡化一個版本）。
3. Task 2 等 1、2 都確定後才能真的動手重跑（需要先有新版 `_depth_overlay_plotly()` 邏輯
   + 新 repo 存在）。
