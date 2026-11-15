"""Tests for scripts/venue_table.py (capability venue-table).

Each test carries a `spec-example:` marker naming the Example it checks.

The baseline fixture `fixtures/venue_table_baseline.tsv` holds the rows the script printed on the
default branch before this change (columns: id, publisher, index, if, q, accept, first, sub_accept,
apc, review, length). It was recorded per record with:

    python3 scripts/venue_table.py --format json <venue-id>

and one row was written for each record that did not make the script raise (23 of 24).
"""
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


class ConferenceRecords(unittest.TestCase):
    GAPS = {"metrics": {"acceptance_rate": {"status": "not_published"}}}

    def test_conference_journal_only_columns(self):
        # spec-example: venue-table / conference journal-only columns
        r = build(kind="conference", identity=self.GAPS)
        for col in ("index", "if", "q", "first", "sub_accept"):
            with self.subTest(col=col):
                self.assertEqual(r[col], "不適用")
        self.assertEqual(r["apc"], "未公布")

    def test_journal_with_the_same_gaps(self):
        # spec-example: venue-table / journal with the same gaps
        r = build(kind="journal", identity=self.GAPS)
        for col in ("index", "if", "q"):
            with self.subTest(col=col):
                self.assertEqual(r[col], "?")


class Baseline(unittest.TestCase):
    def test_baseline_rows_are_unchanged(self):
        # spec-example: venue-table / baseline rows are unchanged
        rows = [l.split("\t") for l in BASELINE.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.assertEqual(len(rows), 23)
        for old in rows:
            vt.NOTES.clear()
            new = vt.row(vt.load(old[0], str(PLUGIN)))
            for name, before in zip(COLUMNS[1:], old[1:]):
                if before in ("?", "double_anonymous"):
                    continue
                with self.subTest(venue=old[0], column=name):
                    self.assertEqual(str(new[name]), before)

    def test_record_that_raised_now_builds(self):
        # spec-example: venue-table / record that raised now builds
        p = subprocess.run([sys.executable, str(SCRIPT), "--format", "json", "jnspg/jns-spine"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr[-400:])
        self.assertEqual(p.stdout.count('"id"'), 1)


if __name__ == "__main__":
    unittest.main()
