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

## 接下來建議的執行順序（已過時，全部完成，見下方最新進度）

1. ~~先做 Task 3...~~ 已完成。
2. ~~決定 Task 1 的新 repo...~~ 已完成後又推翻（互動版整個拿掉，見下方）。
3. ~~Task 2 等 1、2 都確定後才能真的動手重跑...~~ 已完成後又推翻。

## 進度更新（2026-09-09）：RMS depth overlay 改 log 軸、production 修 bug、AGU 新增大量分析圖表

使用者要求把 daily report 的 RMS depth overlay X 軸改成「軸間距是 log，但標籤數字是實際值」
（不是 log10 轉換後的數字），並要求擴及互動版跟**全站已發布的 253 天歷史報告**。過程中
發現並修好兩個 production bug，之後又在 `agu2026` 裡新增了一系列分析用圖表。這節記錄
目前狀態，方便之後接手或回頭查。

### 1. RMS depth overlay log 軸改動（production，已完成且已全站重繪）

- **`daily_report/plot_depth_rms_overlay.py`**（靜態圖）跟 **`daily_report/daily_blog.py` 的
  `_depth_overlay_plotly()`**（互動圖）都已經改成：畫的是 `normalized RMS` 實際值，X 軸用
  `ax.set_xscale("log")`（靜態圖）／`layout.xaxis.type="log"`（互動圖 Plotly），不再是
  `log10(normalized RMS)` 數字畫在線性軸上。兩者數學上完全等價（線形狀不變），只差在
  軸標籤怎麼顯示。已部署到 server 並跟本地 diff 確認一致。
- **全站 253 天已發布的歷史報告全部重繪過**（2024 回溯 152 天：`midas-daily-202401`~
  `202405`；2026 現役 101 天：`midas-daily-2026h1`/`h2`）。做法是寫了一支一次性腳本
  （`mass_regen_depth_overlay.py`，跑完已從 server 刪除），對每一天：
  1. 從該天現有的 `index.html` 裡**擷取原本就算好、嵌入的 CWA 資料**（不重新即時抓 CWA
     官網，因為官網只留最近~3週資料，事後抓歷史日期會抓空，這是先前在 AGU 13 天工作
     時就踩過的坑，這次特別避開）。
  2. 只重新呼叫 `plot_depth_rms_overlay.py` 重繪 PNG（用該天已存在的 CSV，不重算資料）。
  3. **手術式**置換該天 `index.html` 裡 `initDepthPlot('depthA'/'depthB', ...)` 這段
     embedded JSON（用字串定位+括號配對精準抓取要替換的範圍），完全不碰 RMS 時序圖、
     summary、peaks.txt、waterfall 等其他內容。
  4. 每個 repo 處理完所有天數後才一次 commit+push（不是每天各自 push）。
  - 過程中曾經觸發過一次太多平行 SSH 連線被拒絕（跟先前 6 個日期平行運算時一樣的問題），
    改序列後正常。

### 2. 修好的兩個 production bug

- **Bug A**：上面那次「全站重繪」**不知道有 13 個 AGU 事件日額外加的橘色 IASP91 箭頭**
  （跟部分日子的藍色 CWA 箭頭，因為那些是用 `agu2026/globalq_iasp91_arrivals.csv` 手動
  查證的資料，不在任何 HTML 裡能重新擷取），重繪時把這些箭頭洗掉了。**已修好**：寫了
  `fix_agu_globalq_regression.py`（跑完已刪除），從 `globalq_iasp91_arrivals.csv` 重新
  組出 `--globalq`/`--globalq-label`/`--cwa` 參數，對這 13 天重繪＋推送。已驗證
  20260607、20260810 兩天線上圖片正確（橘色+藍色箭頭都在，log 軸也生效）。
- **Bug B**：畫 `zone_vs_ref_scatter` 系列圖表時發現 **20260717、20260728 這兩天的
  zone RMS 長條圖（DZ/FZ 柱子本身）還是沒校正過的 raw count**，比其他天大了快 9 個
  數量級。原因是先前只修了 zone RMS 右軸參考點（`ref.csv`）的單位，忘記把
  `zone_rms_mseed_0p1-1p0Hz.csv`（柱子本身的資料）也重新算一次。**已修好**：透過
  midas-datasrv 重新跑 `zone_rms_mseed.py` 算出正確單位的資料、重繪 `zone_rms.png`、
  推送到 `midas-daily-2026h2`。

### 3. `agu2026` 這次新增的檔案／資料夾

- **`globalq_iasp91_arrivals.csv`**：15 個事件的權威資料（date_utc, usgs_id, mag, place,
  origin_time_utc, p_arrival_iasp91_utc, label, cwa_arrival_utc）。之後任何跟這 15 個
  事件時間有關的圖表都應該讀這份，不要重新用 obspy 算或去翻各腳本裡各自謄的 dict。
- **`event_origin_arrival_summary.csv`**：上面那份的簡化版，只留 origin_time_utc, place,
  magnitude, p_arrival_iasp91_utc 四欄。
- **`globe_map/`**：15 張球形正射投影地圖（`obspy.core.event.catalog.Catalog.plot()`，
  `projection="ortho"`），**一個事件一張圖**（不是先前做過的近側/遠側兩張合併版，那個
  已經被取代）。MiDAS Hole A 用橘色三角形標示（原本是紅色星星，使用者要求改色）。
  6 個事件（委內瑞拉×2、哥倫比亞、墨西哥、秘魯、中大西洋洋脊）離 Hole A 超過 90°，
  該事件自己那張圖裡 Hole A 會落在地球背面看不到，這是幾何上正確、不是 bug。
  腳本：`scripts/plot_event_globe.py`。
- **`usgs_M6.5plus_magnitude_timeline.png`**：X=事件時間、Y=規模的柱狀圖，15 根柱子都
  標上規模+地點文字（斜體旋轉 30°、上下錯開避免重疊，6/24 那天 3 個事件還是會有一點
  點碰在一起，資料太密無法完全避開）。腳本：`scripts/plot_magnitude_timeline.py`。
- **`depth_rms_overlay_holeA/`**：13 個事件日目前（log 軸+三色箭頭）的 Hole A depth RMS
  overlay PNG，直接從 production 網站抓下來的最終版本。
- **`zone_rms_daily/`**：13 個事件日的斷層帶（DZ/FZ）zone RMS 長條圖，一樣是從
  production 抓的。另外有兩張特殊版本：
  - `20260820_zone_rms.png` **已經覆蓋成去掉 UTC+8 03:00 那個小時**的版本（原始資料在
    那個小時整個異常，DZ/FZ/ref 三個數字完全相同且大 8 個數量級，明顯是壞資料，這個
    去除**只改了 agu2026 這份複本，沒有動 production**）。
  - `20260717_zone_rms_excl0400.png` 是**新增**的版本（原本的 `20260717_zone_rms.png`
    保留沒動），去掉 UTC+8 04:00 那個小時（對應一筆 CWA 有感地震，使用者要看不含這次
    地震尖峰的背景趨勢）。
- **`zone_vs_ref_scatter/`**：6 張散佈圖，X 軸都是「Bottom reference-segment average
  RMS」（`depth_rms` ref.csv 的值，也就是 daily report zone RMS 圖右軸的黑色菱形）：
  - `{dz,fz,fz_dz_ratio}_vs_ref_rms.png`：13 天 × 24 小時、312 個點全部混在一起（無事件
    標註），DZ/FZ 兩張 X/Y 軸都切到 `1e-7`，ratio 那張只切 X 軸（Y 軸維持 1.0-1.4 線性）。
  - `{dz,fz,fz_dz_ratio}_vs_ref_rms_events.png`：疊加 15 個事件對應到的 IASP91 預估抵達
    時間所在的那個整點小時，編號 1-15（依時間排序），每個事件用不同顏色（`tab20` 色盤），
    編號文字顏色跟點的顏色一致，右側有文字圖例列出「編號：日期＋事件」。**注意：因為
    zone RMS 資料是整點（小時）解析度，15 個事件裡有 3 個（6/24 的 M7.2/M7.5 委內瑞拉
    +M6.9 日本）全部落在 UTC 22 這個小時，所以圖上只有 13 個不重複的點，不是 15 個**
    （使用者原本以為只有 2 個委內瑞拉事件相鄰 30 秒會重疊，後來查證後發現日本那個事件
    雖然晚 13 分鐘，但一樣落在同一個 UTC 整點小時內）。
  - 腳本：`scripts/plot_zone_vs_ref_scatter.py`（無事件版）、
    `scripts/plot_zone_vs_ref_scatter_events.py`（事件版，import 前者的 `load_all()`/
    `DATES`）。兩支都讀 `scripts/_data/` 裡的 `{date}_depth_rms_mseed_ref.csv` +
    `{date}_zone_rms_mseed_0p1-1p0Hz.csv`（這次連同 Bug B 修正後的資料一起補齊、永久
    存放在這裡，13 天都有）。

### 4. 互動版（Plotly 三色箭頭）已經整個拿掉，改連結到完整報告

**這是這次 session 較早的決定，寫在這裡是因為上面第 2 節提到的「production 全站重繪」
發生在這個決定之後，避免之後看文件誤以為互動版還存在。** `agu-global-event` repo 的
13 個獨立互動頁面已刪除（Plotly 的雙軸模擬箭頭視覺上對不齊，使用者反映後決定拿掉），
現在 `agu-global-event/index.html` 每個日期直接連到 `midas-daily-2026h1`/`h2` 上對應的
完整每日報告。`midas-daily`（入口頁）跟每個半年 repo 自己的首頁也都加了連回
`agu-global-event` 的連結（改在 `daily_blog.py` 的 `_rebuild_landing_index()`/
`_rebuild_root_index()`，共用 production 檔案，已部署）。

### 5. 待確認/下次可能要做的事

- `zone_rms_daily/20260717_zone_rms_excl0400.png` 只存在 agu2026 這份複本，
  **production 網站上的 0717 zone RMS 圖仍然含那個 CWA 小時**，沒有被要求要同步修改。
- `20260820_zone_rms.png` 去掉異常小時也只改了 agu2026 複本，**production 網站上的
  0820 zone RMS 圖仍然含那個異常小時的壞資料**（使用者當時被告知這件事，選擇不處理
  production 端）。如果之後要用 production 網站的圖做正式發表，記得這個落差還沒補。
- `agu2026/abstract.md`、`figures/`、根目錄那份 PDF 從頭到尾都是使用者自己在維護、
  故意沒有 commit 進 git 的內容，每次 push 都特別避開，不要不小心加進去。

## 進度更新（2026-09-26）：hourly_scatter_interactive 新增颱風/地震標籤、可調整長寬比，已部署到樹莓派

`hourly_scatter_interactive/index.html`（2026-09-08 那幾節做的 tab 切換 + log/linear +
日期複選 + Play 動畫版本）這次一口氣加了幾組功能，全部只改這一個檔案（`data.json` 沒動）：

- **颱風警報日**：右側新增面板，資料來自 CWA 颱風資料庫的 `get_warning_typhoon` API
  （`rdc28.cwa.gov.tw/TDB/public/warning_typhoon_list/get_warning_typhoon`，POST
  `year=2026` 查到剛好 4 個對台發布警報的颱風：巴威 202609、紅霞 202612、白海豚 202613、
  沙德爾 202618）。勾選後對應日期的點變紅色並疊到最上層（用獨立 trace，後畫的蓋在上面）；
  有個「警報期間前後各加一天」的開關，切換要不要用擴增後的日期範圍。
- **AGU 15 個遠震事件標籤**：讀 `event_origin_arrival_summary.csv`，用 P 波抵達 MiDAS 的
  UTC 小時對應到 `data.json` 的 `(date, hour)` 格點（15 筆全部對得上，沒有缺漏）。橘色
  星形 + 圖上直接顯示「地點 M規模」文字（不只 hover，annotation 直接畫在圖上）。6/24 那
  小時剛好 3 個事件（委內瑞拉×2 + 日本能代）落在同一格，合併成一個星形、多行標籤。右側
  清單可以逐一勾選要顯示哪些事件的星星；另外有個獨立的「在圖上顯示地點/規模文字」主開關
  ——**這個開關只影響文字標籤，星星永遠都畫**，星星顯示與否是清單裡各別事件的勾選狀態
  決定的（使用者一開始以為兩個是綁在一起的，特別確認過要拆開）。
- **其他地震標籤（原本叫「台灣本地地震標籤」，使用者後來要求改名）**：找 `ref` 值大於
  1.381e-9（Colombia M7.4 那個點）、但不在 15 個遠震名單裡的小時點，共 8 個候選。CWA
  自己的地震查詢頁（`scweb.cwa.gov.tw/zh-tw/earthquake/data` 的 `ajaxhandler` POST 端點）
  被 WAF 擋掉，直接回 `Request Rejected`（200 狀態碼但是假頁面，換 cookie/headers 都沒用，
  判斷是 bot 特徵擋，不是缺參數）。改走兩條路：
  1. 先用 USGS 全球地震目錄（`earthquake.usgs.gov/fdsnws/event/1/query`）比對台灣周邊
     ±1~3 小時窗，8 個候選裡對到 6 個。
  2. 使用者提醒「我們自己就有抓 CWA 的方式」——`daily_report/daily_blog.py` 的
     `fetch_cwa_quakes()` 用的是 `www.cwa.gov.tw/V8/C/E/MOD/EQ_ROW.html`（不同網域，
     production 每天穩定在用，不會被擋，但只回溯約 2 週）+ 已經發布在樹莓派上的
     `midas-daily-2026q3` 歷史報告頁面（產生當下就即時抓過 CWA、嵌進 Plotly trace 的
     `customdata` 裡）。用這兩個來源把其中 3 筆（0730、0822、0913）換成官方規模 + CWA
     詳細頁連結（`https://www.cwa.gov.tw/V8/C/E/EQ/EQ...html`），地點文字從「Taiwan」改
     成震央所在（或最近參考）縣市（臺東、宜蘭、花蓮）。點圖上的星星會開新分頁連到 CWA
     詳細頁（`Plotly.on("plotly_click", ...)`，只在 `customdata` 是 `http` 開頭字串時才
     觸發，避免跟其他 trace 的 hover 文字 customdata 衝突）。0607、0726 這兩筆 CWA 兩邊
     （即時列表 + 已發布報告）都查不到記錄（**真的沒收錄，不是被擋**），維持用 USGS
     資料；0703 那筆其實是日本近海（先島群島）M6.1，不是台灣氣象局轄區，本來就不會有
     CWA 記錄。
- **四個側邊清單（選擇天數、颱風警報日、AGU 遠震、其他地震）全部改成可摺疊**
  （`<details>/<summary>`），且各自有獨立的 scroll 區域限制高度。這裡踩過一個坑：一開始
  直接把 `display:flex`/`max-height` 加在 `<details>` 本身上，日期清單（112 天）展開時
  會溢出、蓋到後面的面板，因為 `<details>` 非 summary 內容在現代瀏覽器是透過內部包裝
  渲染，author CSS 不保證作用到那層。修法是在 `<details>` 裡面再包一層普通的
  `<div class="panel-body">` 承擔 `flex`/`max-height`/`overflow`（連同一開始漏掉的
  `.scroll-area { min-height: 0 }`，這是 flexbox 讓內部元素真的能縮小產生捲軸的必要條件），
  不受 `<details>` 特殊渲染影響。
- **圖表可自由調整長寬比**：拿掉原本固定的 `aspect-ratio: 16/9`，改成右下角一個手動畫的
  拖拉把手（CSS 漸層畫的斜線圖示 + `mousedown`/`mousemove`/`mouseup` 手動實作，沒有用
  原生 CSS `resize`，因為那個在 Safari 上常常畫不出來/不明顯），配合 `ResizeObserver`
  盯著 `#chart` 元素、尺寸一變就呼叫 `Plotly.Plots.resize()`。
- **hover 時間換算成 UTC+8**：底層 `data.json` 的 `(date, hour)` 是 UTC（跟
  `plot_hourly_scatter_combined.py` 的 colorbar 換算邏輯一致，只是那邊只換算 colorbar
  刻度文字，資料本身仍是 UTC）。hover 文字跟事件清單顯示層另外用 `toLocalDateHour()`
  換算成台灣時間，但「選擇天數」的日期分組跟颱風日期比對邏輯仍然用原始 UTC 日曆日分桶，
  沒有跟著換算成本地日期——這是刻意的取捨，只有顯示層换算，避免動到既有的天數篩選邏輯。

**已部署（一次性手動 rsync，不是自動化）**：整個 `hourly_scatter_interactive/` 資料夾
（`index.html` + `data.json`）rsync 到樹莓派
`charlie@192.168.201.197:/srv/www/agu2026/hourly_scatter_interactive/`，可從
`http://192.168.201.197/agu2026/hourly_scatter_interactive/` 存取——這台樹莓派跟
`phasenetdas/daily_report/pi_web.md` 記錄的 `midas-daily` 系列是同一台，但 `agu2026/`
是這次新加的路徑，之前沒有這個資料夾。**跟 `daily_blog.py` 每天自動 `_publish_rsync()`
不一樣，這裡沒有自動化流程**，之後這個頁面如果再改，要記得手動重新 rsync 一次。原本
GitHub Pages 版本 `charliebai605.github.io/agu2026/hourly_scatter_interactive/` 還在線上
沒有動，push 這次的 commit 上去之後會自動更新（跟 `midas-daily` 不同，`agu2026` 這個
repo 沒有遷移離開 GitHub Pages）；樹莓派這份是「額外多加一個存取點」，不是取代它。

**未完成/使用者中途放棄的事**：使用者一度想加「strain rate 積分成 strain、再積分成
加速度」的另一個版本，討論方向（微分 vs 積分該往哪走、log-log 座標乘常數不改變形狀）
後使用者說「算了沒事」，沒有實作。如果之後又提起，先確認清楚要哪一種轉換
（乘 dt 得到 strain，還是要真的對 RMS 序列做數值微分/積分——後者形狀會變、可能要
改成 linear 軸或處理正負號），不要照字面「積分成加速度」直接做（那個方向物理上是
微分，不是積分，這次已經跟使用者說明過）。
