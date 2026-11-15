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
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
NOTES = []   # (id, 欄位, 說明)；有附註的格子會加 † 或 ‡
UNKNOWN = "?"
NOT_PUBLISHED = "未公布"
# 記錄的 status 值 -> 表上的字。not_found 是「查過但沒取得」（例如 JCR 要登入），
# 不是官方沒公布，兩者不可混成同一個字（#5）。
STATUS_LABEL = {
    "not_published": NOT_PUBLISHED,
    "not_found": "未取得",
    "not_applicable": "不適用",
}

# 篇幅的頁數單位 -> 表上的字。只有這兩種有定義；其他 pages_* 原樣印出單位，不猜（#5）。
PAGE_UNIT_LABEL = {
    "pages_double_spaced": "頁雙行距",
    "pages_typeset": "頁（排版後）",
}

# 標準欄位 -> 已知別名（依序嘗試）
ALIASES = {
    "first_decision": ["time_to_first_decision"],
    "sub_to_accept": ["time_submission_to_acceptance", "submission_to_acceptance", "time_to_acceptance"],
}

REVIEW_LABEL = {
    "double_anonymized": "雙匿名",
    "double_anonymous": "雙匿名",
    "double-anonymous": "雙匿名",
    "double_blind": "雙盲",
    "single_anonymized": "單匿名",
    "single_blind": "單盲",
    "single_anonymized_interactive": "單匿名＋互動式",
    "referee_anonymous": "審稿人匿名",
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


def status_label(v):
    """is_unknown 的值要印什麼：依 status 區分未公布／未取得／不適用。"""
    return STATUS_LABEL.get(v.get("status"), NOT_PUBLISHED)


def is_status_only(v):
    """只記了「查過、沒有值」的欄位。status 也有別的用法（例：APC 的 status: optional
    表示選付、旁邊另有金額），所以只認 STATUS_LABEL 的三個值，且不得帶 amount／value。"""
    return (isinstance(v, dict) and v.get("status") in STATUS_LABEL
            and "amount" not in v and "value" not in v)


def num(v):
    """欄位的值：純量照用；mapping 取 value／value_days。取出來不是數字或字串（清單、mapping…）
    就當成認不得，回 None，由呼叫端印「?」，不把 Python 的原始寫法印進表格。"""
    n = v.get("value", v.get("value_days")) if isinstance(v, dict) else v
    return n if isinstance(n, (int, float, str)) and not isinstance(n, bool) else None


def fmt_int(n):
    return f"{n:,}" if isinstance(n, (int, float)) and float(n).is_integer() else str(n)


def is_conference(rec):
    return rec.get("kind") == "conference"


# ---------------------------------------------------------------- 收錄
def wos(rec):
    ind = get(rec, "identity", "indexing")
    alt = get(rec, "identity", "metrics", "indexing")
    if ind is None or (ind == {} and alt):     # 沒寫，或空的而 metrics.indexing 有內容：改讀後者（改動前就如此）
        ind = alt
    if ind is None and is_conference(rec):     # 研討會沒有期刊收錄；有寫就照寫的印
        return STATUS_LABEL["not_applicable"]
    if is_status_only(ind):
        return status_label(ind)
    if not isinstance(ind, dict):              # 清單等認不得的形狀：印「?」，不當掉
        return UNKNOWN
    ssci = scie = None
    if "web_of_science" in ind:                # 標準寫法；有寫就由它決定，不再讀舊的鍵
        ws = ind["web_of_science"]
        if is_status_only(ws):
            return status_label(ws)
        if not (isinstance(ws, dict) and isinstance(ws.get("scie"), bool) and isinstance(ws.get("ssci"), bool)):
            return UNKNOWN                     # 旗標不是布林、缺一個、或別的形狀：不猜
        parts = (["SCIE"] if ws["scie"] else []) + (["SSCI"] if ws["ssci"] else [])
        return "＋".join(parts) if parts else "兩者皆無"
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
    if isinstance(v, (list, tuple, set)):      # 認不得的形狀
        return UNKNOWN
    if v is None:
        return STATUS_LABEL["not_applicable"] if m.get("_conference") else UNKNOWN
    if is_unknown(v):
        return status_label(v)
    n = num(v)
    return f"{n}" if n is not None else UNKNOWN


QUARTILE_VALUES = ("Q1", "Q2", "Q3", "Q4")


def single_quartile(q):
    """單一類別寫成一個 mapping（{system, quartile 或 value}）時轉成一筆的清單；
    只認 Q1–Q4 的字串，其他形狀原樣交回（照改動前的規則處理）。"""
    if isinstance(q, dict) and isinstance(q.get("system"), str):
        v = q.get("quartile") if q.get("quartile") is not None else q.get("value")
        if isinstance(v, str) and v in QUARTILE_VALUES:
            return [{**q, "quartile": v}]
    return q


def quartile(m):
    q = m.get("quartiles")
    if q is None:
        r = get(m, "jcr_category_rank", "ranks")
        if r:
            q = [{"system": "JCR", "quartile": x.get("quartile"), "category": x.get("category")} for x in r]
        else:
            return STATUS_LABEL["not_applicable"] if m.get("_conference") else UNKNOWN
    q = single_quartile(q)
    if isinstance(q, dict):
        return "未取得"
    if not isinstance(q, list):            # 字串等：認不得
        return UNKNOWN
    if not q:
        return "未取得"
    # 讀不出來的那幾筆（不是 mapping，或分區不是文字）略過，表格與 --format quartiles 一致；一筆都讀不出來印「?」
    q = [x for x in q if isinstance(x, dict) and isinstance(x.get("quartile"), str)]
    for system in ("JCR", "SJR"):
        qs = sorted({x.get("quartile") for x in q if x.get("system") == system and x.get("quartile")})
        if qs:
            return f"{'／'.join(qs)}（{system}）"
    return UNKNOWN


def quartile_detail(m):
    """各學科類別的分區與名次，例：Business Q1（48/323，JCR 2025）。給逐刊段落用。"""
    q = single_quartile(m.get("quartiles"))
    if not isinstance(q, list):
        return []
    best = {}   # 同一系統、同一類別、同一分區只留一筆；有名次的優先（出版社轉載常與直接讀到的重複）
    for x in q:
        if not isinstance(x, dict) or not isinstance(x.get("quartile"), str) or not x.get("quartile"):
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
    if v is None or isinstance(v, (list, tuple, set)):
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
        if m.get(k) is not None:           # 寫成 null 視同沒寫
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
    return STATUS_LABEL["not_applicable"] if m.get("_conference") else UNKNOWN


# ---------------------------------------------------------------- 費用、審稿、篇幅
def is_price(x):
    """currency_rates／list_price_usd 裡的價格只認數字；bool 是 int 的子類別，要另外排除。"""
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def apc_kind(rec, a, use_open_access=True):
    """必付或選付，單一判斷處。先後：mandatory 旗標 → status → identity.open_access（必付）
    → applies_when（有條件才收，選付）。都沒有回 None。"""
    if a.get("mandatory") is True:
        return "必付"
    if a.get("mandatory") is False:
        return "選付"
    st = a.get("status") if isinstance(a.get("status"), str) else ""
    if st.startswith("mandatory"):
        return "必付"
    if st == "optional":
        return "選付"
    if use_open_access and get(rec, "identity", "open_access"):
        return "必付"       # 改動前就有的規則；hybrid 也會走到這裡（另案處理），所以新別名的金額不套用
    if a.get("applies_when"):
        return "選付"
    return None


def apc(rec):
    fees = get(rec, "requirements", "fees") or {}
    if is_status_only(fees):               # 整個費用區塊只有 status（例：研討會查不到費用資訊）
        return status_label(fees)
    a = fees.get("apc") if isinstance(fees, dict) else None
    if is_status_only(a):                  # 整欄只有 status：查過，官方沒有 APC 資訊
        return status_label(a)
    if not isinstance(a, dict):
        return UNKNOWN
    cur = a.get("currency") or fees.get("currency")
    amt = a.get("amount")
    alias = False                          # 金額是否來自 currency_rates 或 list_price_usd
    if amt is None and isinstance(a.get("currency_rates"), list):      # 多幣別定價：取 USD
        usd = [x for x in a["currency_rates"] if isinstance(x, dict) and x.get("currency") == "USD"]
        if usd:
            if not is_price(usd[0].get("value")):
                return UNKNOWN
            cur, amt, alias = "USD", usd[0]["value"], True
    if amt is None and isinstance(a.get("list_price_usd"), dict) and a["list_price_usd"]:
        tiers = list(a["list_price_usd"].values())                     # 分級定價：取最高的一級（未折扣的定價）
        if not all(is_price(x) for x in tiers):
            return UNKNOWN
        cur, amt, alias = "USD", max(tiers), True
    if is_status_only(amt):                # 有 OA 選項但金額沒公布（例：只指向出版社的 APC 查詢頁）
        # 金額沒公布時只標得出「選付」：明寫 mandatory: false 或 status: optional，
        # 或有條件才收（applies_when）且沒寫 mandatory: true。
        # 這裡不看 identity.open_access：它常寫成 hybrid（有值但不是必付），改動前的輸出也不看它。
        optional = (a.get("mandatory") is False or a.get("status") == "optional"
                    or (a.get("mandatory") is not True and bool(a.get("applies_when"))))
        return f"{status_label(amt)}（選付）" if optional else status_label(amt)
    if isinstance(amt, bool):              # 型別檢查要在零元判斷之前：False == 0
        return UNKNOWN
    if amt == 0:                           # 鑽石 OA：沒有任何作者費用，不是「0 元選付」
        return "不收費"
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
    if isinstance(amt, bool) or not isinstance(amt, (int, float, str)):
        return UNKNOWN                     # 金額寫成清單等認不得的形狀
    if cur is not None and not isinstance(cur, str):
        return UNKNOWN                     # 幣別不是文字
    cur = (cur or "").split("（")[0].strip()[:3]
    return f"{cur} {fmt_int(amt)}（{apc_kind(rec, a, use_open_access=not alias) or UNKNOWN}）"


def review(rec):
    r = get(rec, "requirements", "review")
    if is_status_only(r):                  # 整個審稿區塊只有 status
        return status_label(r)
    cands = [get(r, "type"), get(r, "model"), get(r, "model_by_track", "research")]
    cands = [c["value"] if isinstance(c, dict) and not is_status_only(c) and isinstance(c.get("value"), str) else c
             for c in cands]               # {value: <code>} 讀成 code
    for t in cands:                        # 第一個真的寫了審稿制度的位置
        if isinstance(t, str) and t and t not in STATUS_LABEL:
            return REVIEW_LABEL.get(t, t)
    for t in cands:                        # 都沒寫制度，但有寫「查過、沒有」（mapping 或字串）
        if is_status_only(t):
            return status_label(t)
        if isinstance(t, str) and t in STATUS_LABEL:
            return STATUS_LABEL[t]
    return UNKNOWN


def length(rec):
    req = rec.get("requirements")
    if not isinstance(req, dict):
        return UNKNOWN
    L = next((req[k] for k in ("length", "length_policy", "length_note", "length_limit")
              if isinstance(req.get(k), dict)), None)      # 第一個寫成 mapping 的鍵；別的形狀不擋後面的鍵
    if L is None:
        return UNKNOWN
    if L.get("limit") == "none_stated_as_unlimited" or get(L, "word_limit", "status") == "not_applicable":
        return "無上限"
    if is_unknown(L):
        return NOT_PUBLISHED
    rng = L.get("recommended_range")
    unit = L.get("unit")
    if unit is not None and not isinstance(unit, str):
        return UNKNOWN                     # 單位不是文字
    if rng and unit == "words":
        return f"建議 {fmt_int(rng[0])}–{fmt_int(rng[1])} 字"
    v = L.get("value")
    if v is None or isinstance(v, bool) or not isinstance(v, (int, float, str)):
        return UNKNOWN
    if unit == "words":
        out = f"{fmt_int(v)} 字"
    elif unit in PAGE_UNIT_LABEL:
        out = f"{fmt_int(v)} {PAGE_UNIT_LABEL[unit]}"
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
                   ("oxford", "OUP"), ("cambridge", "CUP"), ("association for computing machinery", "ACM")]


def publisher(rec):
    raw = get(rec, "identity", "publisher")
    if is_status_only(raw):
        return status_label(raw)
    structured = raw is not None and not isinstance(raw, str)   # mapping 取 name，清單取第一個字串
    if isinstance(raw, dict):
        p = next((raw[k] for k in ("name", "value") if isinstance(raw.get(k), str)), "")
    elif isinstance(raw, (list, tuple)):
        p = next((x for x in raw if isinstance(x, str)), "")
    else:
        p = raw if isinstance(raw, str) else ""
    low = p.lower()
    if re.search(r"\bacm\b", low):
        return "ACM"
    for k, v in PUBLISHER_SHORT:
        if k in low:
            return v
    if structured:
        return UNKNOWN
    return p.split("（")[0].strip() or UNKNOWN


DISCOUNTS = {}   # venue id -> 文字；由 --discounts 檔提供（機構專屬資料，不屬於期刊記錄）


def safe(fn, *args):
    """讀一欄時出任何錯都印「?」：一筆寫壞的記錄不該讓整張表產不出來。"""
    kept = len(NOTES)
    try:
        return fn(*args)
    except Exception:
        del NOTES[kept:]                   # 這一欄印「?」，就不留它加到一半的附註
        return UNKNOWN


def row(rec):
    raw = get(rec, "identity", "metrics")
    bad = raw is not None and not isinstance(raw, dict)      # 有寫但不是 mapping：認不得
    m = {**(raw if isinstance(raw, dict) else {}), "_id": rec["id"],
         "_conference": is_conference(rec) and not bad}      # 形狀認不得時不套研討會的「不適用」
    name = get(rec, "identity", "name")
    return {
        "id": rec["id"],
        "publisher": safe(publisher, rec),
        "discount": DISCOUNTS.get(rec["id"], "—") if DISCOUNTS else None,
        "name": rec["id"] if name is None or name == "" else (name if isinstance(name, str) else UNKNOWN),
        "index": safe(wos, rec),
        "if": safe(impact_factor, m),
        "q": safe(quartile, m),
        "accept": safe(acceptance, m),
        "first": safe(duration, m, "first_decision"),
        "sub_accept": safe(duration, m, "sub_to_accept"),
        "apc": safe(apc, rec),
        "review": safe(review, rec),
        "length": safe(length, rec),
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
            m = get(load(i, a.root), "identity", "metrics")
            detail = safe(quartile_detail, m if isinstance(m, dict) else {})
            print(i + "\t" + "；".join(detail if isinstance(detail, list) else []))
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
