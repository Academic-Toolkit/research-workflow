---
name: update-venue
description: Use when a venue that is ALREADY in the research-submission corpus needs its record changed — a source page changed (verify.py reported CHANGED), the record lacks something a reader needs (a policy or guidance document it only names, a field never filled), a field misstates its source, sources need re-verifying, or yearly figures and a conference cycle need refreshing. Triggers on "更新 <期刊> 的記錄", "update the <venue> record", "這本的規定改了", "記錄少了…", "把這個補進記錄", "記錄寫錯了", "重新驗證 <venue>", "來源變了要更新", "IF 更新了", "下一屆的日期出來了". Edits only the fields the update concerns, keeps every verified not_published marker, changes dates only for sources actually re-read, and ends with validate.py, verify.py and a list of what was and was not re-read. Not for a venue the corpus does not have (add-venue), nor for reading rules or checking a manuscript (submit-to).
---

# update-venue

更新語料庫裡**已經有**的場次記錄。場次還沒收錄時用 `add-venue`。

更新比新增更容易安靜地出錯，而且錯了看不出來：

- 整份重寫，先前查證過的 `not_published` 標記跟著消失，後人又去查一次不存在的東西。
- 把沒有重讀的來源的日期一起改新，過期的快照看起來就是新的。
- 改到已安裝的副本，下次更新外掛就被蓋掉，別人也拿不到。

下面每一步都是為了擋這三件事。

## 開始前 — 建立 task 清單（強制）

動任何事之前，用 `TaskCreate` 建下面七個 task。每做完一步，立刻用 `TaskUpdate` 標成 completed。

| task | 步驟 | 類型 | 可以跳過的條件 |
|---|---|---|---|
| `classify_update` | Step 1：判定這次是 A 到 E 的哪幾種 | 判斷 | 不可跳過 |
| `locate_record` | Step 2：確認記錄在哪裡、要改哪一份 | 機械 | 不可跳過 |
| `read_record` | Step 3：把記錄整份讀完 | 機械 | 不可跳過 |
| `reread_sources` | Step 4：重讀該讀的來源 | 驗證 | 不可跳過 |
| `edit_fields` | Step 5：逐欄修改 ⚠️ | 判斷 | 這次只有 D，而且重讀的來源都沒變：只改日期 |
| `validate_and_diff` | Step 6：`validate.py`、`verify.py`、讀完 diff | 驗證 | 不可跳過 |
| `report` | Step 7：回報四件事 | 機械 | 不可跳過 |

**為什麼強制**：這個流程最容易漏的，是漏了也不會報錯的那幾步（查分支、沒重讀的來源不改日期、把 diff 讀完）。漏掉之後，記錄看起來一切正常。

## Step 1 — 這次是哪一種更新

封閉列舉，只有這五種，**不得依性質相似類推第六種**。一次可以同時有幾種，每一種照自己那一列做。

| 種類 | 何時 | 要重讀什麼 | 會動到什麼 |
|---|---|---|---|
| A 來源變了 | `verify.py` 回報 `CHANGED`，或重讀時發現原文與記錄引用的不同 | 變動的那個來源，整頁 | 受影響的欄位；該來源的兩個日期與 hash 基準 |
| B 記錄有缺口 | 記錄點名了一份文件或政策，卻沒有收它的內容；或讀者需要的欄位在記錄裡根本沒有 | 缺的那份文件，以及指向它的那個既有來源 | 新增來源、新增欄位，必要時 `warnings` |
| C 記錄寫錯 | 欄位與它引用的來源原文不符，而來源沒有變 | 那個欄位的 `src` | 那個欄位；該來源的 `last_verified_at` |
| D 重新驗證 | 來源沒有變，只是太久沒確認（`NEEDS_AGENT`、`BASELINE`、`last_verified_at` 太舊、有人要投稿） | 要驗證的每一個來源 | 只有 `last_verified_at` |
| E 定期翻新 | 每年會換的東西：指標、APC、主編；研討會新一屆的 `cycle` | 刊載那個數字或那一屆資訊的頁面 | `identity.metrics`、`fees`、`cycle`；該來源的日期 |

邊界：

- B 的「缺口」指記錄裡**沒有**的東西。記錄裡有、但標 `not_published` 的欄位不是缺口：重查後仍然沒有是 D，重查後官方現在公布了是 A。
- 場次改名、換出版社、停刊，或記錄的 `id` 與檔名要改，不在這五種之內。停下來告訴使用者：別的記錄、報告與比較表可能引用這個 `id`。
- 場次不在語料庫，用 `add-venue`。

## Step 2 — 找到記錄，確認改的是哪一份

記錄有三個可能的位置，改之前先分清楚。

1. **已安裝的外掛**（路徑含 `plugins/cache/`）。這是發行版的副本，只能讀。
2. **外掛的原始 repo**（`Academic-Toolkit/research-workflow` 的 clone，記錄在 `plugins/research-submission/venues/`）。更新寫在這裡。
3. **原始 repo 裡還沒合併的分支**。記錄可能已經有人建好，只是還沒發版。

```bash
git -C <clone> log --all --oneline -- 'plugins/research-submission/venues/*/<venue>.yaml'
git -C <clone> branch -a --contains <上一行印出的 commit>
```

- 記錄只在某個未合併的分支上：以那一份為準，從那個分支接著改，不要重新建檔。
- 沒有 clone：不要改已安裝的副本。把這次查到的內容（來源網址、讀取日期、原文）整理給使用者，建議到 repo 開 issue 或 PR。
- clone 裡有別人未提交的檔案，或不在預設分支上：另開一個 git worktree 與分支來改，不動那些檔案。

> 為什麼要查分支（2026-11-22）：`submit-to` 在已安裝的版本裡找不到一本期刊，轉去 `add-venue` 建檔；讀完官網才發現，那本期刊的記錄已經在原始 repo 一個未合併的分支上。差一步就重複建檔。

## Step 3 — 先把記錄整份讀完

動手前讀完整份 YAML，列出：

- 每個來源的 `id`、`role`、`fetch.method`、`fetched_at`、`last_verified_at`；
- 這次更新涉及的欄位，以及它們的 `src`；
- 可能受影響的 `warnings`；
- 檔頭註解裡寫的擷取方式與已知的坑。

**不要整份重寫。** 改版通常只動少數欄位；整份重寫比逐欄比對更容易出錯，也丟掉累積的查證成果。

## Step 4 — 重讀來源

讀頁面的方式照 `add-venue` 的 Step 2：預設用 safari-browser，鎖定自己開的分頁，用完只關自己開的；另外用 curl 測一次，只為了記 `http_viable`。

- **只重讀 Step 1 那一列要你讀的來源。** 沒讀的來源在 Step 5 不改日期。
- **新文件從既有頁面的連結點進去**，把實際的網址記下來。網址不可推測。
- **確認 `must_contain` 還在**，再逐一核對這次涉及的欄位所引用的原文。
- **一個來源要算「重讀過」，記錄從它引用的每一段原文都要在這次讀到的頁面上找到。** 只讀了頁面的一部分，就只能說那一部分確認過；這個來源的日期不改。引用很多時，把記錄裡的引文逐段拿去比對這次存下的頁面文字，列出找不到的。
- **搜尋只用來找位置，結論要靠讀。** 核對一個欄位時，把頁面上那一節從頭讀完，不是搜到關鍵字就算數。要下「官方沒有公布」的結論之前，換幾種說法再搜一次，並讀完相關的那一節；被截斷的搜尋結果不能當成頁面上沒有的證據。
- **表格要逐格讀。** `innerText` 會把表格攤平成一串文字，哪一格屬於哪一欄就看不出來了。用 DOM 逐列逐格取：

```bash
safari-browser js "return JSON.stringify([...document.querySelectorAll('table tr')].map(tr => [...tr.children].map(td => td.innerText.trim())))" --url <子字串>
```

> 為什麼（2026-11-22）：一份出版社的 AI 使用指引把三個等級排成三欄的表。攤平的文字裡，十九個例子連成一串，看不出哪個例子屬於哪一級；而讀者要查的正是這個對應。

## Step 5 — 逐欄修改 ⚠️

這一步靠判斷，不是照抄。每一條都對應一種實際發生過或很容易發生的錯。

1. **只改這次涉及的欄位。** 其他行一個字都不動。
2. **每個改過或新增的欄位都帶 `src`**；會隨時間變的值帶 `as_of`。規定附上原文（`原文："…"`），解讀另外寫，兩者分開。
3. **查證過的標記照下表處理。**

   | 情況 | 怎麼寫 |
   |---|---|
   | 這次沒有重查 | `not_published`／`not_found`／`not_applicable` 原樣保留，`checked` 不動 |
   | 重查了，官方仍然沒有 | 只更新 `checked` |
   | 重查了，官方現在有了 | 換成值，`note` 記下何時起有 |

4. **日期只改實際重讀過的來源。**

   | 這個來源 | `fetched_at` | `last_verified_at` |
   |---|---|---|
   | 重讀了，內容沒變（含 C：記錄寫錯、來源沒變） | 不動 | 今天 |
   | 重讀了，內容變了，已重新擷取 | 今天 | 今天 |
   | 這次新增的 | 今天 | 今天 |
   | 沒有重讀 | 不動 | 不動 |

   `last_verified_at` 不得早於 `fetched_at`（`validate.py` 的 L1）。
5. **更正要留痕跡（C）。** 在該欄位的 `note` 寫一句「YYYY-MM-DD 更正，原記為 …」。照舊值做過事的人需要知道它改過。
6. **新增的來源要完整。** `id`、`role`、`url`、`note`（這頁有什麼、怎麼找到的）、`fetch`（`method`、`http_viable`、`http_failure_mode`、`validity` 的 `must_contain` 與 `min_extracted_chars`）、`snapshot`（兩個日期，`extracted_sha256: null`）。`must_contain` 的選字原則見 `add-venue` 的 Step 3。
7. **出版社的通則與本刊的條文分開放、分開標。** 本刊引用通則來設門檻時，兩者都要收：本刊那句話是門檻，通則的定義是門檻的意思。每一句都標明是誰說的。兩者不一致，或本刊比通則嚴，就逐字並列並寫進 `warnings`，不替它們調和。

   | 寫法 | 讀者得到什麼 |
   |---|---|
   | 只收本刊的公告：「超出允許的輔助性使用（某一級）者可直接退稿」 | 知道有門檻，不知道自己的用法算不算那一級 |
   | 公告之外，再收通則裡各級的定義、例子與揭露要求，並標明通則是全品牌的、門檻是本刊加的 | 可以對照自己的用法，也看得出本刊比通則嚴 |

8. **來源互相矛盾時並列**（`conflicting: true` 加 `values`），不挑一個。
9. **`requirements` 與 `cycle` 不放錯格。** 研討會換屆時更新 `cycle`；上一屆的日期地點不得留著冒充新一屆，新一屆還沒公布的項目標 `not_published`。
10. **`warnings` 跟著改。** 這次更新若改變了使用者投稿前一定要知道的事，新增或改寫對應的警告；已經不成立的警告刪掉。
11. **檔頭註解加一行更新紀錄**：日期、種類、範圍。例：`# 2026-11-22 更新（B）：補收出版社 AI 使用指引的分級。` schema 沒有欄位可以記「哪個欄位哪一天改過」，這一行是給下一個讀記錄的人看的。
12. **記錄只放場次公開的規定。** 更新的起因若是某個人的稿件，起因不寫進記錄，也不寫進 commit、PR 或 issue。

## Step 6 — 驗證

**跑的是記錄旁邊那一份腳本**，不是已安裝外掛裡的那一份。`verify.py` 讀的是它自己所在的外掛目錄底下的 `venues/`；跑錯份，驗證的是沒改過的副本。

```bash
cd <clone>/plugins/research-submission
python3 scripts/validate.py venues/<publisher>/<venue>.yaml
python3 scripts/verify.py <venue-id>
git diff -- venues/<publisher>/<venue>.yaml
```

- `validate.py`：錯誤修到零，警告讀懂再決定。
- `verify.py` 的每一行：

  | 狀態 | 在更新時的意思 |
  |---|---|
  | `UNCHANGED` | 來源沒變 |
  | `BASELINE` | 這個來源還沒有 hash 基準，這次只算了一次。**不等於沒變**；你在 Step 4 重讀過才算確認 |
  | `NEEDS_AGENT` | 腳本抓不到，確認靠你在 Step 4 的重讀 |
  | `CHANGED` | 來源變了：回 Step 1 加一列 A |
  | `INVALID`、`FETCH_FAILED` | 沒有驗證到。不得更新該來源的 `last_verified_at` |

- `verify.py --write` 宣稱會把 `last_verified_at` 寫回，但目前不會寫（Academic-Toolkit/research-workflow#2）。跑完看 `git diff`：檔案沒變，就照 Step 5 的日期表手動改，`extracted_sha256` 維持原樣。#2 修好之後這一條可以刪。
- **把 diff 從頭讀到尾。** 每一行變動都要屬於這次更新；不是你要改的行，還原。
- 改了 `identity.metrics` 或 `fees`，跑 `python3 scripts/venue_table.py <venue-id>`，確認比較表還讀得到。

## Step 7 — 回報

回報四件事，缺一不可：

1. **改了什麼**：每個欄位的改前、改後與來源。
2. **重讀了哪些來源**：哪一天、用什麼方式讀的。
3. **哪些來源沒有重讀**：它們的 `last_verified_at` 沒有動，仍是舊的日期。
4. **對使用者的影響**：新增或改寫的警告、變嚴的規定；正照著舊內容準備稿件的人要回頭檢查什麼。

一筆記錄的一次更新是一個 commit。推送與合併照 repo 的流程，這個 skill 不替使用者推送。

## 常見陷阱（實測踩過）

- **公告只寫代號。** 期刊的公告常只寫通則裡的一個名稱（例如只寫某一級的顏色），門檻的意思在通則那份文件裡。只收公告那一句，記錄等於沒有回答讀者的問題。這是 B，不是「記錄已經有了」。
- **表格被攤平。** 見 Step 4。
- **改到已安裝的副本，或跑到已安裝的腳本。** 見 Step 2 與 Step 6。
- **記錄在未合併的分支上。** 見 Step 2。
- **`BASELINE` 當成通過。** 多數來源還沒有 hash 基準，`verify.py` 每次都回 `BASELINE`。確認來源的依據是你這次的重讀，不是這個狀態。
