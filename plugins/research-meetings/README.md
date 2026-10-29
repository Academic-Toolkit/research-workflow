# research-meetings (plugin)

研究會議紀錄：把研究討論、統計諮詢、合作會面的錄音或逐字稿，整理成每一點都指得回逐字稿的研究會議紀錄（XeLaTeX 標楷體 .tex，編譯成 PDF）。完整說明見 [repo README](https://github.com/Academic-Toolkit/research-workflow)。

## Skills

| Skill | 何時觸發 |
|---|---|
| `research-minutes` | 研究會議的錄音或逐字稿要寫成紀錄：研究報告、方法建議、結論狀態、待辦與分工、作者安排 |

## Scripts

```bash
python3 -I ${CLAUDE_PLUGIN_ROOT}/skills/research-minutes/scripts/verify_provenance.py <校對版.srt> <溯源驗證.jsonl>
bash ${CLAUDE_PLUGIN_ROOT}/skills/research-minutes/scripts/compile.sh <會議名>_會議紀錄_<日期>.tex
```

`verify_provenance.py` 只用 Python 標準庫；`compile.sh` 需要 TeX Live 的 `xelatex`、poppler 的 `pdfinfo`／`pdftotext`，以及標楷體（DFKai-SB）。

## 相關

- 錄音轉逐字稿與校對：bestASR（`bestasr:context-ingest`、`bestasr:transcript`、`bestasr:srt-proofread`）
- 機關行政會議、跨機構協調會：`sinica-admin:meeting-minutes`（公文體、標楷體 PDF）。本 plugin 的內容紀律改編自它。

## 維護

- 內容紀律的正本在 `sinica-admin:meeting-minutes`〈內容紀律〉。那邊改了，回頭比對 SKILL.md 的八條最低限度是否要跟著改。
- 兩支腳本改檢查規則後，要用一份故意違規的輸入確認它會失敗。
