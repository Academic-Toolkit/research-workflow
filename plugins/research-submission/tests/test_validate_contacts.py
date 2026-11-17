"""Tests for the contact-address rule of scripts/validate.py (capability venue-contacts).

Each test carries a `spec-example:` marker naming the Example it checks.
Every address in this file is invented and sits under example.org.
"""
import datetime
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

PLUGIN = Path(__file__).resolve().parent.parent
SCRIPT = PLUGIN / "scripts" / "validate.py"
SKILL = PLUGIN / "skills" / "add-venue" / "SKILL.md"

_spec = importlib.util.spec_from_file_location("validate", SCRIPT)
va = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(va)

EDITOR = {"name": "A. Editor", "email": "a.editor@example.org"}
OFFICE = {"email": "office@example.org"}


def w3(rec):
    return [w for w in va.lint_warnings(rec) if w.startswith("[W3]")]


class Classification(unittest.TestCase):
    def test_classification_by_position(self):
        # spec-example: venue-contacts / classification by position
        rows = [
            ({"identity": {"editor": dict(EDITOR)}}, ["identity.editor.email"], []),
            ({"identity": {"editor": {"name": "A. Editor", "note": "write to a.editor@example.org"}}},
             ["identity.editor.note"], []),
            ({"identity": {"editors": [{"name": "A. Editor"},
                                       {"name": "B. Editor", "email": "b.editor@example.org"}]}},
             ["identity.editors[1].email"], []),
            ({"identity": {"editors": {"board": {"name": "A. Editor",
                                                 "contact": {"email": "a.editor@example.org"}}}}},
             ["identity.editors.board.contact.email"], []),
            ({"identity": {"editorial_office": dict(OFFICE)}}, [], ["identity.editorial_office.email"]),
            ({"identity": {"editors": {"desk": {"role": "Reproducibility editors",
                                                "email": "repro@example.org"}}}},
             [], ["identity.editors.desk.email"]),
            ({"identity": {"name": "Journal of Examples", "contact": "office@example.org"}},
             [], ["identity.contact"]),
            ({"requirements": {"submission": {"contact": "office@example.org"}}},
             [], ["requirements.submission.contact"]),
            ({"cycle": {"portal": {"email": "meeting2026@example.org"}}}, [], ["cycle.portal.email"]),
            ({"warnings": ["report fakes to abuse@example.org"]}, [], []),
            ({"identity": {"editor": {"name": "A. Editor", "twitter": "@aeditor"}}}, [], []),
        ]
        for rec, personal, office in rows:
            with self.subTest(rec=rec):
                self.assertEqual(va.contact_addresses(rec), (personal, office))


    def test_named_persons_in_every_section_of_the_scope(self):
        # spec-example: venue-contacts / named persons in every section of the scope
        rows = [
            ({"cycle": {"chairs": [{"name": "C. Chair", "email": "c.chair@example.org"}]}},
             ["cycle.chairs[0].email"], []),
            ({"requirements": {"submission": {"helper": {"name": "H. Helper", "email": "h.helper@example.org"}}}},
             ["requirements.submission.helper.email"], []),
            ({"identity": {"owner": {"name": "Example Trust", "email": "trust@example.org"}}},
             ["identity.owner.email"], []),
            ({"identity": {"editor": {"name": {"en": "A. Editor"}, "email": "a.editor@example.org"}}},
             [], ["identity.editor.email"]),
        ]
        for rec, personal, office in rows:
            with self.subTest(rec=rec):
                self.assertEqual(va.contact_addresses(rec), (personal, office))

    def test_what_counts_as_an_address(self):
        # spec-example: venue-contacts / what counts as an address
        rows = [
            ("a.editor@example.org", True),
            ("write to <a.editor@example.org>.", True),
            ("主編信箱a.editor@example.org。", True),
            ("https://social.example/@aeditor/intro.html", False),
            ("@aeditor", False),
            ("帳號@aeditor，網站 example.org", False),
            ("a.editor@localhost", False),
        ]
        for text, expected in rows:
            with self.subTest(text=text):
                found = va.contact_addresses({"identity": {"contact": text}})
                self.assertEqual(found, ([], ["identity.contact"] if expected else []))

    def test_an_address_used_as_a_key(self):
        # spec-example: venue-contacts / an address used as a key
        rec = {"identity": {"editor": {"name": "A. Editor", "contacts": {"a.editor@example.org": "primary"}},
                            "desk": {"office@example.org": {"hours": "9-5"}}}}
        self.assertEqual(va.contact_addresses(rec),
                         (["identity.editor.contacts.<address>"], ["identity.desk.<address>"]))

    def test_a_section_written_as_a_string_or_a_list(self):
        # spec-example: venue-contacts / a section written as a string or a list
        self.assertEqual(va.contact_addresses({"requirements": {"submission": "write to office@example.org"}}),
                         ([], ["requirements.submission"]))
        self.assertEqual(va.contact_addresses({"cycle": ["meeting2026@example.org"]}), ([], ["cycle[0]"]))
        self.assertEqual(va.contact_addresses({"identity": None, "requirements": None, "cycle": None}), ([], []))
        self.assertEqual(va.contact_addresses(None), ([], []))


class WarningW3(unittest.TestCase):
    def test_one_warning_naming_the_personal_paths(self):
        # spec-example: venue-contacts / one warning naming the personal paths
        rec = {"identity": {"editor": {"name": "A. Editor", "email": "a.editor@example.org",
                                       "note": "also a.editor@example.org"},
                            "editorial_office": dict(OFFICE)}}
        found = w3(rec)
        self.assertEqual(len(found), 1)
        text = found[0]
        self.assertIn("identity.editor.email", text)
        self.assertIn("identity.editor.note", text)
        self.assertLess(text.index("identity.editor.email"), text.index("identity.editor.note"))
        self.assertNotIn("a.editor@example.org", text)
        self.assertNotIn("office@example.org", text)
        self.assertNotIn("@", text)

    def test_one_kind_only_gives_no_warning(self):
        # spec-example: venue-contacts / one kind only gives no warning
        rows = [
            {"identity": {"editor": dict(EDITOR)}},
            {"identity": {"editorial_office": dict(OFFICE)},
             "requirements": {"submission": {"contact": "office@example.org"}}},
            {"identity": {"name": "Journal of Examples"}},
            {"identity": {"editor": dict(EDITOR)}, "warnings": ["write to office@example.org"]},
        ]
        for rec in rows:
            with self.subTest(rec=rec):
                self.assertEqual(w3(rec), [])

    def test_warning_text_when_a_key_is_an_address(self):
        # spec-example: venue-contacts / warning text when a key is an address
        rec = {"identity": {"editor": {"name": "A. Editor", "contacts": {"a.editor@example.org": "primary"}},
                            "editorial_office": dict(OFFICE)}}
        found = w3(rec)
        self.assertEqual(len(found), 1)
        self.assertIn("identity.editor.contacts.<address>", found[0])
        self.assertNotIn("@", found[0])

    def test_validator_run_exits_zero_with_w3(self):
        # spec-example: venue-contacts / validator run exits zero with W3
        rec = yaml.safe_load((PLUGIN / "venues" / "ams" / "bulletin-of-the-ams.yaml").read_text(encoding="utf-8"))
        rec["warnings"] = []
        today = datetime.date.today().isoformat()
        for source in rec["sources"]:  # W2 counts days since last_verified_at; the fixture must not age
            source["snapshot"]["last_verified_at"] = today
        rec["requirements"]["submission"] = {}
        rec["identity"]["editor"] = dict(EDITOR)
        rec["identity"]["editorial_office"] = dict(OFFICE)
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "record.yaml"
            f.write_text(yaml.safe_dump(rec, allow_unicode=True), encoding="utf-8")
            p = subprocess.run([sys.executable, str(SCRIPT), str(f)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout[-400:])
        self.assertEqual(sum("[W3]" in line for line in p.stdout.splitlines()), 1, p.stdout[-400:])
        self.assertIn("0 個錯誤，1 個警告", p.stdout)


class Guidance(unittest.TestCase):
    def test_skill_text_on_contact_addresses(self):
        # spec-example: venue-contacts / skill text on contact addresses
        text = SKILL.read_text(encoding="utf-8")
        self.assertTrue(any(line.startswith("| W3 |") for line in text.splitlines()))
        for phrase in ("公務信箱", "個人信箱", "看信箱屬於誰，不看網域", "即使官網把它列為聯絡方式",
                       "不寫在具名人物底下", "備註與警告", "機構的信箱", "#21"):
            self.assertIn(phrase, text)
        self.assertNotIn("公務信箱寫在 `identity.editorial_office.email`", text)


class Corpus(unittest.TestCase):
    def test_bundled_records_have_no_w3(self):
        # spec-example: venue-contacts / bundled records have no W3
        files = sorted((PLUGIN / "venues").rglob("*.yaml"))
        self.assertTrue(files)
        for f in files:
            with self.subTest(record=str(f.relative_to(PLUGIN))):
                rec = va.normalize_dates(yaml.safe_load(f.read_text(encoding="utf-8")))
                self.assertEqual(w3(rec), [])

    # Records that use the exception of the recording rule: record id -> the source that names the
    # address as the submission contact. Empty when this test was written.
    PERSONAL_ADDRESS_EXCEPTIONS = {}

    def test_bundled_records_hold_no_personal_address(self):
        # spec-example: venue-contacts / bundled records hold no personal address
        for f in sorted((PLUGIN / "venues").rglob("*.yaml")):
            rid = str(f.relative_to(PLUGIN / "venues"))[:-5]
            if rid in self.PERSONAL_ADDRESS_EXCEPTIONS:
                continue
            with self.subTest(record=rid):
                rec = va.normalize_dates(yaml.safe_load(f.read_text(encoding="utf-8")))
                self.assertEqual(va.contact_addresses(rec)[0], [])


if __name__ == "__main__":
    unittest.main()
