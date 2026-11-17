#!/usr/bin/env python3
"""驗證 venue 記錄：JSON Schema + 三條 schema 表達不了的 lint 規則。

用法:  python3 scripts/validate.py [venues/**/*.yaml]
       不給參數則掃 venues/ 底下全部 .yaml
"""
import sys, glob, json, hashlib, datetime, re
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "schema" / "venue.schema.json").read_text())


def normalize_dates(node):
    """YAML 會把未加引號的 2026-08-03 隱式解析成 datetime.date，撞上 schema 的 type:string。

    這是序列化格式的阻抗不匹配，不是資料錯誤 —— 語意上兩者是同一個東西。
    在載入層正規化，而不是要求貢獻者為每個日期加引號（會忘，且錯誤訊息難懂）。
    """
    if isinstance(node, dict):
        return {k: normalize_dates(v) for k, v in node.items()}
    if isinstance(node, list):
        return [normalize_dates(v) for v in node]
    if isinstance(node, (datetime.date, datetime.datetime)):
        return node.isoformat()
    return node


ADDRESS = re.compile(r"[^\s@<>()\[\],;:\"']+@[^\s@<>()\[\],;:\"']+\.[^\s@<>()\[\],;:\"'.]+")


def contact_addresses(rec):
    """聯絡信箱依位置分成兩種，回傳 (個人信箱的欄位路徑, 公務信箱的欄位路徑)。

    只看 identity、requirements.submission、cycle。identity 底下（不含 identity 本身，
    它的 name 是 venue 的名稱）有字串 name 的 mapping 是具名人物，它底下任何深度含位址的
    字串都算個人信箱；範圍內其他含位址的字串算公務信箱。不看網域。
    """
    personal, office = [], []

    def walk(node, path, in_person, may_name):
        if isinstance(node, dict):
            person = in_person or (may_name and isinstance(node.get("name"), str))
            for k, v in node.items():
                walk(v, f"{path}.{k}", person, may_name)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]", in_person, may_name)
        elif isinstance(node, str) and ADDRESS.search(node):
            (personal if in_person else office).append(path)

    def section(node, path, may_name):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{path}.{k}", False, may_name)

    if isinstance(rec, dict):
        section(rec.get("identity"), "identity", True)
        req = rec.get("requirements")
        section(req.get("submission") if isinstance(req, dict) else None, "requirements.submission", False)
        section(rec.get("cycle"), "cycle", False)
    return personal, office


def lint(rec, path):
    """JSON Schema 表達不了的跨欄位不變量。每條都對應 SCHEMA.md 裡一個實測發現。"""
    errs = []
    sources = rec.get("sources", [])

    # L1 — staleness 算 last_verified_at，所以它不能早於 fetched_at
    for s in sources:
        snap = s.get("snapshot", {})
        f, v = snap.get("fetched_at"), snap.get("last_verified_at")
        if f and v and str(v) < str(f):
            errs.append(f"[L1] source '{s['id']}': last_verified_at({v}) 早於 fetched_at({f})")

    # L2 — 跨 source 的 hash 相同 = 抓取故障（實測: APA 三頁都回同一個 Incapsula 空殼）
    seen = {}
    for s in sources:
        h = (s.get("snapshot") or {}).get("extracted_sha256")
        if not h:
            continue
        if h in seen:
            errs.append(
                f"[L2] source '{s['id']}' 與 '{seen[h]}' 的 extracted_sha256 相同 "
                f"({h[:16]}…) — 幾乎必然是抓到 bot 挑戰頁或空殼，不是巧合"
            )
        seen[h] = s["id"]

    # L3 — http_viable=false 卻宣告 method: http，是自相矛盾
    for s in sources:
        fetch = s.get("fetch", {})
        if fetch.get("http_viable") is False and fetch.get("method") == "http":
            errs.append(f"[L3] source '{s['id']}': http_viable=false 但 method=http")

    # L4 — 權威來源缺 validity 斷言 = freshness 檢查會安靜說謊
    for s in sources:
        if s.get("role") == "authoritative" and "validity" not in s.get("fetch", {}):
            errs.append(
                f"[L4] source '{s['id']}' 是 authoritative 但缺 fetch.validity — "
                f"沒有斷言就無法分辨『內容沒變』與『抓到空殼』"
            )

    return errs


def lint_warnings(rec):
    """WARN 而非 ERROR：這些是「使用者必須知道」但「記錄本身沒有錯」的狀態。

    過期的 cycle 是合法狀態（研討會辦完了），不是缺陷。若當成 error，語料庫會
    永遠紅燈，人就不再看驗證輸出 —— 那反而讓真正的錯誤被淹沒。
    """
    warns = []
    if rec.get("kind") == "conference":
        cyc = rec.get("cycle") or {}
        exp = cyc.get("expires_at")
        if exp and str(exp) < datetime.date.today().isoformat():
            warns.append(
                f"[W1] cycle.expires_at({exp}) 已過期（status: {cyc.get('status')}）— "
                f"日期/地點/報名資訊不得沿用至下一屆"
            )

    # W2 — 快照太久沒驗證。staleness 算 last_verified_at，不是 fetched_at。
    today = datetime.date.today()
    for s in rec.get("sources", []):
        v = (s.get("snapshot") or {}).get("last_verified_at")
        if not v:
            continue
        age = (today - datetime.date.fromisoformat(str(v))).days
        if age > 365:
            warns.append(f"[W2] source '{s['id']}' 已 {age} 天未驗證（last_verified_at {v}）")

    # W3 — 同一筆記錄同時有個人信箱與公務信箱。訊息只列欄位路徑，不印位址：
    # 驗證輸出常被貼到 issue 或對話裡。
    personal, office = contact_addresses(rec)
    if personal and office:
        warns.append(
            "[W3] 同時記了個人信箱與公務信箱；有公務信箱時只記公務信箱。"
            f"個人信箱的位置：{'、'.join(personal)}"
        )

    return warns


def main(argv):
    files = argv[1:] or sorted(glob.glob(str(ROOT / "venues" / "**" / "*.yaml"), recursive=True))
    if not files:
        print("找不到任何 venue 檔案"); return 1

    validator = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
    total_err = 0
    total_warn = 0

    for f in files:
        rec = normalize_dates(yaml.safe_load(Path(f).read_text()))
        rel = Path(f).relative_to(ROOT) if str(f).startswith(str(ROOT)) else f
        schema_errs = sorted(validator.iter_errors(rec), key=lambda e: list(e.path))
        lint_errs = lint(rec, f)
        warns = lint_warnings(rec)

        mark = "✓" if not (schema_errs or lint_errs) else "✗"
        print(f"  {mark} {rel}")
        for e in schema_errs:
            loc = "/".join(str(p) for p in e.path) or "(root)"
            print(f"      [schema] {loc}: {e.message}")
        for e in lint_errs:
            print(f"      {e}")
        for w in warns:
            print(f"      ⚠ {w}")
        total_err += len(schema_errs) + len(lint_errs)
        total_warn += len(warns)

    print(f"\n{len(files)} 個檔案，{total_err} 個錯誤，{total_warn} 個警告")
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
