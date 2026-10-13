# research-submission (plugin)

學術投稿須知的一手來源語料庫。完整說明見 [repo README](https://github.com/PsychQuant/research-workflow)。

## Skills

| Skill | 何時觸發 |
|---|---|
| `choose-venue` | 判斷哪本（或某一本）適合這篇稿件：用官方規定淘汰、看期刊實際刊了什麼判斷主題契合、比對最接近的前人結果，排序並給投稿順序 |
| `submit-to` | 查詢規定、跨刊對照單一規定、對照已選定期刊的稿件、投稿前驗證 |
| `venue-report` | `choose-venue` 跑完後，把結果做成 `.tex` 與 PDF 報告（逐刊優缺＋由腳本產生的比較表，含 IF 與分區） |
| `add-venue` | 場次尚未收錄，或 `verify.py` 回報來源已變動 |
| `case-report` | 把病歷寫成去識別化、文獻有據、經對抗式驗證的病例報告（會議摘要或期刊稿）；投稿規定一律讀本語料庫 |

## Scripts

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py            # schema + 4 錯誤 / 2 警告 lint
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify.py <venue-id>   # 重抓、斷言、比對 hash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/venue_topic_scan.py --venue <venue-id> --term "<主題>"   # 期刊實際刊了什麼（OpenAlex 標題掃描）
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/venue_table.py <venue-id> ...   # 比較表（IF、分區、接受率、速度、APC），讀記錄產生，不手抄
```

## Layout

```
venues/<publisher>/<venue>.yaml   # 語料庫
schema/venue.schema.json          # 形式契約
scripts/{validate,verify}.py
scripts/venue_topic_scan.py      # 期刊實際刊了什麼（OpenAlex 標題掃描，choose-venue 用）
scripts/venue_table.py           # 比較表產生器（venue-report 用）
skills/venue-report/templates/   # 報告 .tex 範本
```

依賴：`pyyaml`、`jsonschema`（validate.py）；`verify.py` 只用標準庫；`venue_topic_scan.py` 需要 `pyyaml` 與網路（OpenAlex）。
