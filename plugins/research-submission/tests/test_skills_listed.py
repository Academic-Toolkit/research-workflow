"""Every skill of the plugin is named after its directory, described, and listed in the README.

Also checks that updating a record has one owner: update-venue. The other skills point to it
and no longer claim that job themselves.
"""
import re
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
SKILLS = PLUGIN / "skills"
README = PLUGIN / "README.md"


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---\n", text, flags=re.S)
    if match is None:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep and re.fullmatch(r"[a-z_-]+", key):
            fields[key] = value.strip()
    return fields


def skill_dirs() -> list[Path]:
    return sorted(p for p in SKILLS.iterdir() if p.is_dir())


class SkillsAreListed(unittest.TestCase):
    def test_each_skill_has_its_own_name_and_a_description(self) -> None:
        for directory in skill_dirs():
            with self.subTest(skill=directory.name):
                fields = frontmatter(directory / "SKILL.md")
                self.assertEqual(fields.get("name"), directory.name)
                self.assertTrue(fields.get("description"))

    def test_the_readme_lists_each_skill(self) -> None:
        readme = README.read_text(encoding="utf-8")
        for directory in skill_dirs():
            with self.subTest(skill=directory.name):
                self.assertIn(f"| `{directory.name}` |", readme)


class UpdatingARecordHasOneOwner(unittest.TestCase):
    def test_update_venue_exists(self) -> None:
        self.assertTrue((SKILLS / "update-venue" / "SKILL.md").is_file())

    def test_update_venue_states_its_kinds_as_a_closed_list(self) -> None:
        text = (SKILLS / "update-venue" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("封閉列舉", text)
        for kind in ("A", "B", "C", "D", "E"):
            with self.subTest(kind=kind):
                self.assertRegex(text, rf"(?m)^\| {kind} ")

    def test_add_venue_leaves_changed_sources_to_update_venue(self) -> None:
        description = frontmatter(SKILLS / "add-venue" / "SKILL.md")["description"]
        self.assertNotIn("CHANGED", description)
        self.assertIn("update-venue", description)

    def test_submit_to_sends_a_changed_source_to_update_venue(self) -> None:
        text = (SKILLS / "submit-to" / "SKILL.md").read_text(encoding="utf-8")
        row = next(line for line in text.splitlines() if line.startswith("| `CHANGED` |"))
        self.assertIn("update-venue", row)


if __name__ == "__main__":
    unittest.main()
