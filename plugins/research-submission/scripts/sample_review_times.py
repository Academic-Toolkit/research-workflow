#!/usr/bin/env python3
"""官方沒有公布「投稿到接受」時，從已刊出文章頁的 Received／Accepted／Published 日期自行估計。

**這是自己的抽樣估計，不是官方統計**：只含最後被刊出的稿件，看不到被拒稿；樣本是「某一年刊出」的文章，
不是「某一年投稿」的稿件；各刊的 Received 是否等於首次投稿日，需要看該刊對這個欄位的說明。
結果寫進記錄時必須放在 identity.metrics.estimates（不是官方欄位），並註明方法與限制。

用法:
  python3 scripts/sample_review_times.py --issn 1664-1078 --journal-path journals/psychology \\
      --preset frontiers --year 2025 --n 200 --out result.json

流程：Crossref 以 ISSN 隨機抽樣（sample 參數，每次最多 100 篇，會重複抽並去重）→ 逐篇抓文章頁 →
用 preset 的樣式取出三個日期 → 輸出中位數、四分位、10–90 百分位與樣本數。
抓文章頁預設每篇間隔 1.2 秒；出版社擋 curl（例如 MDPI 回 403）時不能用本腳本，要改用 safari-browser 讀頁面。

preset：
  frontiers   已驗證（2026-10-13）：文章頁含 <p class="h5">Received</p><p>10 January 2025</p>，Accepted、Published 同形。
其他出版社請用 --received-re / --accepted-re / --published-re 自訂（各一個含一個捕捉組的正則，日期格式用 --date-format），
並先用 --n 5 試跑，確認 n_parsed 等於 n_sampled，再放大。
"""
import argparse
import json
import re
import statistics
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime

UA = {"User-Agent": "Mozilla/5.0 (research-notes)"}

PRESETS = {
    "frontiers": {
        "url": "https://www.frontiersin.org/{journal_path}/articles/{doi}/full",
        "received": r'<p class="h5">Received</p><p>(\d{1,2} \w+ \d{4})</p>',
        "accepted": r'<p class="h5">Accepted</p><p>(\d{1,2} \w+ \d{4})</p>',
        "published": r'<p class="h5">Published</p><p>(\d{1,2} \w+ \d{4})</p>',
        "date_format": "%d %B %Y",
    },
}


def get(url, retries=3):
    for a in range(retries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode("utf-8", "ignore")
        except Exception:
            time.sleep(5 * (a + 1))
    return None


def quantile(v, p):
    v = sorted(v)
    k = (len(v) - 1) * p
    f = int(k)
    c = min(f + 1, len(v) - 1)
    return v[f] + (v[c] - v[f]) * (k - f)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--issn", required=True)
    ap.add_argument("--year", type=int, required=True, help="刊出年（Crossref 的 pub-date）")
    ap.add_argument("--n", type=int, default=200, help="目標樣本數（實際會略少，去重後）")
    ap.add_argument("--preset", choices=sorted(PRESETS))
    ap.add_argument("--journal-path", help="文章頁網址中的期刊路徑，例 journals/psychology（preset 用）")
    ap.add_argument("--url-template", help="自訂文章頁網址，含 {doi}")
    ap.add_argument("--received-re")
    ap.add_argument("--accepted-re")
    ap.add_argument("--published-re")
    ap.add_argument("--date-format", default="%d %B %Y")
    ap.add_argument("--delay", type=float, default=1.2)
    ap.add_argument("--out", help="輸出 JSON 路徑（含逐篇資料）")
    a = ap.parse_args()

    if a.preset:
        p = PRESETS[a.preset]
        url_t = p["url"].replace("{journal_path}", a.journal_path or "")
        res = {k: re.compile(p[k]) for k in ("received", "accepted", "published")}
        fmt = p["date_format"]
    else:
        if not (a.url_template and a.received_re and a.accepted_re and a.published_re):
            sys.exit("✗ 沒有 --preset 時，--url-template 與三個 --*-re 都要給")
        url_t, fmt = a.url_template, a.date_format
        res = {"received": re.compile(a.received_re), "accepted": re.compile(a.accepted_re),
               "published": re.compile(a.published_re)}

    dois = []
    rounds = max(1, -(-a.n // 100))
    for _ in range(rounds):
        q = urllib.parse.urlencode({"filter": f"from-pub-date:{a.year}-01-01,until-pub-date:{a.year}-12-31,type:journal-article",
                                    "sample": 100, "select": "DOI"})
        j = get(f"https://api.crossref.org/journals/{a.issn}/works?{q}")
        if j:
            dois += [i["DOI"] for i in json.loads(j)["message"]["items"]]
        time.sleep(2)
    dois = list(dict.fromkeys(dois))[: a.n]
    print(f"sampled {len(dois)}", file=sys.stderr)

    rows, failed = [], []
    for n, d in enumerate(dois, 1):
        h = get(url_t.replace("{doi}", d))
        time.sleep(a.delay)
        try:
            t = {k: datetime.strptime(r.search(h).group(1), fmt) for k, r in res.items()}
        except Exception:
            failed.append(d)
            continue
        rows.append({"doi": d, "sub_to_acc": (t["accepted"] - t["received"]).days,
                     "acc_to_pub": (t["published"] - t["accepted"]).days,
                     "received": t["received"].strftime("%Y-%m-%d")})
        if n % 25 == 0:
            print(n, file=sys.stderr)

    if not rows:
        sys.exit("✗ 一篇也解析不出來：檢查網址樣式、日期正則，或出版社是否擋掉 curl（回 403 就改用 safari-browser）")
    s = [r["sub_to_acc"] for r in rows]
    ap_ = [r["acc_to_pub"] for r in rows]
    out = {
        "issn": a.issn, "published_year": a.year, "queried": time.strftime("%Y-%m-%d"),
        "n_sampled": len(dois), "n_parsed": len(rows), "n_failed": len(failed),
        "received_range": [min(r["received"] for r in rows), max(r["received"] for r in rows)],
        "sub_to_acceptance_days": {"median": statistics.median(s), "q1": quantile(s, .25), "q3": quantile(s, .75),
                                   "p10": quantile(s, .10), "p90": quantile(s, .90), "min": min(s), "max": max(s)},
        "acceptance_to_publication_days": {"median": statistics.median(ap_), "q1": quantile(ap_, .25), "q3": quantile(ap_, .75)},
        "caveats": ["自行抽樣估計，不是官方統計", "只含最後被刊出的稿件，看不到被拒稿",
                    "樣本是某年刊出的文章，不是某年投稿的稿件", "Received 是否等於首次投稿日需看出版社說明"],
    }
    if failed:
        print(f"⚠ {len(failed)} 篇解析失敗（見輸出檔 failed）", file=sys.stderr)
    if a.out:
        json.dump({**out, "rows": rows, "failed": failed}, open(a.out, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
