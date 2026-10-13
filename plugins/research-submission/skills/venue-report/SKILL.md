---
name: venue-report
description: Use after choose-venue has produced a ranking, when the user wants it as a document — "做成報告", "產生 PDF", "匯出 .tex", "給我可以轉給別人的版本", "寫成報告說明優缺". Turns the choose-venue result into a compiled .tex + PDF report with per-journal pros and cons and an official-facts comparison table (IF, JCR/SJR quartile, acceptance rate, speed, APC) generated from the corpus records by script, not retyped. Does not re-judge the ranking; if choose-venue has not been run in this conversation, run it first.
---

# venue-report

把 `choose-venue` 的結果做成 `.tex` 與 PDF 報告。**本 skill 只負責把已有的判斷排版成文件，不重新判斷排序**；兩套結論會互相矛盾。

| 要回答的問題 | 唯一來源 |
|---|---|
| 比較表裡的數字 | `scripts/venue_table.py` 讀語料庫記錄，**不手抄** |
| 排序、淘汰、優缺的判斷 | 本次對話中 `choose-venue` 已產出的結果 |
| 版面 | `templates/report.tex` |

**前置條件**：本次對話已跑過 `choose-venue`，手上有淘汰清單、排序與翻盤條件。沒有就先跑它，再回來。

## Step 1 — 輸出位置與敏感度

先問使用者要存哪裡；預設是目前工作目錄，**不是 repo 的 `docs/`**。報告通常含稿件細節與使用者的偏好，放進公開 repo 不合適。存好後只回報路徑並註明「未 commit」，**不自動 commit**。

## Step 2 — 產生比較表（不手抄）

1. 寫一份順序檔（每行一個 venue id；# 開頭為註解），順序＝報告裡的順位，淘汰的期刊接在最後。
2. 執行：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/venue_table.py --order-file order.txt --format latex > rows.tex
```

3. **處理 stderr 的警告。** 「?」的意思是「這支腳本認不得記錄的結構」，**不是**「官方未公布」（官方未公布會印「未公布」）。逐一處理：
   - 記錄有值但欄位名稱特殊 → 補 `venue_table.py` 的別名，或把記錄改成下面的標準欄位。
   - 記錄真的沒有（例如分區還沒查）→ 先查，不要手填。**絕對不可憑記憶補 IF 或 Q 值**；查不到就寫「未取得」。
4. **‡ 表示自行抽樣估計**（記錄的 `identity.metrics.estimates`，不是官方統計）。顯示為「未公布（自行估計中位約 N 天‡）」，官方欄位仍是「未公布」。報告裡要寫明方法、樣本數、限制三件事（只含被刊出稿件、樣本是某年刊出而非某年投稿、Received 的定義），**不得把估計與其他刊的官方數字排名**；在口徑說明段加一句 ‡ 的解釋。估計怎麼做見 `add-venue`。
5. 輸出中的 † 表示該格有附註（例如單一研究與多研究的篇幅不同），附註行會跟在表後，要抄進報告的口徑說明。

### 記錄的標準欄位（`identity.metrics`）

`add-venue` 收錄時請用這些名稱；腳本也容忍已知別名。

| 欄位 | 形狀 |
|---|---|
| `impact_factor` | `{value, year, as_of, src}`；官方未公布寫 `{status: not_published, checked}` |
| `quartiles` | 清單：`{system: JCR 或 SJR, category, quartile: Q1–Q4, rank, year, as_of, src}`；查不到寫 `{status: not_found, checked, note}` |
| `acceptance_rate` | `{value, unit, year, basis}`；官方只公布拒絕率時，`acceptance_rate` 寫 not_published，另放 `rejection_rate.by_year` |
| `time_to_first_decision`、`time_submission_to_acceptance` | `{value, unit: days, statistic: median 或 mean, year, basis}`；口徑是官方的定義，不是你的換算 |

**分區（Q）有兩個系統，不是同一個統計量**：JCR（Clarivate，臺灣一般說的「Q 幾」）與 SJR（SCImago，Scopus 資料）。表格的分區欄一律標明系統，**不混用、不互換**。JCR 需登入；讀不到時用 SJR 並標 SJR，不可寫成 JCR。一本期刊有多個學科類別時分區可能不同，表格顯示「Q1／Q2」，完整類別放在逐刊段落。

## Step 3 — 填範本

複製 `templates/report.tex`，把 `%%TABLE_ROWS%%` 換成 `rows.tex` 的內容，再填每一個「【待填】」。

- **官方事實與判斷分欄**：判斷句尾一律加 `\J`；事實附數字、口徑、來源與日期。
- **逐刊優缺**：每本期刊一個小節，優點與缺點各一個清單。缺點若來自官方文字，引原句；「保留語氣」的句子（unless、in principle、may）列為缺點，**不寫成排除**。優缺是相對於這篇稿件與使用者條件，不是期刊的一般評價。
- **前人結果**：只寫讀過的。只讀摘要就標「只讀摘要」，沒讀到的標「未查證」。
- **主題證據**：寫明計法（片語或寬鬆）、年份窗口、查詢日；掃不到的期刊列為「未取得」，不要留空白。數字異常偏低時先查來源是否被拆分，不可直接讀成「不收這個主題」。
- **未取得的項目都要寫進最後一節**，包括：沒讀到的社論、需要登入的頁面、尚在重試的查詢。

## Step 4 — 編譯與檢查

```bash
grep -c '待填' report.tex        # 必須是 0
latexmk -xelatex -interaction=nonstopmode -halt-on-error report.tex | tee build.log
grep -c 'Overfull .hbox' build.log   # 必須是 0（見下「表格寬度」）
pdfinfo report.pdf | grep Pages
pdffonts report.pdf              # 全部 emb = yes
```

### 表格寬度（超寬一定要處理）

`Overfull \hbox (N pt too wide)` 代表有東西超出頁面右緣，**PDF 裡看起來只是被截掉，編譯照樣成功**。任何一件都要處理，不可忽略；超出 1pt 以內的才可以放過。處理順序：

1. **直向的表一律用 `tabularx{\textwidth}`**，文字欄用 `X` 或 `p{寬度}` 加 `\raggedright\arraybackslash`，數字欄用 `\centering\arraybackslash` 的 `X`。不要用沒有寬度限制的 `tabular` 放長標題。
2. **橫向表**：所有欄寬加總再加欄距（欄數 × 2 × `\tabcolsep`）必須小於橫向版面寬（A4、邊界 2.2 cm 時約 25.3 cm）。超過就縮欄寬，或把字級降到 `\footnotesize`、`\tabcolsep` 降到 3pt。
3. **單字比欄寬還長**（例如窄欄裡的 `environmental`）不會自動斷行，縮窄欄寬也沒用：改縮寫欄名，並在表後用一行文字寫出完整名稱。
4. 最後才考慮 `\scriptsize`；字小到難讀就改成拆成兩張表。

修完重編，**再看 Overfull 是 0**，並渲染頁面確認右緣沒有被截。

然後**把頁面渲染出來看**（`pdftoppm -r 60 -png`），不要只看編譯成功。至少檢查：

- 每一張表的右緣都完整在頁面內（含主題證據表這類直向表）。
- 橫向比較表整張在**同一頁**，沒有只剩一列溢到下一頁。
- 沒有只有一個標題的空白頁（`landscape` 環境會強制換頁，章節標題要放在環境裡面）。
- 目錄標題是中文；表格內的 `→`、`%`、`&` 沒有破版。
- 口徑說明在直向頁，沒有被截斷。

完成後 `latexmk -c` 清掉輔助檔，只留 `.tex` 與 `.pdf`。回報路徑、頁數，並說明哪些項目標為「未取得」。

## 失敗史

- **2026-10（Frontiers）**：官方完全沒有公布審稿速度，使用者問有沒有辦法知道。每篇文章頁都標 Received／Accepted，隨機抽 198 篇估得投稿到接受中位數約 108.5 天；但那只含被刊出的稿件，所以只能標為自行估計，不能與 Elsevier、Wiley 的官方中位數排名。
- **2026-10（第一次產生報告）**：比較表是從代理的文字回報手動轉進 `.tex` 的，十三列、十欄，全靠人眼對。這是整份報告最容易出錯的地方，因此現在由腳本讀記錄產生。
- 同一次：`landscape` 環境前的 `\section` 被孤立在一頁空白頁；表格最後一列溢到下一頁；目錄標題是英文。三項都是編譯成功但看頁面才發現，所以 Step 4 要求渲染頁面。
- 同一次：主題證據表用沒有寬度限制的 `tabular`，欄標題的 `consumption`、`environmental` 把表撐出右緣 163pt，編譯成功、PDF 右側被截掉，是使用者提醒後才查日誌發現。因此 Step 4 要求 Overfull 為 0。
- 同一次：各代理寫的記錄欄位名稱不一致（投稿到接受有三種寫法），腳本因此要容忍別名，並在認不得時印「?」而不是猜。

## 不做

- 不重新排序、不改淘汰結論；發現結論有問題，回到 `choose-venue` 重跑並說明改了哪個前提。
- 不 commit、不發布；使用者要分享再另外處理。
- 不為了讓表格好看而補值。
