---
name: choose-venue
description: Use when deciding which journal or conference fits a manuscript or idea — even when the user already names candidates. Triggers on "這篇該投哪", "投哪個期刊最好", "最適合的期刊", "A 跟 B 哪個適合這篇", "X 適合這篇嗎", "幫我選期刊", "which journal should this paper go to", "is X a good fit for this paper", "rank these venues for my paper", or a list of requirements (APC budget, review speed, double-blind, which field should recognise the work) with a request for the best match. Eliminates venues only on official corpus text, judges topical fit from what each venue actually published (OpenAlex title scan), checks the closest prior work, and returns a ranked submission sequence with the premises that would change it. Not for comparing one rule across venues ("A 和 B 哪個字數寬") or checking a draft against a chosen venue — that is submit-to; writing a case report is case-report.
---

# choose-venue

選期刊要兩種證據，來源不同，不可混用：

| 要回答的問題 | 唯一來源 |
|---|---|
| 這本期刊的**規定**（明文排除、篇幅、可重現性、審稿制度、費用） | 本 plugin 的語料庫 `${CLAUDE_PLUGIN_ROOT}/venues/**/*.yaml` |
| 這個**主題**它收不收、收的時候怎麼包裝 | 它實際刊出的論文（`scripts/venue_topic_scan.py`） |

兩者都不能憑記憶。推薦本身是判斷，不是事實：輸出時把官方事實（附來源與 `last_verified_at`）和你的判斷分開標示。

**分工判準**：判斷「哪本適合這篇稿件」——即使使用者已點名 A、B，或只問單一期刊「X 適合這篇嗎」——是本 skill；已經決定要投、問規定合不合，同一條規定跨刊對照（「A 和 B 哪個字數寬」），或拿稿件對照已選定的期刊，是 `submit-to`。

## Step 0 — 稿件側寫與使用者條件

先讀稿件（若有），能推得出的不要問；只問推不出的：偏好、預算、職涯考量。

| 項目 | 內容 |
|---|---|
| 貢獻類型 | 理論／方法／應用／軟體，可複選；哪一項是主軸 |
| 核心主張 | 一句可檢驗的話（Step 3.5 要用） |
| 關鍵概念 | 3–6 個主題詞**加上同義詞**（Step 3 的查詢詞） |
| 稿件現況 | 長度（照稿件自己的單位）、有無證明、模擬、真實資料、可公開的程式 |
| 使用者條件 | 分成**必須**與**偏好**。只有能直接對照語料庫欄位的條件才可能是「必須」：費用上限、審稿制度、preprint 政策、審稿速度。「哪個領域要認可這篇」「特別想上的期刊」一律是偏好，在 Step 5 處理 |

## Step 1 — 候選清單

- 使用者點名的期刊，加上語料庫中同一 `family` 的期刊；需要時加入相鄰 family。**「相鄰」是你的判斷**，要列出選了哪些、沒選哪些。
- **每一本都必須有語料庫記錄。** 沒有就先跑 `add-venue`。`add-venue` 收錄失敗的期刊列為「未收錄，無法比較」，**不算淘汰**，也不得用記憶補規定。
- 排序可以讀快照；但 **(a) 回報任何淘汰之前，對被淘汰的期刊跑 `verify.py`；(b) 使用者要開始為第一志願改稿之前，對它跑 `verify.py`**（使用者會據此動筆，屬於 `submit-to` Step 0 的嚴格情境）。每筆都報 `last_verified_at`。`verify.py` 回 `NEEDS_AGENT` 或 `BASELINE` 都**不等於「未變動」**：自己打開被引用的那一頁，確認原文仍在，並報出確認日期。

## Step 2 — 硬性淘汰（只用官方文字）

**只有以下四類可以淘汰一本期刊，不得依性質相似類推第五類：**

1. **範圍明文排除。** 官方文字**不附條件地**排除這類稿件。附條件或保留語氣的文字**不算第 1 類**，一律進 Step 4 當代價。校準（措辭取自現有記錄）：

   | 算第 1 類（不附條件） | 不算第 1 類（保留語氣，進 Step 4） |
   |---|---|
   | 「... are not acceptable」「... are not suitable for Series C」「... are not appropriate」「We do not publish ...」 | 「typically unsuitable unless」「may be inappropriate」「discouraged ... unless」「likely to be rejected」「likely to be assigned a lower priority ... unless」「find a better home」「generally not interested」 |

   判斷的對象是**論文的定位**（它要回答什麼問題、由什麼驅動），不是作者手上目前有的材料；使用者能改變定位時（例：補上真正驅動研究的應用），從 Step 2 重新判斷。必須引用原文、`src` 與 `last_verified_at`。
2. **篇幅確定放不下。** 稿件的核心內容在該刊的原生單位下確定超出上限。不得換算單位來湊結論；無法確定時不淘汰，改列為 Step 4 的代價。篇幅可能記在 `requirements.length`、`requirements.length_by_type`、`requirements.article_types[].length` 或 `requirements.article_types[].limits`——四處都要看。
3. **稿件無法滿足的強制要求。** 作者確定**做不到**（例：資料依法不能提供，而該刊無例外條款）。「還沒做」不算。
4. **使用者的「必須」條件被違反**，且該條件屬於**以下四種之一**：費用、審稿制度、preprint 政策、審稿速度。其他條件（開放取用、LaTeX、語言……）一律是偏好。欄位是 `not_published`，或官方統計量的形式和條件不同（例：條件是「兩個月內有首次決定」，官方給的是平均天數）時，**無法判定，不淘汰**，列入輸出第 8 項。

範圍風險不論寫了幾句，都不是淘汰理由。被淘汰的期刊照樣列在輸出裡，附原文、來源與 `last_verified_at`。

## Step 3 — 主題契合度：看期刊實際刊了什麼

先不設年份，看全部年代的趨勢；需要時再用 `--since` 放大近年：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/venue_topic_scan.py --venue <venue-id> \
  --term "<主題詞>" --term "<同義詞>" [--pair '<正則，例 estimat\w*>']
```

腳本會先確認 ISSN 在 OpenAlex 對得到期刊，對不到就中止，不會回報假的「零篇」。多字詞預設以**片語**比對；`--loose` 改成「各字都出現即算」，數字會明顯變大，兩者不可混用。

### 判讀原則

**原則一：主題契合以刊出的論文為準，明文排除以官方文字為準。** 範圍寫「no restrictions on the area of statistics」，不代表每個主題同等受歡迎；範圍沒提到某個領域，也不代表不收。要看的是：這個主題在該刊的篇數與**依年代的趨勢**、近年例子**用什麼問題框架**收它。那個框架就是稿件的定位指南。刊出的論文與明文排除衝突時（明文排除，卻刊過類似論文），兩者都報給使用者並標為判斷，不據此淘汰，也不據此推翻排除。

**原則二：看主題通常跟什麼一起出現，但樣本要夠才下結論。** `--pair` 看得出這類論文是單獨成篇，還是總和某種東西綁在一起。**個位數不得推廣成規律**；遇到就放寬年份重查，兩個窗口結論不一致時以樣本大的為準並說明。

> 失敗紀錄（2026-10）：查某統計期刊 2015 年以來標題含 identifiability 的論文，只有 2 篇，都和估計或因果效應綁在一起，於是得出「識別性論文在這裡總是搭配估計」並告訴了使用者。改查全部年份：14 篇，只有 2 篇同時含 estimat-；純識別性的先例反而在窄窗口之外。

**原則三：查詢語意要一致。** 同一個多字詞，寬鬆計法與片語計法的篇數可以差近一倍（實測同一刊同一詞：24 對 13）。比較不同期刊時用同一種計法，並在報告中寫明。

**原則四：近年例子的作者群是判斷，不是事實。** 從作者可以推測哪些研究社群在這裡發表、會不會有同領域審稿人，但輸出時標示為判斷。

**限制要連同數字一起告訴使用者**：只掃標題、同義詞要自己多下 term、OpenAlex 的期刊歸屬偶有錯置、超過上限時年代分布只算抓到的那些。

## Step 3.5 — 比對最接近的前人結果

排序之前，先確認稿件的**核心主張**有沒有人發表過。每一本候選期刊的審稿人都會拿最接近的前人結果來比；差異沒講清楚，排序沒有意義。

1. 用 Step 0 那句可檢驗的核心主張。
2. 從 Step 3 掃到的近年例子、稿件已引用的文獻、以及頂尖期刊（含不在候選內的）找出最接近的二到五篇。
3. **讀原文的摘要或定理，不憑記憶描述。** 取不到原文就標「未查證」。
4. 逐篇寫出：它證了什麼、前提是什麼、稿件的主張在哪些前提上比它弱或比它多。
5. 主張的主要情形已被涵蓋時，**直接告訴使用者**，並把推薦改為「先重新定位，再排序」。

文獻要歸檔時交給文獻庫的工具（例如 akashic-bootstrap），不要只留在對話裡。

> 失敗紀錄（2026-10）：一次選刊中，使用者原本認為主張「目前所有方法都做不到」；比對後發現核心主張的主要情形已有前人結果。這改變的是稿件定位，比選哪本期刊影響更大，而它是在比較期刊的過程中才出現的。

## Step 4 — 每本要付的代價

對 Step 2 留下的每本期刊，從記錄讀出稿件要付出什麼才合格（路徑以實際記錄為準，各刊結構不完全相同）：

| 記錄欄位 | 轉成的代價 |
|---|---|
| `requirements.scope.*`（含 `evaluation_criteria`、`out_of_scope_hints`，有些刊放在 section 子節點下） | 要怎麼重新定位、要補什麼論證；Step 2 不算第 1 類的保留語氣文字也在這裡 |
| `requirements.length`、`requirements.length_by_type`、`requirements.article_types[].length`、`requirements.article_types[].limits` | 要刪多少、什麼移到補充材料 |
| `requirements.openness`、`requirements.reproducibility` | 要準備的程式碼、資料與表單，以及在哪個階段交 |
| `requirements.review`、`requirements.policies.preprints` | 雙盲期刊與既有或計畫中的 preprint 是否衝突 |
| `requirements.fees` | 必付或選付、金額、機構協議 |
| `identity.metrics.*` | 只引用官方公布、附 `as_of` 或年度的值。**IF 與分區（Q）每本都要有**：分區取 `quartiles`，並標明系統——JCR（Clarivate）與 SJR（SCImago）是不同的統計量，不混用、不互換；查不到寫「未取得」，不可憑記憶補 |
| `warnings` | 一律複述給使用者 |

結合 Step 3、3.5 的證據，寫出每本的「定位與補強清單」。

## Step 5 — 排序與投稿順序

1. **先寫出前提**：稿件內容的假設（例：「假設補得出真實資料與模擬」）與使用者條件，逐條列出。
2. **前提一變就從 Step 2 重跑，並說明改了哪個前提。** 不要讓舊推薦在新前提下靜默留著。

   > 失敗紀錄（2026-10）：同一篇理論稿件的推薦在一次對話裡翻了三次——沒有真實資料時推不要求應用驅動的期刊；使用者說補得出模擬與資料後，改推要求應用驅動但篇幅足夠的期刊；使用者補充投稿偏好、掃描證據也顯示主題常見後，又換了一次第一順位。每一次翻轉都對，前提是把原因講清楚。

3. **投稿順序的考量**（依序檢查）：
   - 不可一稿多投，順序本身就是策略。
   - 首次決定時間：**只有同一種統計量才能比**（平均天數不能和「某比例在一個月內」比）；`not_published` 不推論。比不了就照實說，不拿它排序。
   - 篇幅緊的先投：短版擴寫成長版比反向容易。
   - 雙盲期刊在後面時，要先決定 preprint 放不放、何時放。
   - 使用者特別想上的期刊，只要沒有在 Step 2 被淘汰，就排進順序並說明勝算與代價。
4. **保留但沒排進順序的期刊，逐本寫出理由並標為判斷。** 不能讓它們無聲消失。理由**不得**是 Step 2 或原則一已排除的那幾種（例：「官網沒提到這個領域」「範圍風險」），而且要寫出**在什麼條件下它會排進順序**。
5. **寫出翻盤條件**：「若 X 成立（或失敗），改為 Y」。

## 輸出格式

1. **前提**（Step 5 第 1 點）
2. **淘汰清單**：期刊、淘汰類別（Step 2 的 1–4）、官方原文、`src`、`last_verified_at`；以及「未收錄，無法比較」的期刊
3. **比較表**：只放官方事實，附 `src` 與 `last_verified_at`；判斷不放進這張表。欄位至少含收錄（SSCI／SCIE）、**IF、分區（Q，標明 JCR 或 SJR）**、接受率、首次決定、投稿到接受、APC、審稿制度、篇幅；表格可用 `scripts/venue_table.py` 從記錄直接產生
4. **主題證據**：每本的篇數、計法（片語／寬鬆）、年份窗口、查詢日、近年例子與其框架、限制
5. **最接近的前人結果**：逐篇寫它證了什麼、前提是什麼、稿件多了什麼；未查證的標出來
6. **排序與投稿順序**，附翻盤條件；保留但未排入的期刊與理由
7. **每本的定位與補強清單**
8. **官網未公布的欄位**（`not_published` / `not_found`）與仍待查證的事
9. **人的訊號**（例：編委會有與作者同單位的人）：只在回覆裡提醒使用者，**不寫進語料庫**——本 repo 是公開的

## Step 6 — 問要不要產生報告

輸出完成後，**問一次**：要不要把這份結果做成 `.tex` 與 PDF 報告（含逐刊優缺與比較表）？

- 要 → 呼叫 `venue-report`；它只排版，不重新判斷。
- 不要，或使用者沒回應 → 到此為止，**不自動產生**。
- 非互動（unattended）情境不問、不產生。

為什麼是問而不是預設產生：報告含稿件細節與使用者偏好，產生它是一個要使用者決定存放位置的動作；多數情況在對話裡讀結果就夠了。

## 鐵律

- 規定只讀語料庫；主題契合只讀刊出的論文；推薦標明是判斷。
- 淘汰只有 Step 2 的四類；範圍風險不論幾句都不是淘汰理由；範圍寫「不限」也不代表契合。
- 個位數的樣本不推廣成規律；不同計法的數字不混用。
- 排序之前先比對最接近的前人結果；主張已被涵蓋時直接說，不為了讓排序好看而淡化。
- 前提改變必須從 Step 2 重跑，並說出改了哪個前提。
- 私人資訊（作者、合作者、同事姓名、未發表稿件的內容與投稿偏好）不寫進語料庫或本 skill 的範例。

虛構化的精簡範例（只示範 Step 2、3、3.5、5 的判讀）見 [`references/example-theory-paper.md`](references/example-theory-paper.md)。
