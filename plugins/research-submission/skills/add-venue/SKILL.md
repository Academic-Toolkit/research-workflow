---
name: add-venue
description: Use when a journal or conference is NOT yet in the research-submission corpus and needs to be added, or when an existing record must be re-fetched because verify.py reported CHANGED. Triggers on "把 <期刊> 加進來", "add <venue> to the corpus", "這個期刊還沒收錄", "收錄 <conference>", "來源變了要更新". Fetches the venue's primary sources, asserts fetch validity, and writes a schema-valid YAML record with full provenance.
---

# add-venue

把一個新場次收進語料庫。**這個 skill 的產出會被別人當成權威來用**，所以寧可標「查過，沒有」也不要憑印象填。

## Step 1 — 找到一手來源（不要只找一頁）

投稿須知**通常散在多個頁面**。已知的分佈樣態：

| 場次類型 | 典型分佈 |
|---|---|
| 期刊 | 期刊首頁（metrics、範圍）+ submit 頁（規定本體）+ 外部標準頁（JARS/TOP） |
| 研討會 | 學會年會通則頁（不變的部分）+ 該年度頁（日期地點）+ Presenter Information 子頁（投稿規定）+ 投稿系統（Ex Ordo/EasyChair） |

**URL 不可推測。** 實測過的陷阱：APA 的 `/submission-guidelines` 是 404、真路徑 `/submit`；Psychometric Society 的 `/imps` 是 404、真路徑帶年份 `/imps-2026`。找不到就從首頁導覽點進去，把真實 URL 記下來。

## Step 2 — 預設用 safari-browser 讀頁面，再記進 `fetch.method`

**預設用 safari-browser 讀。** 出版社與學會網站多半擋機器人（Wiley、Elsevier/ScienceDirect、MDPI 對 curl 與 WebFetch 都回 403；APA 回 200 空殼），Safari 帶著使用者的一般瀏覽器環境，這些頁面在 Safari 裡都讀得到。看不到頁面是工具的限制，不是期刊的問題，**不要因此換掉候選期刊或改憑記憶填**。

先載入 `safari-browser` skill，照它的 tab-locking 規則：

- 用 `--url <子字串>` 鎖分頁（多視窗時可用 `--window` 加 `--tab-in-window`）；重用鎖定旗標時存成 bash 陣列，不要存成字串。
- `open` 會開在最前面的視窗，只開自己需要的頁；用完**只關自己開的分頁**，不要碰使用者或其他代理開的分頁。多個代理同時操作時，每次動作前先用頁面內容（期刊名、ISSN）確認抓到的是自己的頁。
- 讀頁面文字用 `document.body.innerText`。

仍要測一次 curl，不是為了取得內容，是為了回答「這個來源別人能不能自動重抓」，並記進 `fetch.method` / `http_viable`（`verify.py` 靠這個決定能不能自動比對）：

```bash
curl -sS -L --max-time 15 -w '\n%{http_code}|%{size_download}' "<url>" | tail -1
```

判讀：

- 正常大小、狀態 200 → `http_viable: true`。內容仍可用 Safari 讀；`method` 記 `http`
- **200 但只有幾百 bytes** → **bot 挑戰頁**（APA 的 Incapsula 即如此）。`method: browser`（或 `webfetch`，視實際用哪種讀到），`http_viable: false`，並把失敗樣態寫進 `http_failure_mode`
- 403 → 同上，`method: browser`，`http_viable: false`
- 多個不同 URL 回**相同大小/hash** → 決定性證據，全部是同一個挑戰頁

`method: browser` 的來源 `verify.py` 無法自動重抓，會回 `NEEDS_AGENT`；這是預期結果，不是故障。重新驗證時請用 Safari 打開被引用的頁面，確認原文仍在並記下確認日期。

### 收錄／指標：Clarivate Master Journal List

要確認期刊是否收錄在 SSCI、SCIE 時，以 Clarivate Master Journal List（mjl.clarivate.com）為準，不要憑記憶，也不要用出版社自己的收錄清單當證據（實測 IJCS 的出版社頁列有 AHCI，MJL 卻只有 SSCI）。MJL 是 JS 頁面，結果頁網址不帶查詢字串、`?issn=` 會被導回首頁，所以只能在頁內操作：從 `/home` 在 `#search-box` 填 ISSN，按 `#search-button`，讀結果列的 Web of Science Core Collection 欄。SCIE、SSCI、ESCI 要分開記；只有 ESCI 不算 SCIE 或 SSCI。

## Step 3 — 設定 `fetch.validity`（**不可省略**）

```yaml
validity:
  must_contain: "<該頁獨有、規定改版也不會消失的字串>"
  min_extracted_chars: <保守下限>
```

**兩個條件缺一不可。** 實測：psychometricsociety.org 的 404 頁面有 28 KB，比某些真實頁面還大——單靠長度擋不住。而缺少斷言時，freshness 檢查會把空殼當內容存下，且空殼 hash 穩定不變，於是**永遠回報「沒變動」而實際上什麼都沒監看**。

`must_contain` 選字原則：挑內容性的字（如場地名、規定用語），不要挑導覽列或頁尾——那些在錯誤頁上也會出現。

## Step 4 — 填記錄

從既有樣本複製起手最快：

```bash
ls ${CLAUDE_PLUGIN_ROOT}/venues/*/          # apa/psychological-methods.yaml（期刊）
                                            # psychometric-society/imps.yaml（研討會）
```

### 指標用標準欄位名（比較表由腳本讀這些欄位產生）

`identity.metrics` 請用 `impact_factor`、`quartiles`、`acceptance_rate`、`time_to_first_decision`、`time_submission_to_acceptance`，形狀見 `venue-report` skill 的「記錄的標準欄位」。**分區（Q）要記系統**：JCR 與 SJR 是不同的統計量，不混用。官方只公布拒絕率時，`acceptance_rate` 寫 not_published，另放 `rejection_rate`。

### 官方沒有公布審稿速度時：自行抽樣估計（只當估計，不當官方事實）

官方未公布「投稿到接受」時，先寫 `not_published`（官方欄位照舊，不動）。若該刊的**文章頁標有 Received／Accepted／Published 日期**，可以用 `scripts/sample_review_times.py` 抽樣估計，結果放在 `identity.metrics.estimates`，**與官方欄位分開**：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sample_review_times.py --issn <ISSN> --journal-path <期刊路徑> \
    --preset frontiers --year <刊出年> --n 200 --out result.json
```

腳本以 Crossref 隨機抽樣該刊某年刊出的文章，逐篇讀文章頁日期，輸出投稿到接受的中位數、四分位、10–90 百分位與樣本數。記錄格式：

```yaml
estimates:
  sub_to_acceptance: {statistic: median, value: ..., unit: days, q1: ..., q3: ..., p10: ..., p90: ...,
                      method: "...", n: ..., sample_year: ..., queried: ..., caveats: [...]}
```

**一定要寫進 `caveats` 的限制**：
1. 只含最後被刊出的稿件，**看不到被拒稿**，不能回答「被拒要花多久」。
2. 樣本是「某年刊出」的文章，不是「某年投稿」的稿件。
3. Received 是否等於首次投稿日，要看該刊的說明；沒說明就記為假設。
4. 抽樣有隨機誤差；n 小時（例：8 篇得到 80 天，198 篇得到 108.5 天）差很多，至少抽 100 篇以上。

**已驗證的 preset（2026-10-13）**：`frontiers`、`plos`（curl 讀文章頁）、`europepmc`（PMC 開放全文 XML；只涵蓋 PMC 收錄者，且可能有相當比例讀不到日期——Behavioral Sciences 200 篇中 78 篇失敗，失敗率高時可靠度下降，必須寫進 caveats）、`mdpi-safari`（mdpi.com 擋 curl，改用 safari-browser 開專用視窗，每篇隨機延遲，結束時只關自己開的視窗）。其他出版社先用 `--n 5` 試跑，`n_parsed` 要等於 `n_sampled` 才放大。

**用有官方數字的刊校準**：方法本身要先驗證。PLOS ONE 官方公布 2023 上半年投稿到接受中位數 188 天；同一方法抽該期間刊出的 190 篇得 188.5 天，相差半天。新增一個 preset 時，盡量找一本有官方數字的同出版社期刊做同樣的校準；沒有校準對象就在 caveats 寫「未校準」。**估計不得與官方統計互比**（口徑不同：官方的中位數有自己的母體與起訖點），也不得放進官方欄位。

### 三條填寫紀律

1. **查過但官網沒有 → 寫 `{status: not_published, checked: <date>}`**，不要留空。留空會讓後人以為是漏抓，於是重複去查一次不存在的東西。
   - `not_published` 官方未公布 ／ `not_found` 找不到 ／ `not_applicable` 不適用
2. **`requirements`（慢）與 `cycle`（快）分開放。** 期刊多為 `cycle.applies_to: null`；研討會反過來——requirements 薄、cycle 厚。放錯格會導致「須知是對的但截稿日是去年」。
3. **`extracted_sha256` 留 `null`**，交給 `verify.py` 建基準。不要手算——hash 必須由同一個 extractor 產生才可比。

## Step 5 — 驗證（兩支都要跑）

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py    # schema + 5 條 lint
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify.py <venue-id>   # 建 hash 基準
```

`validate.py` 的錯誤代碼：

| 代碼 | 意義 |
|---|---|
| L1 | `last_verified_at` 早於 `fetched_at` |
| L2 | 跨 source 的 hash 相同 → **抓取故障**，不是巧合 |
| L3 | `http_viable: false` 卻宣告 `method: http` |
| L4 | authoritative 來源缺 `fetch.validity` |
| W1 | 研討會 cycle 已過期（警告，非錯誤——辦完了是合法狀態） |
| W2 | 快照超過一年未驗證 |

**錯誤要修到零；警告要讀懂再決定。**

## Step 6 — 更新既有記錄（`verify.py` 回報 CHANGED 時）

1. 重新擷取該來源
2. **人工覆核差異**——找出哪些欄位真的變了。不要整份覆蓋，那會弄丟先前查證過的 `not_published` 標記
3. 更新變動欄位 + `fetched_at`
4. 重跑 `verify.py` 建新基準

改版通常只動少數欄位。整份重寫比逐欄比對更容易出錯，也丟掉累積的查證成果。
