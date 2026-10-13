# research-design (plugin)

研究設計階段的文件。完整說明見 [repo README](https://github.com/PsychQuant/research-workflow)。

## Skills

| Skill | 何時觸發 |
|---|---|
| `hypothesis-brief` | 把研究假設寫成給讀者看的說明文件（研究假設一覽）：期刊句式且不宣稱因果、每條分研究假設／依據／統計三層、頁首說明受測者實際做了什麼、名詞與統計術語附白話 |

## Layout

```
skills/hypothesis-brief/SKILL.md            # 流程與規則
skills/hypothesis-brief/templates/brief.tex # XeLaTeX 範本（示例為虛構情境）
```

依賴：XeLaTeX（xeCJK、needspace、tikz）、`pdftoppm`（渲染頁面檢查）。
