#!/usr/bin/env python3
"""從語料庫記錄產生期刊比較表（官方事實欄位），不手抄。

用法:
  python3 scripts/venue_table.py wiley/journal-of-consumer-psychology elsevier/journal-of-business-research
  python3 scripts/venue_table.py --format latex --order-file order.txt
  python3 scripts/venue_table.py --root /path/to/plugin --format markdown <id> <id> ...

輸出欄位：收錄、IF、分區（Q）、接受率、首次決定（中位）、投稿→接受（中位）、APC、審稿、篇幅。

設計：
- 每個值都直接來自記錄；讀不到就印「?」並在 stderr 警告，**不猜、不補**。
  「?」代表「記錄的結構這支腳本認不得」，不是「官方未公布」；官方未公布會印「未公布」。
- 記錄是由不同人／代理寫的，欄位名稱不完全一致，所以這裡容忍已知的別名（見 ALIASES）。
  遇到新的寫法請補別名，或把記錄改成 skills/venue-report/SKILL.md 定義的標準欄位。
- 口徑（平均或中位數、哪一年）只在記錄有寫時才附；不同出版社的口徑不同，表格不替你換算。
"""
import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
NOTES = []   # (id, 欄位, 說明)；有附註的格子會加 † 或 ‡
UNKNOWN = "?"
NOT_PUBLISHED = "未公布"

# 標準欄位 -> 已知別名（依序嘗試）
ALIASES = {
    "first_decision": ["time_to_first_decision"],
    "sub_to_accept": ["time_submission_to_acceptance", "submission_to_acceptance", "time_to_acceptance"],
}

REVIEW_LABEL = {
    "double_anonymized": "雙匿名",
    "double_blind": "雙盲",
    "single_anonymized": "單匿名",
    "single_blind": "單盲",
    "single_anonymized_interactive": "單匿名＋互動式",
}


def load(venue_id, root):
    path = Path(root) / "venues" / f"{venue_id}.yaml"
    if not path.exists():
        sys.exit(f"✗ 找不到記錄 {path}（先用 add-venue 收錄）")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def get(d, *keys):
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def is_unknown(v):
    return isinstance(v, dict) and "status" in v and "value" not in v


def num(v):
    return v.get("value", v.get("value_days")) if isinstance(v, dict) else v


def fmt_int(n):
    return f"{n:,}" if isinstance(n, (int, float)) and float(n).is_integer() else str(n)


# ---------------------------------------------------------------- 收錄
def wos(rec):
    ind = get(rec, "identity", "indexing") or get(rec, "identity", "metrics", "indexing") or {}
    ssci = scie = None
    cw = ind.get("clarivate_wos")
    if isinstance(cw, dict) and isinstance(cw.get("in_ssci"), dict):
        ssci = bool(cw["in_ssci"].get("value"))
        scie = bool((cw.get("in_scie") or {}).get("value"))
    elif isinstance(ind.get("wos_ssci_scie"), dict):
        w = ind["wos_ssci_scie"]
        ssci = "SSCI" in str(w.get("value"))
        scie = bool(w.get("scie")) or "SCIE" in str(w.get("value"))
    else:
        m = ind.get("clarivate_mjl")
        if isinstance(m, dict):
            if "ssci" in m or "scie" in m:
                ssci, scie = bool(m.get("ssci")), bool(m.get("scie"))
            col = str(m.get("web_of_science_core_collection", ""))
            if col:
                ssci = ssci or "Social Sciences Citation Index" in col
                scie = scie or "Science Citation Index Expanded" in col
    if ssci is None and scie is None:
        return UNKNOWN
    parts = (["SCIE"] if scie else []) + (["SSCI"] if ssci else [])
    return "＋".join(parts) if parts else "兩者皆無"


# ---------------------------------------------------------------- 指標
def impact_factor(m):
    v = m.get("impact_factor")
    if v is None:
        return UNKNOWN
    if is_unknown(v):
        return NOT_PUBLISHED
    n = num(v)
    return f"{n}" if n is not None else UNKNOWN


def quartile(m):
    q = m.get("quartiles")
    if q is None:
        r = get(m, "jcr_category_rank", "ranks")
        if r:
            q = [{"system": "JCR", "quartile": x.get("quartile"), "category": x.get("category")} for x in r]
        else:
            return UNKNOWN
    if isinstance(q, dict):
        return "未取得"
    if not q:
        return "未取得"
    for system in ("JCR", "SJR"):
        qs = sorted({x.get("quartile") for x in q if x.get("system") == system and x.get("quartile")})
        if qs:
            return f"{'／'.join(qs)}（{system}）"
    return UNKNOWN


def quartile_detail(m):
    """各學科類別的分區與名次，例：Business Q1（48/323，JCR 2025）。給逐刊段落用。"""
    q = m.get("quartiles")
    if not isinstance(q, list):
        return []
    best = {}   # 同一系統、同一類別、同一分區只留一筆；有名次的優先（出版社轉載常與直接讀到的重複）
    for x in q:
        if not x.get("quartile"):
            continue
        cat = str(x.get("category", "")).lower().replace("&", "and")
        key = (x.get("system"), " ".join(cat.split()), x["quartile"])
        if key not in best or (x.get("rank") and not best[key].get("rank")):
            best[key] = x
    out = []
    for x in best.values():
        rank = f"{x['rank']}，" if x.get("rank") else ""
        out.append(f"{x.get('category')} {x['quartile']}（{rank}{x.get('system')} {x.get('year', '')}）".replace(" ）", "）"))
    return out


def acceptance(m):
    v = m.get("acceptance_rate")
    if v is None:
        return UNKNOWN
    if isinstance(v, dict) and "insights_page" in v:        # 例：JEP，社論的世代數字
        sub = v.get("editorial_2023_cohort") or {}
        if "value" in sub:
            return f"{fmt_int(sub['value'])}%（{sub.get('cohort', '2023 年投稿世代')}，社論）"
        v = v["insights_page"]
    if is_unknown(v):
        rej = get(m, "rejection_rate", "by_year")
        if rej:
            last = rej[0]
            return f"{NOT_PUBLISHED}（拒絕率 {last['year']}：{fmt_int(last['value_percent'])}%）"
        return NOT_PUBLISHED
    n = num(v)
    if n is None:
        return UNKNOWN
    s = str(n)
    if not s.endswith("%"):
        s += "%"
    y = v.get("year") if isinstance(v, dict) else None
    return f"{s}（{y}）" if y else s


EST_KEYS = {"sub_to_accept": "sub_to_acceptance"}


def estimate_or_unpublished(m, key):
    """官方未公布時，若記錄有自行抽樣估計（identity.metrics.estimates），顯示「未公布（自行估計…‡）」。
    估計與官方數字必須一眼分得出來，所以一定帶 ‡ 與附註，絕不直接印成官方欄位的數字。"""
    e = (m.get("estimates") or {}).get(EST_KEYS.get(key, ""))
    if not e or "value" not in e:
        return NOT_PUBLISHED
    NOTES.append((m.get("_id", "?"), "估計",
                  f"‡ 自行抽樣估計，不是官方統計：{e.get('method', '')} 樣本 n={e.get('n')}；"
                  f"四分位 {fmt_int(e.get('q1'))}–{fmt_int(e.get('q3'))} 天；限制：{'；'.join(e.get('caveats', [])[:2])}"))
    return f"{NOT_PUBLISHED}（自行估計中位約 {e['value']:g} 天‡）"


def duration(m, key):
    for k in ALIASES[key]:
        if k in m:
            v = m[k]
            if is_unknown(v):
                return estimate_or_unpublished(m, key)
            n = num(v)
            if n is None:
                return UNKNOWN
            s = f"{fmt_int(n)} 天"
            if isinstance(v, dict):
                tag = v.get("period") or v.get("year")
                if isinstance(tag, (str, int)) and tag and str(tag) not in ("not_published", "not_found", "not_applicable"):
                    s += f"（{str(tag).split('（')[0]}）"
            return s
    return UNKNOWN


# ---------------------------------------------------------------- 費用、審稿、篇幅
def apc(rec):
    fees = get(rec, "requirements", "fees") or {}
    a = fees.get("apc")
    if not isinstance(a, dict):
        return UNKNOWN
    cur = a.get("currency") or fees.get("currency")
    amt = a.get("amount")
    if isinstance(amt, dict):
        cur, amt = "USD", amt.get("usd")
    if amt is None:
        for k in ("all_other_articles", "a_type"):
            if isinstance(a.get(k), dict):
                amt = a[k].get("amount")
                cur = a[k].get("currency") or cur
                break
    if amt is None:
        return UNKNOWN
    cur = str(cur or "").split("（")[0].strip()[:3]
    if a.get("mandatory") is False or a.get("status") == "optional":
        kind = "選付"
    elif a.get("mandatory") is True or str(a.get("status", "")).startswith("mandatory"):
        kind = "必付"
    elif get(rec, "identity", "open_access"):
        kind = "必付"
    else:
        kind = UNKNOWN
    return f"{cur} {fmt_int(amt)}（{kind}）"


def review(rec):
    t = get(rec, "requirements", "review", "type")
    return REVIEW_LABEL.get(t, UNKNOWN if t is None else str(t))


def length(rec):
    req = rec.get("requirements") or {}
    L = req.get("length") or req.get("length_policy") or req.get("length_note")
    if not isinstance(L, dict):
        return UNKNOWN
    if L.get("limit") == "none_stated_as_unlimited" or get(L, "word_limit", "status") == "not_applicable":
        return "無上限"
    if is_unknown(L):
        return NOT_PUBLISHED
    rng = L.get("recommended_range")
    unit = L.get("unit")
    if rng and unit == "words":
        return f"建議 {fmt_int(rng[0])}–{fmt_int(rng[1])} 字"
    v = L.get("value")
    if v is None:
        return UNKNOWN
    if unit == "words":
        out = f"{fmt_int(v)} 字"
    elif unit and unit.startswith("pages"):
        out = f"{fmt_int(v)} 頁雙行距"
    else:
        out = f"{fmt_int(v)} {unit or ''}".strip()
    note = str(L.get("note") or L.get("exceptions") or "")
    if any(w in note for w in ("單一研究", "多研究", "Research Report", "其他類型")):
        NOTES.append((rec["id"], "篇幅", note))
        out += "†"
    return out


PUBLISHER_SHORT = [("elsevier", "Elsevier"), ("wiley", "Wiley"), ("springer", "Springer Nature"), ("mdpi", "MDPI"),
                   ("multidisciplinary digital", "MDPI"), ("frontiers", "Frontiers"), ("public library of science", "PLOS"),
                   ("plos", "PLOS"), ("american psychological", "APA"), ("sage", "SAGE"), ("taylor", "Taylor & Francis"),
                   ("oxford", "OUP"), ("cambridge", "CUP")]


def publisher(rec):
    p = str(get(rec, "identity", "publisher") or "")
    low = p.lower()
    for k, v in PUBLISHER_SHORT:
        if k in low:
            return v
    return p.split("（")[0].strip() or UNKNOWN


DISCOUNTS = {}   # venue id -> 文字；由 --discounts 檔提供（機構專屬資料，不屬於期刊記錄）


def row(rec):
    m = get(rec, "identity", "metrics") or {}
    m = {**m, "_id": rec["id"]}
    return {
        "id": rec["id"],
        "publisher": publisher(rec),
        "discount": DISCOUNTS.get(rec["id"], "—") if DISCOUNTS else None,
        "name": get(rec, "identity", "name") or rec["id"],
        "index": wos(rec),
        "if": impact_factor(m),
        "q": quartile(m),
        "accept": acceptance(m),
        "first": duration(m, "first_decision"),
        "sub_accept": duration(m, "sub_to_accept"),
        "apc": apc(rec),
        "review": review(rec),
        "length": length(rec),
    }


COLS = [("name", "期刊"), ("publisher", "出版社"), ("index", "收錄"), ("if", "IF"), ("q", "分區"), ("accept", "接受率"),
        ("first", "首次決定（中位）"), ("sub_accept", "投稿→接受（中位）"), ("apc", "APC"),
        ("discount", "機構折扣"), ("review", "審稿"), ("length", "篇幅")]


def tex(s):
    s = str(s)
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"),
                 ("_", r"\_"), ("→", r"$\to$")):
        s = s.replace(a, b)
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*", help="venue id，例 wiley/journal-of-consumer-psychology")
    ap.add_argument("--order-file", help="每行一個 venue id；決定列的順序（# 開頭為註解，空行略過）")
    ap.add_argument("--root", default=str(ROOT), help="含 venues/ 的外掛根目錄（預設為本外掛）")
    ap.add_argument("--discounts", help="JSON 檔：{venue-id: 文字}。機構專屬的 APC 折扣或合約資訊（例如某校與出版社的協議），"
                    "不屬於期刊記錄，所以由外部提供；有給才多一欄「機構折扣」")
    ap.add_argument("--format", choices=["markdown", "latex", "json", "quartiles"], default="markdown")
    a = ap.parse_args()

    if a.discounts:
        DISCOUNTS.update(json.loads(Path(a.discounts).read_text(encoding="utf-8")))
    ids = list(a.ids)
    if a.order_file:
        ids += [l.strip() for l in Path(a.order_file).read_text(encoding="utf-8").splitlines()
                if l.strip() and not l.lstrip().startswith("#")]
    if not ids:
        sys.exit("✗ 沒有 venue id")

    global COLS
    if not DISCOUNTS:
        COLS = [c for c in COLS if c[0] != "discount"]
    rows = [row(load(i, a.root)) for i in ids]
    bad = [(r["id"], label) for r in rows for k, label in COLS if r[k] == UNKNOWN or UNKNOWN in str(r[k])]
    for vid, label in bad:
        print(f"⚠ {vid}：「{label}」讀不出來（記錄結構認不得，不是官方未公布）— 請查記錄或補別名", file=sys.stderr)

    notes = [(f"{i} {k}：{n}" if k == "估計" else f"† {i} {k}：{n[:140]}") for i, k, n in NOTES]
    if a.format == "quartiles":
        for i in ids:
            m = get(load(i, a.root), "identity", "metrics") or {}
            print(i + "\t" + "；".join(quartile_detail(m)))
        return
    if a.format == "json":
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    elif a.format == "markdown":
        print("| " + " | ".join(l for _, l in COLS) + " |")
        print("|" + "|".join(["---"] * len(COLS)) + "|")
        for r in rows:
            print("| " + " | ".join(str(r[k]) for k, _ in COLS) + " |")
        for n in notes:
            print(f"\n{n}")
    else:
        for r in rows:
            print(" & ".join(tex(r[k]).replace("†", r"\textsuperscript{†}").replace("‡", r"\textsuperscript{‡}") for k, _ in COLS) + r" \\")
        for n in notes:
            print("% " + n)


if __name__ == "__main__":
    main()
