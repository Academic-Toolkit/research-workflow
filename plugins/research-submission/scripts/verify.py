#!/usr/bin/env python3
"""重抓一手來源、比對 hash，回報快照是否仍然有效。這是名稱裡「live」的實作。

用法:
    python3 scripts/verify.py                      # 驗證全部
    python3 scripts/verify.py apa/psychological-methods
    python3 scripts/verify.py --write              # 通過者更新 last_verified_at

設計約束（見 SCHEMA.md）:
  * hash 算在【抽取後純文字】上，不是 HTTP body。bot 挑戰頁會以 200 回傳空殼，
    對 body 取 hash 會得到一個穩定不變的值 —— freshness 檢查於是永遠說「沒變動」
    而實際上什麼都沒監看。
  * 入庫前先跑 fetch.validity 斷言（must_contain + min_extracted_chars）。
    兩者缺一不可：實測 psychometricsociety.org 的 404 頁面有 28 KB，
    比某些真實頁面還大，單靠長度擋不住。
  * method 為 webfetch / browser 的 source 本腳本無法處理（需要 agent 或真實
    瀏覽器）。這類會標成 NEEDS_AGENT 而非假裝成功 —— 靜默略過等於謊報新鮮。
"""
import sys, re, json, hashlib, datetime, urllib.request, urllib.error
from html.parser import HTMLParser
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
EXTRACTOR = "stdlib-htmlparser/1"   # hash 只在同一 extractor 內可比，故記版本
UA = "research-submission/0.1 (+https://github.com/Academic-Toolkit/research-workflow)"


class TextExtractor(HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "head"}

    def __init__(self):
        super().__init__()
        self.parts, self.skip_depth = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data):
        if not self.skip_depth:
            t = data.strip()
            if t:
                self.parts.append(t)


def extract_text(html):
    p = TextExtractor()
    try:
        p.feed(html)
    except Exception:
        pass
    return re.sub(r"\s+", " ", " ".join(p.parts)).strip()


def fetch_http(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return raw.decode("utf-8", errors="replace")


def check_source(src):
    """回傳 (status, detail, new_hash|None)."""
    fetch = src.get("fetch", {})
    method = fetch.get("method", "http")

    if method != "http":
        return ("NEEDS_AGENT",
                f"method={method} — 需 agent/瀏覽器擷取（{fetch.get('http_failure_mode','')[:60]}）",
                None)

    try:
        html = fetch_http(src["url"])
    except Exception as e:
        return ("FETCH_FAILED", f"{type(e).__name__}: {e}", None)

    text = extract_text(html)
    v = fetch.get("validity") or {}

    need = v.get("must_contain")
    if need and need not in text:
        return ("INVALID", f"缺少必含字串 {need!r} — 疑似 404/挑戰頁，不入庫", None)

    lo = v.get("min_extracted_chars")
    if lo and len(text) < lo:
        return ("INVALID", f"抽取長度 {len(text)} < 下限 {lo}", None)

    h = hashlib.sha256(text.encode()).hexdigest()
    stored = (src.get("snapshot") or {}).get("extracted_sha256")
    stored_ex = (src.get("snapshot") or {}).get("extractor")

    if not stored:
        return ("BASELINE", f"首次建立基準（{len(text)} chars）", h)
    if stored_ex and stored_ex != EXTRACTOR:
        return ("EXTRACTOR_MISMATCH",
                f"記錄用 {stored_ex}，現行 {EXTRACTOR} — hash 不可比，需重建基準", h)
    if stored == h:
        return ("UNCHANGED", f"{len(text)} chars", h)
    return ("CHANGED", f"來源已變動 — 須重新擷取內容並人工覆核", h)


def main(argv):
    write = "--write" in argv
    targets = [a for a in argv[1:] if not a.startswith("--")]
    files = sorted((ROOT / "venues").rglob("*.yaml"))
    if targets:
        files = [f for f in files if any(t in str(f) for t in targets)]
    if not files:
        print("找不到符合的 venue"); return 1

    today = datetime.date.today().isoformat()
    exit_code = 0

    for f in files:
        raw = f.read_text()
        rec = yaml.safe_load(raw)
        print(f"\n{rec['id']}")
        for src in rec.get("sources", []):
            status, detail, h = check_source(src)
            icon = {"UNCHANGED": "✓", "BASELINE": "+", "NEEDS_AGENT": "→",
                    "CHANGED": "!", "INVALID": "✗", "FETCH_FAILED": "✗",
                    "EXTRACTOR_MISMATCH": "!"}.get(status, "?")
            print(f"  {icon} {status:<18} {src['id']:<16} {detail}")

            if status in ("CHANGED", "INVALID", "FETCH_FAILED"):
                exit_code = 1

            if write and status in ("UNCHANGED", "BASELINE") and h:
                # 只有真的驗證過才動 last_verified_at —— 這是 staleness 的依據
                raw = raw.replace(
                    f"extracted_sha256: null",
                    f"extracted_sha256: \"{h}\"\n      extractor: {EXTRACTOR}", 1
                ) if status == "BASELINE" else raw
                rec_src = src
                rec_src.setdefault("snapshot", {})["last_verified_at"] = today

        if write:
            print("  (--write: 已更新 last_verified_at；hash 基準請人工覆核後再提交)")

    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
