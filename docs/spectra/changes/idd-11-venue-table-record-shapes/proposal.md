## Problem

`plugins/research-submission/scripts/venue_table.py` cannot produce a comparison table for records written by `add-venue` when a record uses a field shape the script does not know. Two shapes make it crash (`requirements.review.type` holding a status mapping; `identity.indexing` holding a list). Several others print `?`. Conference records print `?` in columns that do not apply to a conference, and a publisher recorded as a status mapping is printed as a raw Python dict.

The `venue-report` skill forbids copying table values by hand, so a record the script cannot read blocks the report.

## Root Cause

Each getter accepts a fixed set of field shapes and assumes the record is a journal. `review()` and `wos()` use the value before checking its type. `publisher()` calls `str()` on whatever it finds. Nothing reads `kind`. The `add-venue` skill names standard shapes only for `identity.metrics`, so records written by different agents differ in indexing, fees, length and review fields.

## Proposed Solution

- A value that is a status mapping (`status` is `not_published`, `not_found` or `not_applicable`) prints the label for that status in every column, including review and publisher.
- A value of an unrecognised shape prints `?` with a warning on stderr and never raises.
- The script recognises these additional shapes: `identity.indexing.web_of_science` with `scie` and `ssci` flags; `quartiles` as one mapping with `system` and `value` or `quartile`; `fees.apc.currency_rates` with a USD entry; `fees.apc.list_price_usd`; `requirements.length_limit`; `requirements.review.model` and `requirements.review.model_by_track.research`, with `double_anonymous` and `double-anonymous` read as double-anonymized.
- For a record whose `kind` is `conference`, the indexing, impact factor, quartile and both review-time columns print the not-applicable label when the record does not state them; the APC column prints the not-published label when the record has no fee information.
- `plugins/research-submission/skills/add-venue/SKILL.md` states the standard shapes for indexing, APC, length and review type, and which columns a conference record may leave out.

## Non-Goals (optional)

- Rewriting existing records to one shape. The script reads the shapes that exist; the skill text guides new records.
- Conference support in `choose-venue` and `venue_topic_scan.py` (tracked separately in issue 12).
- The page-unit label. `main` already prints `pages_typeset` as typeset pages.

## Success Criteria

- The script exits 0 and prints no `?` for the four records that exposed the problem (two software-engineering journals, two conferences), reproduced as minimal fixtures in the tests.
- `jnspg/jns-spine`, which crashes on `main`, produces a row.
- For the 23 records that produce a row on `main`, every cell is unchanged unless it was `?` before.
- `python3 -m unittest discover -s plugins/research-submission/tests` passes, and each test fails on `main` before the script change.

## Impact

- Affected code:
  - Modified: plugins/research-submission/scripts/venue_table.py
  - Modified: plugins/research-submission/skills/add-venue/SKILL.md
  - New: plugins/research-submission/tests/test_venue_table.py
  - Removed: none
