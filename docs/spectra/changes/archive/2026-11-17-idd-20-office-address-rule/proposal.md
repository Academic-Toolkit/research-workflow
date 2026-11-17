## Why

Venue records hold contact addresses with no rule about which kind to record. Some records carry an editor's own address inside the editor's entry while the same record also has an editorial office address; others carry an office mailbox inside a named person's entry. An editor's own address goes stale when the editor changes, and a public corpus has no use for it when the venue publishes an office address. Issue 20 asks for a rule, a check, and a clean-up of the existing records. The maintainer decided two points on 2026-11-17: an address is an office address by what the venue uses it for, not by its domain; and the validator tells the two kinds apart by where the address sits in the record.

## What Changes

- The record validator `plugins/research-submission/scripts/validate.py` gains warning W3: a record that holds both a personal address and an office address gets one warning that names the field paths of the personal addresses and prints no address. Like W1 and W2 it does not change the exit status.
- The add-venue skill states the rule: record the office address when the venue publishes one; record a personal address only when the official site gives no office address and names that address as the way to reach the venue about a submission, with its source; never place an office address inside a named person's entry. Its warning table lists W3.
- Six existing records are brought in line with the rule, so the bundled corpus produces no W3.
- The plugin version goes from 0.8.3 to 0.8.4.

## Non-Goals (optional)

- One canonical shape for the office address (three shapes exist today); tracked in issue 21.
- Addresses inside `warnings`, `sources` and the parts of `requirements` other than `requirements.submission`: W3 does not read them. The clean-up still removes personal addresses found there by hand.
- Rewriting published git history.
- Judging by domain whether an address belongs to a person. A personal address written into an office field is not detected; the skill text is the only guard.

## Capabilities

### New Capabilities

- `venue-contacts`: how contact addresses in a venue record are classified as personal or office by position, the W3 warning, and the recording rule the add-venue skill states

### Modified Capabilities

(none)

## Impact

- Affected specs: new `venue-contacts`
- Affected code:
  - plugins/research-submission/scripts/validate.py
  - plugins/research-submission/skills/add-venue/SKILL.md
  - plugins/research-submission/tests/test_validate_contacts.py (new)
  - plugins/research-submission/venues/acm/tosem.yaml
  - plugins/research-submission/venues/apa/psychological-methods.yaml
  - plugins/research-submission/venues/asa/jcgs.yaml
  - plugins/research-submission/venues/ase/ase.yaml
  - plugins/research-submission/venues/biometrika-trust/biometrika.yaml
  - plugins/research-submission/venues/ims/annals-of-statistics.yaml
  - the plugin manifest and marketplace entry that carry the version
