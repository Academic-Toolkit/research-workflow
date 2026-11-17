## Problem

The first verification round of issue 20 found one high, six medium and five low defects in the contact-address change:

- The rule text contradicts itself. It says an address the site lists as a contact window is an office address, and also says a personal address is recorded only when the site gives no office address; under the first sentence the second never applies.
- The add-venue skill names the key an office address goes in, which issue 21 has not decided, and tells writers to keep personal addresses out of notes and warnings, which no requirement states.
- Mappings under `cycle` are never treated as named persons, although the maintainer's decision names chairs as persons.
- The skill states that a mapping with a `name` under `identity` is a person; organisation mappings have the same shape.
- A mapping key that is itself an address is printed in the W3 text. The address pattern matches a URL that holds an `@` handle.
- The validator-run test reads a bundled record whose sources become stale on a fixed date, after which the test fails.
- Four of the six record edits were never guarded by a requirement or a test, and the earlier proposal gave the wrong reason for them.
- Two record notes and the plugin README need wording fixes.

## Root Cause

The rule was written from the maintainer's first decision, which answered a narrower question (whether a mailbox opened on a free mail service counts as an office address), and its wording was taken as the definition. The classifier scope and the address pattern were written for the shapes in the corpus and not for the shapes a writer can produce. The validator-run test reused a live record instead of controlling its dates.

## Proposed Solution

- State the rule by ownership, as the maintainer decided on 2026-11-17: a mailbox that belongs to a role or desk and passes to the successor is an office address, whatever its domain; a mailbox that belongs to one person is a personal address even when the site lists it as a contact.
- Remove the key prescription from the skill and say the canonical key is open in issue 21. Put the notes-and-warnings sentence into the requirement.
- Treat a mapping with a string `name` as a named person in all three sections of the contact scope, and state that the rule cannot tell a person from an organisation.
- Tighten the address pattern, classify a key that holds an address like a string at that position, and write such a key as `<address>` in field paths.
- Give the validator-run test fresh verification dates.
- Require that no bundled record holds a personal address unless the test lists it as an exception, with an empty list today.
- Correct the earlier proposal's statement here: only `acm/tosem` and `biometrika-trust/biometrika` produced W3 before the clean-up; `asa/jcgs`, `ims/annals-of-statistics` and `apa/psychological-methods` held only a personal-position address, and `ase/ase` held addresses outside the contact scope.

## Non-Goals (optional)

- One canonical shape for the office address (issue 21).
- A person written as a plain string or with a non-string name, addresses written with a full-width at-sign or `[at]`, addresses in prose outside the contact scope, and the running time of the pattern on long strings (issue 22).
- Editing the archived change `idd-20-office-address-rule`.

## Success Criteria

- Each Example of the modified requirements has a test with its marker.
- `python3 plugins/research-submission/scripts/validate.py && python3 -m unittest discover -s plugins/research-submission/tests` exits 0.
- The validator-run test passes with the system date moved two years ahead of every source date in its fixture, because the fixture carries the date of the run.

## Impact

- Affected specs: `venue-contacts` (all four requirements modified)
- Affected code:
  - Modified: plugins/research-submission/scripts/validate.py
  - Modified: plugins/research-submission/tests/test_validate_contacts.py
  - Modified: plugins/research-submission/skills/add-venue/SKILL.md
  - Modified: plugins/research-submission/README.md
  - Modified: plugins/research-submission/venues/acm/tosem.yaml
  - Modified: plugins/research-submission/venues/apa/psychological-methods.yaml
  - New: none
  - Removed: none
