# research-workflow

研究流程用的 Claude Code plugins，從研究會議紀錄、研究設計到投稿。共同原則是每個產出都指得回來源：會議紀錄指回逐字稿，投稿規定指回帶時間戳的一手來源快照。

| Plugin | 做什麼 |
|---|---|
| [`research-meetings`](plugins/research-meetings) | 研究會議錄音／逐字稿 → 可溯源的研究會議紀錄（標楷體 .tex → PDF；討論、結論、待辦），每一點指得回逐字稿 |
| [`research-design`](plugins/research-design) | 研究假設說明文件（研究假設一覽）：期刊句式且不宣稱因果、每條分研究假設／依據／統計三層，頁首說明受測者實際做了什麼 |
| [`research-presentation`](plugins/research-presentation) | 海報／短講的備忘稿：30 秒、約 2 分鐘、4–5 分鐘導覽版（含〔動作〕指示），日文標「漢字（かな）」讀音並附數學記號念法表 |
| [`research-submission`](plugins/research-submission) | 投稿須知的一手來源語料庫（期刊與研討會），投稿前強制現場驗證 |

## Install

```
/plugin marketplace add PsychQuant/research-workflow
/plugin install research-meetings@research-workflow
/plugin install research-design@research-workflow
/plugin install research-presentation@research-workflow
/plugin install research-submission@research-workflow
```

**從舊名遷移**：本 repo 原名 `live-submission-guidelines`，marketplace 原名 `live-submission-guidelines-marketplace`，`research-submission` 原名 `live-submission-guidelines`。GitHub 會把舊 repo URL 轉到新址，但 Claude Code 以 marketplace 的 `name` 識別，所以已安裝舊版的機器要移除舊 marketplace 再加新的：

```
/plugin marketplace remove live-submission-guidelines-marketplace
/plugin marketplace add PsychQuant/research-workflow
/plugin install research-submission@research-workflow
```

## research-submission：投稿須知語料庫

學術投稿須知的**一手來源語料庫** —— 期刊與研討會。每筆記錄帶來源 URL、擷取日期、最後驗證日期，以及抽取後內容的 sha256。

投稿須知不該憑模型記憶回答：規定會改、各刊差異細碎，而錯誤的代價不對稱 —— **照著錯的字數上限寫完一整篇稿是不可逆的浪費**。

裝好之後照常問投稿問題即可（「Psychological Methods 字數上限多少」「幫我對照 IMPS 的規定」），`submit-to` skill 會自動接手；問「這篇該投哪」「A 跟 B 哪個適合這篇」時由 `choose-venue` 接手。要把病歷寫成病例報告投稿時，`case-report` skill 會從本語料庫讀該場次的規定。

### 跟 livedocs 的關係：哲學相同，機制相反

繼承 [livedocs](https://github.com/PsychQuant/livedocs) 的 primary-source-first 原則，但**存取策略相反**：

| | livedocs | 本專案 |
|---|---|---|
| 底層變動速度 | 快（套件版本天天動） | **慢**（投稿須知數年不變） |
| 一手來源可機讀？ | 是（25 個 docs host 約 88% 有 `llms.txt`） | **否**（6 家出版社 `llms.txt` **0/6**，半數擋 bot） |
| 策略 | **不存**，每次現查 | **存**，語料庫就是產品 |
| 「live」的意義 | 即時取得最新版 | **驗證存下來的還算不算數** |

livedocs 不能存，因為存了就過時；本專案必須存，因為底層本來就慢、而且抓取成本高。

### 兩種嚴格度

| 情境 | 政策 |
|---|---|
| 瀏覽 / 跨場次比較（「A 和 B 哪個字數寬」） | 讀快照。快、可離線 |
| 選期刊（`choose-venue`） | 排序讀快照；回報淘汰前、開始為第一志願改稿前現場驗證 |
| **實際準備投稿** | **強制現場驗證**；記錄過期不得靜默通過 |

投稿前是唯一「錯了會很貴」的時刻。平常寬鬆、關鍵時刻嚴格，優於一律嚴格（難用）或一律寬鬆（危險）。

### 為什麼 provenance 這麼囉嗦

因為天真的做法會**安靜地說謊**。實測 APA：

```
200      212 bytes  sha256:8bd329e5869bd8e0  /pubs/journals/met/submit
200      212 bytes  sha256:8bd329e5869bd8e0  /pubs/journals/met
200      212 bytes  sha256:8bd329e5869bd8e0  apastyle.apa.org/jars/quantitative
```

三個不同頁面回**同一個 hash**，內容是 Incapsula bot 挑戰頁，狀態碼是 **200 而非 403**。對 HTTP body 取 hash 做 freshness 檢查，會永遠回報「沒變動、仍然新鮮」，而它監看的是一個空殼 —— **比沒有檢查更危險，因為它製造虛假信心**。

所以 schema 強制：hash 算在**抽取後純文字**上、每個權威來源必須有 `fetch.validity` 斷言、跨來源 hash 相同視為**故障**。

### 已收錄

| ID | 類型 | 狀態 |
|---|---|---|
| `apa/psychological-methods` | journal | 4 來源，2026-08-03 |
| `psychometric-society/imps` | conference | 3 來源，2026-08-03（cycle 2026 已辦畢） |
| `sage/global-spine-journal` | journal | 2 來源，2026-10-05（已不收病例報告） |
| `toa/spring-meeting` | conference | 6 來源，2026-10-05（中華民國骨科醫學會春季會；cycle 2026 已辦畢；摘要字數只在登入後表單） |
| `tpa/annual-meeting` | conference | 4 來源，2026-08-08 |
| `asa/jasa` | journal | 10 來源，2026-10-08 |
| `rss/jrss-series-b` | journal | 10 來源，2026-10-08 |
| `rss/jrss-series-c` | journal | 10 來源，2026-10-08 |
| `biometrika-trust/biometrika` | journal | 8 來源，2026-10-08 |
| `ims/annals-of-statistics` | journal | 17 來源，2026-10-08 |
| `psychometric-society/psychometrika` | journal | 25 來源，2026-10-08 |

需求驅動 —— 有人要投才加。收錄新場次用 `add-venue` skill。

### 開發

```bash
python3 plugins/research-submission/scripts/validate.py          # schema + lint
python3 plugins/research-submission/scripts/verify.py [venue-id] # 新鮮度驗證
```

設計理由、實測發現與未決事項見 [`SCHEMA.md`](SCHEMA.md)。

### 現況（v0.5.0）

**可用，但年輕。** 一個 schema、三支腳本（`validate.py`、`verify.py`、`venue_topic_scan.py`）、四個 skill（`choose-venue`、`submit-to`、`add-venue`、`case-report`），全部驗證過（含反例測試）。尚未決定的事誠實列在 `SCHEMA.md` 末尾 —— 主要是抽取器尚未定版（故 `extracted_sha256` 目前為 `null`）、以及是否需要 MCP server（目前判斷不需要）。

MIT License.
