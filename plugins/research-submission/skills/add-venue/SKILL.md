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

### 比較表會讀的其他欄位（標準形狀）

比較表由 `scripts/venue_table.py` 從記錄產生。下面是它讀的標準寫法；照這個寫，表上才不會出現「?」（「?」的意思是腳本認不得記錄的形狀，不是官方未公布）。

| 欄 | 標準寫法 |
|---|---|
| 收錄 | `identity.indexing.web_of_science: {scie, ssci, esci, as_of, src}`，三個旗標各寫 `true` 或 `false`（布林，不要寫成字串）。表上只顯示 SCIE 與 SSCI；`esci` 照實記錄，但不顯示。寫了 `web_of_science` 就由它決定這一格，舊的收錄鍵不再讀 |
| APC | `requirements.fees.apc: {amount, currency, mandatory}`，`mandatory` 寫 `true` 或 `false`。多幣別定價寫 `currency_rates: [{currency, value}, ...]`（表上取第一筆 USD）；分級定價寫 `list_price_usd: {<級別>: <金額>}`（表上取最高的一級）。`list_price_usd` 只放價格級別，每個值都會被當成一級的價格；年份、來源、附註寫在 `apc` 的其他鍵（例如 `as_of`、`src`、`note`）。必付或選付請明寫 `mandatory`。沒寫時腳本依序看：`status`（`mandatory…` 是必付、`optional` 是選付）、`identity.open_access` 有值（必付；只對直接寫 `amount`、或寫在 `all_other_articles`、`a_type` 的記錄，用 `currency_rates` 或 `list_price_usd` 寫的不看這一項）、`applies_when`（選付）；都沒有就印「?」。`identity.open_access` 寫 `hybrid` 的期刊因此一定要明寫 `mandatory: false`。金額沒公布時寫 `amount: {status: not_published, checked}`，表上印「未公布」；依同樣順序判斷但不看 `identity.open_access`，結果是選付才加「（選付）」 |
| 篇幅 | `requirements.length: {value, unit}`，`unit` 用 `words`、`pages_double_spaced` 或 `pages_typeset`。官方沒寫上限時寫 `requirements.length_limit: {status: not_published, checked}`（schema 規定 `requirements.length` 一定要有 `value` 與 `unit`，所以「沒有上限的資訊」另放這個鍵） |
| 審稿 | `requirements.review.type`，值用 `single_blind`、`single_anonymized`、`double_blind`、`double_anonymized`。官方沒寫時寫 `{status: not_published, checked}` |
| 出版社 | `identity.publisher` 寫字串；官方沒寫時寫 `{status: not_published, checked}` |

期刊記錄的任何一欄查過而沒有值，都寫 `{status: not_published|not_found|not_applicable, checked}`，不要留空，也不要自創別的形狀（篇幅是例外，寫在 `requirements.length_limit`，見上表）。`status` 三個值的意思不同：`not_published` 是官方沒公布，`not_found` 是查過但沒取得（例如要登入），`not_applicable` 是這一欄對這個場地不適用。表上目前只有出版社、收錄、IF、APC、審稿這五欄會照 `status` 印出對應的字；分區、接受率、審稿時間、篇幅四欄還不會區分（例如分區一律印「未取得」），記錄仍照實寫。

**研討會（`kind: conference`）**：

- 收錄、IF、分區、首次決定、投稿到接受這五欄**省略不寫**，表上會印「不適用」。不要替這五欄寫 `status`：分區與審稿時間欄目前不會照 `status` 印出對應的字。
- 審稿型態各軌不同時，寫 `requirements.review.model_by_track: {research: ..., ...}`，表上取 `research`；只有一種時寫 `requirements.review.type`。
- APC 沒有預設值，要明寫：有金額就照上表寫 `requirements.fees.apc`；官方沒公布就寫 `requirements.fees.apc: {status: not_published, checked}`。只寫報名費而沒寫 `apc`，表上會印「?」。

### 聯絡信箱：有公務信箱時只記公務信箱

記錄裡的聯絡信箱分兩種。**公務信箱**屬於 venue 的一個職務或窗口，換人之後由接任者收信：編輯部、期刊行政、會議的聯絡信箱。**個人信箱**屬於某一個人自己，例如主編的學校信箱。

- 判斷**看信箱屬於誰，不看網域**。學會用免費信箱開的年會聯絡信箱是公務信箱。某個人自己的信箱，**即使官網把它列為聯絡方式**，仍然是個人信箱。
- 官網有公務信箱時，只記公務信箱。主編、編輯、主席只記姓名與職稱，不記他們自己的信箱：人會換，信箱跟著過期。
- 個人信箱只在兩個條件都成立時才記：官網沒有公務信箱，而且官網寫明投稿的事要寄到那個信箱。記的時候附上來源（`src`）。
- 公務信箱**不寫在具名人物底下**。承辦人的姓名可以留在人物那一欄，信箱移到不屬於任何人物的欄位。該用哪個鍵還沒有標準寫法（#21），先沿用語料庫裡已有的寫法之一。
- **備註與警告**的文字裡不寫出個人信箱；要提到時指向來源頁。
- `validate.py` 只看位置：`identity`、`requirements.submission`、`cycle` 底下，有字串 `name` 的 mapping 一律被當成具名人物（`identity` 本身除外），它底下的信箱都算個人信箱。它分不出人與機構，所以**機構的信箱**也不要寫在有 `name` 的 mapping 裡。

`validate.py` 的 W3 在同一筆記錄同時有個人信箱與公務信箱時警告。它不看 `warnings` 與 `requirements` 的其他部分；把個人信箱寫進編輯部欄位，它也看不出來。

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

1. **查過但官網沒有 → 寫 `{status: not_published, checked: <date>}`**，不要留空。留空會讓後人以為是漏抓，於是重複去查一次不存在的東西。例外有兩個：研討會記錄的收錄、IF、分區、首次決定、投稿到接受這五欄省略不寫；篇幅沒有上限的資訊時寫在 `requirements.length_limit`（兩者見上方「比較表會讀的其他欄位」）。
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
| W3 | 同一筆記錄同時有個人信箱與公務信箱（見 Step 4「聯絡信箱」）。訊息只列欄位路徑 |

**錯誤要修到零；警告要讀懂再決定。**

## Step 6 — 更新既有記錄（`verify.py` 回報 CHANGED 時）

1. 重新擷取該來源
2. **人工覆核差異**——找出哪些欄位真的變了。不要整份覆蓋，那會弄丟先前查證過的 `not_published` 標記
3. 更新變動欄位 + `fetched_at`
4. 重跑 `verify.py` 建新基準

改版通常只動少數欄位。整份重寫比逐欄比對更容易出錯，也丟掉累積的查證成果。
