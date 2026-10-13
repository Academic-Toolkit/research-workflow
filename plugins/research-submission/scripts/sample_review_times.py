#!/usr/bin/env python3
"""官方沒有公布「投稿到接受」時，從已刊出文章的 Received／Accepted／Published 日期自行估計。

**這是自己的抽樣估計，不是官方統計**：只含最後被刊出的稿件，看不到被拒稿；樣本是「某段期間刊出」的文章，
不是「某段期間投稿」的稿件；各刊的 Received 是否等於首次投稿日，需要看該刊對這個欄位的說明。
結果寫進記錄時必須放在 identity.metrics.estimates（不是官方欄位），並註明方法與限制。

用法:
  # 一般出版社頁面（curl 可抓）
  python3 scripts/sample_review_times.py --issn 1664-1078 --journal-path journals/psychology --preset frontiers --year 2025 --n 200
  python3 scripts/sample_review_times.py --issn 1932-6203 --preset plos --from-date 2023-01-01 --until-date 2023-06-30 --n 200
  # 生醫收錄、Europe PMC 有全文 XML 的期刊
  python3 scripts/sample_review_times.py --issn 2076-328X --preset europepmc --year 2025 --n 200
  # 擋 curl 的出版社（MDPI）：用 safari-browser，會開一個專用視窗，結束時關掉
  python3 scripts/sample_review_times.py --issn 2071-1050 --preset mdpi-safari --year 2025 --n 100

抽樣：Crossref 以 ISSN 隨機抽樣（sample 參數，每次最多 100 篇）；europepmc 則先列出該期間所有開放全文的 PMCID，
再以 --seed 隨機抽（可重現）。輸出投稿到接受的中位數、四分位、10–90 百分位與樣本數。

preset（驗證日 2026-10-13）：
  frontiers    文章頁 <p class="h5">Received</p><p>10 January 2025</p>
  plos         文章頁 "Received: </strong>January 12, 2025;"；刊出日取 Crossref
  europepmc    全文 XML 的 history 段 "Received 2025 Nov 10; Revised …; Accepted 2025 Dec 27"；刊出日取檢索結果的 firstPublicationDate。
               限制：只涵蓋 PMC 收錄的開放全文，覆蓋率與延遲可能造成偏差
  mdpi-safari  mdpi.com 對 curl 回 403，故用 safari-browser（網址必須是 https://www.mdpi.com/ 或 mdpi.com，其他主機一律拒絕）：頁面文字 "Received:\\n19 December 2024\\n…Accepted:\\n…Published:\\n…"
其他出版社先用 --n 5 試跑，n_parsed 要等於 n_sampled 才放大。
"""
import argparse
import json
import math
import random
import re
import statistics
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime

UA = {"User-Agent": "Mozilla/5.0 (research-notes)"}

CURL_PRESETS = {
    "frontiers": {
        "url": "https://www.frontiersin.org/{journal_path}/articles/{doi}/full",
        "received": r'<p class="h5">Received</p><p>(\d{1,2} \w+ \d{4})</p>',
        "accepted": r'<p class="h5">Accepted</p><p>(\d{1,2} \w+ \d{4})</p>',
        "published": r'<p class="h5">Published</p><p>(\d{1,2} \w+ \d{4})</p>',
        "fmt": "%d %B %Y",
    },
    "plos": {
        "url": "https://journals.plos.org/plosone/article?id={doi}",
        "received": r"Received: </strong>([A-Za-z]+ \d{1,2}, \d{4})",
        "accepted": r"Accepted: </strong>([A-Za-z]+ \d{1,2}, \d{4})",
        "published": None,           # 取 Crossref 的刊出日
        "fmt": "%B %d, %Y",
    },
}
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"


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


def crossref_sample(issn, d0, d1, n):
    items = []
    for _ in range(max(1, -(-n // 100))):
        q = urllib.parse.urlencode({"filter": f"from-pub-date:{d0},until-pub-date:{d1},type:journal-article",
                                    "sample": 100, "select": "DOI,issued,resource"})
        j = get(f"https://api.crossref.org/journals/{issn}/works?{q}")
        if j:
            items += json.loads(j)["message"]["items"]
        time.sleep(2)
    seen, out = set(), []
    for i in items:
        if i["DOI"] not in seen:
            seen.add(i["DOI"])
            dp = i["issued"]["date-parts"][0] + [1, 1]
            out.append({"doi": i["DOI"], "pub": datetime(dp[0], dp[1], dp[2]),
                        "landing": (i.get("resource") or {}).get("primary", {}).get("URL")})
    return out[:n]


def epmc_sample(issn, d0, d1, n, seed):
    q = f'ISSN:"{issn}" AND FIRST_PDATE:[{d0} TO {d1}] AND OPEN_ACCESS:y AND HAS_FT:y'
    cursor, allr = "*", []
    while True:
        u = f"{EPMC}/search?" + urllib.parse.urlencode({"query": q, "format": "json", "pageSize": 1000,
                                                       "resultType": "lite", "cursorMark": cursor})
        r = json.loads(get(u))
        res = r["resultList"]["result"]
        allr += [x for x in res if x.get("pmcid")]
        nxt = r.get("nextCursorMark")
        if not res or not nxt or nxt == cursor:
            break
        cursor = nxt
    random.Random(seed).shuffle(allr)
    return allr[:n], len(allr)


# ---- Safari（MDPI）-----------------------------------------------------------------
def sf(*args, timeout=60):
    p = subprocess.run(["safari-browser", *args], capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


JS_EXTRACT = (r"var t=document.body.innerText;function g(k){var m=t.match(new RegExp(k+':\\s*\\n(\\d{1,2} \\w+ \\d{4})'));"
              r"return m?m[1]:''};return g('Received')+'|'+g('Accepted')+'|'+g('Published')")


ALLOWED_BROWSER_HOSTS = {"mdpi-safari": ("www.mdpi.com", "mdpi.com")}


def safe_landing(url, preset):
    """Crossref 的 resource 欄位是出版社自填的，不可信。要交給有登入的 Safari 之前，必須是 https 且主機在白名單內，
    否則一個被竄改的紀錄就能讓使用者的瀏覽器導向任意網站並在上面執行 JavaScript。"""
    u = urllib.parse.urlparse(url or "")
    if u.scheme != "https" or u.hostname not in ALLOWED_BROWSER_HOSTS.get(preset, ()):
        raise ValueError(f"landing url not allowed: {url!r}")
    return url


def human_delay():
    time.sleep(min(15, max(2.0, 3 + math.tan(math.pi * (random.random() - 0.5)) * 0.8)))


def safari_dates(url, lock):
    sf("js", f"location.href={json.dumps(url)}", *lock)
    path = urllib.parse.urlparse(url).path
    for _ in range(25):
        time.sleep(1)
        rc, out, _ = sf("js", "return document.readyState+'|'+location.pathname", *lock)
        if rc == 0 and out.startswith("complete") and out.endswith(path):
            break
    else:
        return None
    rc, out, _ = sf("js", JS_EXTRACT, *lock)
    parts = out.split("|") if rc == 0 else []
    if len(parts) != 3 or not all(parts):
        return None
    return [datetime.strptime(p, "%d %B %Y") for p in parts]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--issn", required=True)
    ap.add_argument("--preset", required=True, choices=sorted(CURL_PRESETS) + ["europepmc", "mdpi-safari"])
    ap.add_argument("--year", type=int)
    ap.add_argument("--from-date")
    ap.add_argument("--until-date")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed", type=int, default=20261013, help="europepmc 抽樣用，可重現")
    ap.add_argument("--journal-path", help="frontiers 用，例 journals/psychology")
    ap.add_argument("--delay", type=float, default=1.2)
    ap.add_argument("--out")
    a = ap.parse_args()
    d0 = a.from_date or (f"{a.year}-01-01" if a.year else None)
    d1 = a.until_date or (f"{a.year}-12-31" if a.year else None)
    if not (d0 and d1):
        sys.exit("✗ 要給 --year，或 --from-date 與 --until-date")

    rows, failed, total_pool = [], [], None
    lock = ["--url", "https://www.mdpi.com/"]   # 以完整主機前綴鎖定，避免子字串誤中其他網站

    if a.preset == "europepmc":
        sample, total_pool = epmc_sample(a.issn, d0, d1, a.n, a.seed)
        print(f"pool {total_pool}, sampled {len(sample)}", file=sys.stderr)
        pat = re.compile(r"Received (\d{4} \w{3} \d{1,2}).*?Accepted (\d{4} \w{3} \d{1,2})", re.S)
        for k, x in enumerate(sample, 1):
            h = get(f"{EPMC}/{x['pmcid']}/fullTextXML")
            time.sleep(0.4)
            try:
                m = pat.search(h)
                r_, a_ = (datetime.strptime(m.group(i), "%Y %b %d") for i in (1, 2))
                p_ = datetime.strptime(x["firstPublicationDate"], "%Y-%m-%d")
                rows.append({"id": x["pmcid"], "sub_to_acc": (a_ - r_).days, "acc_to_pub": (p_ - a_).days,
                             "received": r_.strftime("%Y-%m-%d")})
            except Exception:
                failed.append(x["pmcid"])
            if k % 50 == 0:
                print(k, file=sys.stderr)
    else:
        sample = crossref_sample(a.issn, d0, d1, a.n)
        print(f"sampled {len(sample)}", file=sys.stderr)
        opened = False
        consecutive_fail = 0
        try:
            for k, x in enumerate(sample, 1):
                try:
                    if a.preset == "mdpi-safari":
                        landing = safe_landing(x["landing"], a.preset)
                        if not opened:
                            sf("open", landing, "--new-window")
                            opened = True
                            time.sleep(4)
                        t = safari_dates(landing, lock)
                        if not t:
                            raise ValueError("no dates")
                        r_, a_, p_ = t
                        human_delay()
                    else:
                        p = CURL_PRESETS[a.preset]
                        h = get(p["url"].replace("{journal_path}", a.journal_path or "").replace("{doi}", x["doi"]))
                        time.sleep(a.delay)
                        r_ = datetime.strptime(re.search(p["received"], h).group(1), p["fmt"])
                        a_ = datetime.strptime(re.search(p["accepted"], h).group(1), p["fmt"])
                        p_ = (datetime.strptime(re.search(p["published"], h).group(1), p["fmt"])
                              if p["published"] else x["pub"])
                    rows.append({"id": x["doi"], "sub_to_acc": (a_ - r_).days, "acc_to_pub": (p_ - a_).days,
                                 "received": r_.strftime("%Y-%m-%d")})
                    consecutive_fail = 0
                except Exception:
                    failed.append(x["doi"])
                    consecutive_fail += 1
                    if consecutive_fail >= 8:
                        print("✗ 連續 8 篇失敗，中止（檢查頁面格式或是否被擋）", file=sys.stderr)
                        break
                if k % 25 == 0:
                    print(k, file=sys.stderr)
        finally:
            if a.preset == "mdpi-safari" and opened:
                sf("close", *lock)       # 只關我們開的 mdpi 視窗（以 https://www.mdpi.com/ 前綴鎖定）

    if not rows:
        sys.exit("✗ 一篇也解析不出來：檢查網址或日期樣式、出版社是否擋掉 curl（回 403 就改用 safari-browser）")
    s = [r["sub_to_acc"] for r in rows]
    ap_ = [r["acc_to_pub"] for r in rows]
    out = {
        "issn": a.issn, "preset": a.preset, "published_from": d0, "published_until": d1,
        "queried": time.strftime("%Y-%m-%d"),
        "n_sampled": len(rows) + len(failed), "n_parsed": len(rows), "n_failed": len(failed),
        "pool_size": total_pool, "seed": a.seed if a.preset == "europepmc" else None,
        "received_range": [min(r["received"] for r in rows), max(r["received"] for r in rows)],
        "sub_to_acceptance_days": {"median": statistics.median(s), "q1": quantile(s, .25), "q3": quantile(s, .75),
                                   "p10": quantile(s, .10), "p90": quantile(s, .90), "min": min(s), "max": max(s)},
        "acceptance_to_publication_days": {"median": statistics.median(ap_), "q1": quantile(ap_, .25),
                                           "q3": quantile(ap_, .75)},
        "caveats": ["自行抽樣估計，不是官方統計", "只含最後被刊出的稿件，看不到被拒稿",
                    "樣本是某段期間刊出的文章，不是某段期間投稿的稿件", "Received 是否等於首次投稿日需看出版社說明"],
    }
    if failed:
        print(f"⚠ {len(failed)} 篇解析失敗（見輸出檔 failed）", file=sys.stderr)
    if a.out:
        json.dump({**out, "rows": rows, "failed": failed}, open(a.out, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
