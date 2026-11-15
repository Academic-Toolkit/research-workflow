"""Tests for scripts/venue_table.py (capability venue-table).

Each test carries a `spec-example:` marker naming the Example it checks.

The baseline fixture `fixtures/venue_table_baseline.tsv` holds the rows the script printed on the
default branch before this change (columns: id, publisher, index, if, q, accept, first, sub_accept,
apc, review, length, sha256 of the record file). A row is compared only while its record file still
has that SHA-256, so a later update to a record does not fail the suite. It was recorded per record with:

    python3 scripts/venue_table.py --format json <venue-id>

and one row was written for each record that did not make the script raise (23 of 24).
"""
import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
SCRIPT = PLUGIN / "scripts" / "venue_table.py"
BASELINE = Path(__file__).resolve().parent / "fixtures" / "venue_table_baseline.tsv"
COLUMNS = ["id", "publisher", "index", "if", "q", "accept", "first", "sub_accept", "apc", "review", "length"]

_spec = importlib.util.spec_from_file_location("venue_table", SCRIPT)
vt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vt)


def record(kind="journal", identity=None, requirements=None):
    """A minimal in-memory record; only the fields a test names are present."""
    ident = {"name": "Test Venue", "publisher": "Test Press"}
    ident.update(identity or {})
    return {"id": "test/venue", "kind": kind, "identity": ident, "requirements": requirements or {}}


def build(**kw):
    vt.NOTES.clear()
    return vt.row(record(**kw))


def run_on_record(yaml_text):
    """Write one record file under a temporary plugin root and run the script on it."""
    with tempfile.TemporaryDirectory() as root:
        d = Path(root) / "venues" / "test"
        d.mkdir(parents=True)
        (d / "venue.yaml").write_text(yaml_text, encoding="utf-8")
        return subprocess.run([sys.executable, str(SCRIPT), "--root", root, "--format", "json", "test/venue"],
                              capture_output=True, text=True)


class StatusMappings(unittest.TestCase):
    def test_review_type_status_mapping(self):
        # spec-example: venue-table / review type status mapping
        r = build(requirements={"review": {"type": {"status": "not_published", "checked": "2026-11-15"}}})
        self.assertEqual(r["review"], "未公布")

    def test_publisher_status_mapping(self):
        # spec-example: venue-table / publisher status mapping
        r = build(kind="conference", identity={"publisher": {
            "status": "not_published", "checked": "2026-11-15", "note": "electronic proceedings"}})
        self.assertEqual(r["publisher"], "未公布")
        self.assertNotIn("status", r["publisher"])


class FeesBlock(unittest.TestCase):
    def test_fees_block_status_mapping(self):
        # spec-example: venue-table / fees block status mapping
        r = build(kind="conference", requirements={"fees": {"status": "not_found", "checked": "2026-11-15"}})
        self.assertEqual(r["apc"], "未取得")

    def test_apc_amount_with_applies_when(self):
        # spec-example: venue-table / apc amount with applies_when
        r = build(requirements={"fees": {"apc": {
            "amount": 3000, "currency": "USD", "applies_when": "author chooses open access"}}})
        self.assertEqual(r["apc"], "USD 3,000（選付）")


class Stderr(unittest.TestCase):
    def test_indexing_list_warns_on_stderr(self):
        # spec-example: venue-table / indexing list warns on stderr
        p = run_on_record("id: test/venue\nkind: journal\nidentity:\n  name: T\n  publisher: P\n"
                          "  indexing: [Scopus, PubMed]\nrequirements: {}\n")
        self.assertEqual(p.returncode, 0, p.stderr[-300:])
        lines = [l for l in p.stderr.splitlines() if "test/venue" in l and "「收錄」" in l]
        self.assertEqual(len(lines), 1)

    def test_conference_columns_write_no_warning(self):
        # spec-example: venue-table / conference columns write no warning
        p = run_on_record("id: test/venue\nkind: conference\nidentity:\n  name: T\n  publisher: P\n"
                          "requirements: {}\n")
        self.assertEqual(p.returncode, 0, p.stderr[-300:])
        for label in ("「收錄」", "「IF」", "「分區」", "「首次決定（中位）」", "「投稿→接受（中位）」"):
            with self.subTest(label=label):
                self.assertNotIn(label, p.stderr)


class UnrecognisedShapes(unittest.TestCase):
    def test_scalar_and_list_values_in_metric_fields(self):
        # spec-example: venue-table / scalar and list values in metric fields
        cases = [({"identity": {"metrics": {"quartiles": "Q1"}}}, "q"),
                 ({"identity": {"metrics": {"quartiles": ["Q1"]}}}, "q"),
                 ({"identity": {"metrics": {"impact_factor": [1]}}}, "if"),
                 ({"identity": {"metrics": {"acceptance_rate": [1]}}}, "accept"),
                 ({"identity": {"metrics": ["x"]}}, "if"),
                 ({"requirements": ["x"]}, "length")]
        for kw, col in cases:
            with self.subTest(kw=kw):
                self.assertEqual(build(**kw)[col], "?")

    def test_indexing_as_a_list(self):
        # spec-example: venue-table / indexing as a list
        r = build(identity={"indexing": ["Scopus", "PubMed"]})
        self.assertEqual(r["index"], "?")

    def test_review_type_of_an_unknown_mapping(self):
        # spec-example: venue-table / review type of an unknown mapping
        r = build(requirements={"review": {"type": {"kind": "custom"}}})
        self.assertEqual(r["review"], "?")


class AdditionalShapes(unittest.TestCase):
    def test_web_of_science_flags(self):
        # spec-example: venue-table / web of science flags
        cases = [(True, False, "SCIE"), (True, True, "SCIE＋SSCI"), (False, False, "兩者皆無")]
        for scie, ssci, expected in cases:
            with self.subTest(scie=scie, ssci=ssci):
                r = build(identity={"indexing": {"web_of_science": {"scie": scie, "ssci": ssci}}})
                self.assertEqual(r["index"], expected)

    def test_single_quartile_mapping(self):
        # spec-example: venue-table / single quartile mapping
        r = build(identity={"metrics": {"quartiles": {
            "system": "SJR", "category": "Software", "value": "Q1", "year": 2025}}})
        self.assertEqual(r["q"], "Q1（SJR）")

    def test_apc_from_currency_rates(self):
        # spec-example: venue-table / apc from currency rates
        r = build(requirements={"fees": {"apc": {
            "applies_when": "author chooses open access",
            "currency_rates": [{"currency": "GBP", "value": 2390}, {"currency": "USD", "value": 3390}]}}})
        self.assertEqual(r["apc"], "USD 3,390（選付）")

    def test_apc_from_list_price_tiers(self):
        # spec-example: venue-table / apc from list price tiers
        r = build(requirements={"fees": {"apc": {
            "mandatory": True, "list_price_usd": {"member": 1300, "non_member": 1800}}}})
        self.assertEqual(r["apc"], "USD 1,800（必付）")

    def test_length_limit_not_published(self):
        # spec-example: venue-table / length limit not published
        r = build(requirements={"length_limit": {"status": "not_published", "checked": "2026-11-15"}})
        self.assertEqual(r["length"], "未公布")

    def test_review_model_codes(self):
        # spec-example: venue-table / review model codes
        cases = [({"model": "double_anonymous"}, "雙匿名"),
                 ({"model_by_track": {"research": "double-anonymous"}}, "雙匿名"),
                 ({"type": "single_blind"}, "單盲")]
        for review, expected in cases:
            with self.subTest(review=review):
                self.assertEqual(build(requirements={"review": review})["review"], expected)


class FixRound1(unittest.TestCase):
    def test_status_mapping_at_the_newer_positions(self):
        # spec-example: venue-table / status mapping at the newer positions
        self.assertEqual(build(identity={"indexing": {"web_of_science": {"status": "not_found"}}})["index"], "未取得")
        self.assertEqual(build(requirements={"review": {"status": "not_published"}})["review"], "未公布")
        self.assertEqual(build(requirements={"review": {
            "type": {"status": "not_published"}, "model": "double_anonymous"}})["review"], "雙匿名")

    def test_shapes_that_raised_before_the_fix_round(self):
        # spec-example: venue-table / shapes that raised before the fix round
        nf = {"status": "not_found"}
        cases = [({"identity": {"metrics": {"quartiles": {"system": "JCR", "quartile": nf}}}}, "q", "未取得"),
                 ({"identity": {"metrics": {"quartiles": {"system": "SJR", "value": 1}}}}, "q", "未取得"),
                 ({"identity": {"metrics": {"quartiles": [{"system": "JCR", "quartile": nf}]}}}, "q", "?"),
                 ({"identity": {"metrics": {"jcr_category_rank": {"ranks": "Q1"}}}}, "q", "?"),
                 ({"requirements": {"review": {"type": ""}}}, "review", "?"),
                 ({"identity": {"metrics": {"time_to_first_decision": [30]}}}, "first", "?"),
                 ({"identity": {"metrics": {"impact_factor": {"value": {"x": 1}}}}}, "if", "?"),
                 ({"identity": {"metrics": {"acceptance_rate": {"value": [1]}}}}, "accept", "?"),
                 ({"requirements": {"length": {"value": [1], "unit": "words"}}}, "length", "?"),
                 ({"requirements": {"fees": {"apc": {"amount": [2000], "currency": "USD", "mandatory": True}}}},
                  "apc", "?")]
        for kw, col, expected in cases:
            with self.subTest(kw=kw):
                self.assertEqual(build(**kw)[col], expected)

    def test_quartiles_format_never_raises(self):
        # spec-example: venue-table / quartiles format never raises
        with tempfile.TemporaryDirectory() as root:
            d = Path(root) / "venues" / "test"
            d.mkdir(parents=True)
            (d / "venue.yaml").write_text("id: test/venue\nkind: journal\nidentity:\n  name: T\n  publisher: P\n"
                                          "  metrics:\n    quartiles: [Q1]\nrequirements: {}\n", encoding="utf-8")
            p = subprocess.run([sys.executable, str(SCRIPT), "--root", root, "--format", "quartiles", "test/venue"],
                               capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr[-300:])
        lines = p.stdout.splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].split("\t"), ["test/venue", ""])

    def test_web_of_science_decides_the_indexing_cell(self):
        # spec-example: venue-table / web of science decides the indexing cell
        cases = [({"web_of_science": {"scie": "false", "ssci": False}}, "?"),
                 ({"web_of_science": {"scie": {"status": "not_found"}, "ssci": False}}, "?"),
                 ({"web_of_science": {"scie": True}}, "?"),
                 ({"web_of_science": {"scie": False, "ssci": False},
                   "clarivate_wos": {"in_ssci": {"value": True}}}, "兩者皆無"),
                 ({"web_of_science": {"scie": True, "ssci": False, "esci": True}}, "SCIE")]
        for indexing, expected in cases:
            with self.subTest(indexing=indexing):
                self.assertEqual(build(identity={"indexing": indexing})["index"], expected)

    def test_single_quartile_mapping_in_the_quartiles_format(self):
        # spec-example: venue-table / single quartile mapping in the quartiles format
        detail = vt.quartile_detail({"quartiles": {
            "system": "SJR", "category": "Software", "value": "Q1", "year": 2025}})
        self.assertEqual(detail, ["Software Q1（SJR 2025）"])

    def test_apc_kind_precedence(self):
        # spec-example: venue-table / apc kind precedence
        np_ = {"status": "not_published"}
        cases = [({"amount": 2000, "currency": "USD", "status": "mandatory", "applies_when": "on acceptance"},
                  None, "USD 2,000（必付）"),
                 ({"amount": 2000, "currency": "USD", "applies_when": "on acceptance"}, True, "USD 2,000（必付）"),
                 ({"amount": 2000, "currency": "USD", "mandatory": False}, True, "USD 2,000（選付）"),
                 ({"amount": np_, "mandatory": True, "applies_when": "on acceptance"}, None, "未公布"),
                 ({"amount": np_, "applies_when": "on acceptance"}, None, "未公布（選付）")]
        for apc, oa, expected in cases:
            with self.subTest(apc=apc, oa=oa):
                ident = {"open_access": oa} if oa is not None else {}
                self.assertEqual(build(identity=ident, requirements={"fees": {"apc": apc}})["apc"], expected)

    def test_length_key_that_holds_a_mapping_wins(self):
        # spec-example: venue-table / length key that holds a mapping wins
        r = build(requirements={"length": "see guidelines", "length_limit": {"status": "not_published"}})
        self.assertEqual(r["length"], "未公布")

    def test_review_model_in_other_positions(self):
        # spec-example: venue-table / review model in other positions
        self.assertEqual(build(requirements={"review": {"type": {"value": "single_blind"}}})["review"], "單盲")
        self.assertEqual(build(requirements={"review": {"type": "", "model": "double_anonymous"}})["review"], "雙匿名")
        self.assertEqual(build(requirements={"review": {
            "type": "not_published", "model": "double_anonymous"}})["review"], "雙匿名")
        self.assertEqual(build(requirements={"review": {"type": "not_published"}})["review"], "未公布")

    def test_publisher_short_names(self):
        # spec-example: venue-table / publisher short names
        cases = [("Association for Computing Machinery", "ACM"),
                 ("ACM Digital Library（2026 proceedings）", "ACM"),
                 ({"name": "Elsevier B.V."}, "Elsevier"),
                 ({"name": "ACM Press"}, "ACM"),
                 ({"value": "Elsevier"}, "Elsevier"),
                 ("IEEE and ACM", "ACM"),
                 ("Acme Books", "Acme Books"),
                 ({"name": "Unknown House", "note": "formerly Wiley"}, "?"),
                 ({"name": "Unknown House"}, "?"),
                 (["Unknown House"], "?")]
        for pub, expected in cases:
            with self.subTest(pub=pub):
                self.assertEqual(build(identity={"publisher": pub})["publisher"], expected)


class FixRound2(unittest.TestCase):
    def test_indexing_block_status_mapping(self):
        # spec-example: venue-table / indexing block status mapping
        r = build(identity={"indexing": {"status": "not_found", "checked": "2026-11-15"}})
        self.assertEqual(r["index"], "未取得")

    def test_values_that_are_not_numbers_or_text(self):
        # spec-example: venue-table / values that are not numbers or text
        cases = [({"requirements": {"fees": {"apc": {"amount": False, "currency": "USD"}}}}, "apc"),
                 ({"requirements": {"fees": {"apc": {"currency_rates": [{"currency": "USD", "value": False}]}}}}, "apc"),
                 ({"requirements": {"fees": {"apc": {"mandatory": True, "list_price_usd": {"non_member": False}}}}}, "apc"),
                 ({"requirements": {"fees": {"apc": {"amount": 2000, "currency": ["USD"], "mandatory": True}}}}, "apc"),
                 ({"requirements": {"fees": {"apc": {"all_other_articles": {"amount": [1]}, "mandatory": True}}}}, "apc"),
                 ({"requirements": {"length": {"value": 10, "unit": ["pages"]}}}, "length"),
                 ({"identity": {"name": ["A", "B"]}}, "name")]
        for kw, col in cases:
            with self.subTest(kw=kw):
                self.assertEqual(build(**kw)[col], "?")

    def test_failed_column_leaves_no_footnote(self):
        # spec-example: venue-table / failed column leaves no footnote
        r = build(identity={"metrics": {"time_submission_to_acceptance": {"status": "not_published"},
                                        "estimates": {"sub_to_acceptance": {"value": "fast", "n": 10}}}})
        self.assertEqual(r["sub_accept"], "?")
        self.assertEqual(vt.NOTES, [])

    def test_apc_kind_for_amounts_from_the_new_price_keys(self):
        # spec-example: venue-table / apc kind for amounts from the new price keys
        tiers = {"member": 1300, "non_member": 1800}
        cases = [({"applies_when": "author chooses open access",
                   "currency_rates": [{"currency": "USD", "value": 3390}]}, "USD 3,390（選付）"),
                 ({"list_price_usd": tiers}, "USD 1,800（?）"),
                 ({"mandatory": True, "list_price_usd": tiers}, "USD 1,800（必付）"),
                 ({"amount": {"status": "not_published"}, "status": "optional"}, "未公布（選付）")]
        for apc, expected in cases:
            with self.subTest(apc=apc):
                r = build(identity={"open_access": "hybrid"}, requirements={"fees": {"apc": apc}})
                self.assertEqual(r["apc"], expected)

    def test_quartile_list_with_one_unreadable_entry(self):
        # spec-example: venue-table / quartile list with one unreadable entry
        q = [{"system": "JCR", "category": "A", "quartile": {"status": "not_found"}},
             {"system": "SJR", "category": "B", "quartile": "Q1", "year": 2025}]
        self.assertEqual(build(identity={"metrics": {"quartiles": q}})["q"], "Q1（SJR）")
        self.assertEqual(vt.quartile_detail({"quartiles": q}), ["B Q1（SJR 2025）"])

    def test_metrics_indexing_is_still_read(self):
        # spec-example: venue-table / metrics indexing is still read
        r = build(identity={"indexing": {}, "metrics": {
            "indexing": {"web_of_science": {"scie": True, "ssci": False}}}})
        self.assertEqual(r["index"], "SCIE")

    def test_prescribed_length_shape_validates(self):
        # spec-example: venue-table / prescribed length shape validates
        import yaml
        unknown = {"status": "not_published", "checked": "2026-11-15"}
        src = yaml.safe_load((PLUGIN / "venues" / "psychometric-society" / "psychometrika.yaml").read_text(encoding="utf-8"))
        results = []
        for key in ("length_limit", "length"):
            rec = yaml.safe_load(yaml.safe_dump(src, allow_unicode=True))
            rec["requirements"].pop("length", None)
            rec["requirements"][key] = unknown
            with tempfile.TemporaryDirectory() as d:
                f = Path(d) / "record.yaml"
                f.write_text(yaml.safe_dump(rec, allow_unicode=True), encoding="utf-8")
                p = subprocess.run([sys.executable, str(PLUGIN / "scripts" / "validate.py"), str(f)],
                                   capture_output=True, text=True)
            results.append(p.returncode)
        self.assertEqual(results, [0, 1])

    def test_skill_text_names_the_validating_shape(self):
        # spec-example: venue-table / skill text names the validating shape
        text = (PLUGIN / "skills" / "add-venue" / "SKILL.md").read_text(encoding="utf-8")
        row = [l for l in text.splitlines() if l.startswith("| 篇幅 |")]
        self.assertEqual(len(row), 1)
        self.assertIn("requirements.length_limit: {status: not_published, checked}", row[0])
        self.assertNotIn("requirements.length: {status: not_published, checked}", row[0])


class ConferenceRecords(unittest.TestCase):
    GAPS = {"metrics": {"acceptance_rate": {"status": "not_published"}}}

    def test_conference_journal_only_columns(self):
        # spec-example: venue-table / conference journal-only columns
        r = build(kind="conference", identity=self.GAPS)
        for col in ("index", "if", "q", "first", "sub_accept"):
            with self.subTest(col=col):
                self.assertEqual(r[col], "不適用")
        self.assertEqual(r["apc"], "?")

    def test_conference_metric_edge_cases(self):
        # spec-example: venue-table / conference metric edge cases
        cases = [(["x"], "if", "?"), (["x"], "first", "?"),
                 ({"time_to_first_decision": None}, "first", "不適用"),
                 ({"impact_factor": None, "quartiles": None}, "q", "不適用")]
        for metrics, col, expected in cases:
            with self.subTest(metrics=metrics, col=col):
                self.assertEqual(build(kind="conference", identity={"metrics": metrics})[col], expected)
        self.assertEqual(build(kind="conference", identity={"indexing": {}})["index"], "?")

    def test_conference_apc_is_read_like_a_journal(self):
        # spec-example: venue-table / conference apc is read like a journal
        cases = [({}, "?"), ({"fees": {"registration": {"amount": 500, "currency": "USD"}}}, "?"),
                 ({"fees": {"apc": {"status": "not_published"}}}, "未公布")]
        for req, expected in cases:
            with self.subTest(req=req):
                self.assertEqual(build(kind="conference", requirements=req)["apc"], expected)

    def test_journal_with_the_same_gaps(self):
        # spec-example: venue-table / journal with the same gaps
        r = build(kind="journal", identity=self.GAPS)
        for col in ("index", "if", "q"):
            with self.subTest(col=col):
                self.assertEqual(r[col], "?")


def compare_baseline(rows):
    """Compare baseline rows with the script's output. Returns (compared, skipped, mismatches).
    A row is skipped when its record file no longer has the SHA-256 stored with the row."""
    compared, skipped, mismatches = 0, 0, []
    for old in rows:
        path = PLUGIN / "venues" / f"{old[0]}.yaml"
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != old[11]:
            skipped += 1
            continue
        compared += 1
        vt.NOTES.clear()
        new = vt.row(vt.load(old[0], str(PLUGIN)))
        for name, before in zip(COLUMNS[1:], old[1:11]):
            if before in ("?", "double_anonymous"):
                continue
            if str(new[name]) != before:
                mismatches.append((old[0], name, before, str(new[name])))
    return compared, skipped, mismatches


def baseline_rows():
    return [l.split("\t") for l in BASELINE.read_text(encoding="utf-8").splitlines() if l.strip()]


class Baseline(unittest.TestCase):
    def test_baseline_rows_are_unchanged(self):
        # spec-example: venue-table / baseline rows are unchanged
        rows = baseline_rows()
        self.assertEqual(len(rows), 23)
        compared, skipped, mismatches = compare_baseline(rows)
        self.assertEqual(mismatches, [])
        self.assertEqual(compared + skipped, 23)
        self.assertGreater(compared, 0)

    def test_changed_record_is_not_compared(self):
        # spec-example: venue-table / changed record is not compared
        row = list(baseline_rows()[0])
        row[1] = "a publisher the record never had"   # would be a mismatch if it were compared
        row[11] = "0" * 64                             # the record file does not have this hash
        compared, skipped, mismatches = compare_baseline([row])
        self.assertEqual((compared, skipped, mismatches), (0, 1, []))

    def test_record_that_raised_now_builds(self):
        # spec-example: venue-table / record that raised now builds
        self.assertIsInstance(vt.load("jnspg/jns-spine", str(PLUGIN))["identity"]["indexing"], list,
                              "precondition changed: the record no longer has the shape that raised")
        p = subprocess.run([sys.executable, str(SCRIPT), "--format", "json", "jnspg/jns-spine"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr[-400:])
        self.assertEqual(p.stdout.count('"id"'), 1)


if __name__ == "__main__":
    unittest.main()
