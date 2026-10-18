---
name: submit-to
description: Use when the user has chosen (or is checking) a specific academic journal or conference and is submitting to it or preparing a manuscript for it — word limits, abstract rules, masked/blind review, required sections, data/code availability, reporting standards (JARS/TOP), deadlines, or formatting. Triggers on "投稿", "submit to <journal>", "字數上限", "截稿日", "abstract word limit", "does <venue> require preregistration", "check my draft against <venue>", or any question about a named venue's rules (Psychological Methods, IMPS, …). Reads a timestamped primary-source corpus instead of model memory, and forces live re-verification before an actual submission. NOTE despite the name this skill NEVER performs the submission itself — it prepares and checks, then stops before the portal. Division of labour: deciding which venue fits a manuscript — even when the user names candidates or asks about one venue ("這篇該投哪", "A 跟 B 哪個適合這篇", "X 適合這篇嗎") — is choose-venue; comparing one rule across venues ("A 和 B 哪個字數寬") or checking a draft against a chosen venue is this skill.
---

# submit-to

> **名字的免責**：本 skill **不會**替使用者送出稿件。它查規定、對照稿件、在真的要投之前做現場驗證，然後**停在投稿系統之前**——按下 submit 永遠是作者本人的動作。若使用者要求「幫我投出去」，說明本 skill 到哪裡為止，並把 portal URL 給他。

投稿須知**不要憑記憶回答**。模型記憶對期刊規定特別不可靠：規定會改、各刊差異細碎，而錯誤的代價不對稱——照著錯的字數上限寫完一整篇稿，是不可逆的浪費。

本 skill 讀 `${CLAUDE_PLUGIN_ROOT}/venues/**/*.yaml`，每筆記錄都帶 provenance（來源 URL、擷取日、最後驗證日、內容 hash）。

## Step 0 — 判斷情境，決定嚴格度

這一步決定要不要現場驗證。**分錯了不是效率問題，是安全問題。**

| 情境 | 政策 |
|------|------|
| **瀏覽/比較**——「A 和 B 哪個字數寬」「IMPS 大概什麼時候」 | 讀快照即可。快、可離線 |
| **選期刊**——「這篇該投哪」「A 跟 B 哪個適合這篇」 | 交給 `choose-venue`（它排序用快照，回報淘汰前與開始改稿前才現場驗證） |
| **實際準備投稿**——「我要投 X」「幫我檢查這份稿」「照 X 的規定改」「要交了」 | **強制現場驗證**（見 Step 3）。記錄過期不得靜默通過 |

判準是「使用者會不會據此動筆或送出」。會，就走嚴格路徑。

## Step 1 — 找到 venue 記錄

```bash
ls ${CLAUDE_PLUGIN_ROOT}/venues/*/          # 列出已收錄的場次
grep -ril "<關鍵字>" ${CLAUDE_PLUGIN_ROOT}/venues/
```

**找不到 → 預設先跑 `add-venue` 建檔，再回到 Step 2 讀那筆新記錄。** 不要用記憶補，也不要只回報「尚未收錄」就停下或改用臨時抓的頁面直接回答。三種情境（瀏覽、選期刊、準備投稿）一律如此：臨時讀到的規定沒有 provenance、沒有 hash 基準，下次還得從頭查，也無法在投稿前用 `verify.py` 比對來源是否變動。

例外只有兩種（封閉列舉，不得依性質相似類推第三種）：

1. **使用者在當次明說不要收錄**（例如「只是隨口問，不用建檔」）。此時照實說「尚未收錄、以下是臨時讀取」，並附上讀取的 URL 與日期。
2. **`add-venue` 跑完仍無法建檔**（一手來源找不到、或抓到的都通不過 `validity` 斷言）。此時回報「未收錄，無法驗證」，**不得**用記憶補規定。

建檔完成後告訴使用者新記錄的路徑（`venues/<publisher>/<id>.yaml`），因為它會進語料庫，之後別人會當成權威來用。

> 為什麼是預設（2026-10-19）：投 J Neurosurg: Spine 前跑本 skill，語料庫沒有這本，舊版寫的是「走 `add-venue` **或**直接告訴使用者尚未收錄」，於是只做了現場重讀官網、回報結果就停了。使用者看到後指出應該預設先建檔。兩個選項並列等於把建檔變成可省略的那一個。

## Step 2 — 讀取並回答

記錄的結構（完整規格見 `${CLAUDE_PLUGIN_ROOT}/schema/venue.schema.json`）：

- `requirements` — **慢**（數年不變）：篇幅、摘要、格式、必要段落、審查方式、資料/程式碼政策、外部標準
- `cycle` — **快**（每年翻新）：截稿日、地點、報名窗口。期刊多為 `applies_to: null`，研討會的重心在這裡
- `sources[]` — provenance
- `warnings[]` — **一定要向使用者複述**

### 回答時的三條紀律

1. **一律附上 provenance**：「依 2026-08-03 的快照（來源 apa.org/pubs/journals/met/submit）」。這是本 plugin 存在的理由，省略等於退回憑記憶。
2. **`status: not_published` / `not_found` 要照實說**，不要填補。「官網未公布接受率」和「我不知道」是不同的資訊，前者已經幫使用者省下再查一次的力氣。
3. **原生單位不要擅自換算**。「50 頁雙倍行距含參考文獻」不等於任何確定字數；`approx_words` 若有，必須連同 `assumption` 與 `confidence` 一起講。

### 條件式要求

`requirements.review.conditional[]` 裡的項目**不是無條件適用**。例如遮蔽審查是選配，但一旦選了就帶出一整串額外規定（清除補助案號、IRB 機構名、自我引用、repository 連結）。攤平成單一清單會誤導使用者。

### 外部標準的缺口

`requirements.standards[].applicability[]` 可能標 `status: no_module`——那是**實測發現的真實缺口**，不是資料不全。例：JARS-Quant 對模擬研究、對提出新估計式的方法論文，都沒有對應模組。遇到就照實說，並給 `escalation`（如 styleexpert@apa.org）。

## Step 3 — 投稿前的現場驗證（嚴格路徑才做）

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify.py <venue-id>
```

輸出的意義：

| 狀態 | 意義 | 該怎麼辦 |
|------|------|----------|
| `UNCHANGED` | 來源未變，快照有效 | 可以放心用 |
| `CHANGED` | **來源已變動** | **停下來**。重新擷取該頁，人工覆核差異後才繼續 |
| `NEEDS_AGENT` | 該來源擋一般 HTTP（如 APA 的 Incapsula） | 你自己用 WebFetch 或 safari-browser 抓，比對關鍵欄位 |
| `BASELINE` | 記錄還沒有 hash 基準，這次只是第一次建立 | **不等於未變動**。自己打開被引用的頁面，確認原文仍在並報出確認日期 |
| `EXTRACTOR_MISMATCH` | 記錄的 hash 是別版抽取器算的 | hash 不可比；照 `BASELINE` 處理並重建基準 |
| `INVALID` | 抓到了但內容不對（缺必含字串/過短） | 視為抓取失敗，**不可**當成「沒變動」 |
| `FETCH_FAILED` | 抓不到 | 明確告知使用者「無法驗證」，並報出快照已幾天未驗證 |

**`NEEDS_AGENT` 不等於通過。** 那表示驗證責任落到你身上——去抓、去比對，不要略過。

### staleness 怎麼算

`now − last_verified_at`，**不是** `fetched_at`。2020 年抓的、上週驗證過沒變，是新鮮的；上個月抓的、之後沒驗證過，反而不確定。

## Step 4 — 對照稿件（使用者要求時）

逐項比對，輸出**可勾選的清單**，並明確分成三類：

- ✅ 已滿足
- ❌ 未滿足（**指出具體差距**：現在幾頁 / 上限幾頁）
- ⚠️ 無法自動判定（如「是否已在他處投稿」這種只有作者知道的事）

不要把第三類混進前兩類假裝完整。

## 常見陷阱（實測踩過）

- **APA 的兩份摘要**：技術摘要 ≤250 字 + 另一份給非方法學者的非技術摘要。第二份極易漏。
- **URL 不可推測**：`/submission-guidelines` 是 404，真路徑是 `/submit`；`/imps` 是 404，真路徑帶年份 `/imps-2026`。一律用記錄裡的 URL。
- **須知是散的**：Psychological Methods 分佈在三個頁面（期刊首頁 / submit / apastyle 的 JARS）。只讀一頁會漏。
- **研討會的 cycle 會過期**：`status: held` 表示那屆已辦完，日期地點**不得**沿用到下一屆。
