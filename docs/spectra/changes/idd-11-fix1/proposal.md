## Problem

The first verification round of issue 11 found that the change `idd-11-venue-table-record-shapes` introduced one crash (a single-mapping quartile whose value is not a quartile string), reads `web_of_science` flags by truthiness so that non-boolean values print a confident indexing claim, and leaves the precedence between `web_of_science` and the older indexing keys unstated. It also found columns that still raise or print a Python representation, a conference APC default inferred from a missing field, status mappings that print `?` at positions the new aliases read, an APC kind rule decided in two places, and a baseline test tied to record files that will change.

## Root Cause

The new aliases tested values for truthiness instead of checking their type, and each column guarded its own shapes one by one, so every unguarded shape was a new crash or a wrong cell. The conference APC default stated a fact the record does not state. The baseline test compared a frozen output with live input.

## Proposed Solution

- Read every column behind one guard, so an error in a column prints `?` for that column and never stops the table; the quartiles format gets the same guard.
- Accept the single-mapping quartile only for the strings Q1 to Q4, and `web_of_science` only with two boolean flags; state that `web_of_science` decides the cell when present.
- Print status labels for `web_of_science` and for the whole review block; let a stated review model show through a status-only type.
- Remove the conference APC default; a conference record states its APC as an amount or a status mapping.
- Keep a conference's not-applicable default for absent or null metric fields, and print `?` when the metrics block has an unknown shape.
- Decide the APC kind in one place with a stated order.
- Store the record file's SHA-256 with each baseline row and compare only unchanged records.
- Shorten ACM in the publisher cell and match non-string publishers by their text as before.
- Update the add-venue skill text to match, and raise the plugin version to 0.8.3.

## Non-Goals (optional)

- TeX escaping of record text in the LaTeX output, which predates this work and is tracked separately.
- Status labels in the quartile, acceptance rate, review time and length columns (issue 13).

## Success Criteria

- Each Example of the modified and added requirements has a test with its marker, and each new test fails on the commit before this change.
- `python3 plugins/research-submission/scripts/validate.py && python3 -m unittest discover -s plugins/research-submission/tests` exits 0.
- The baseline comparison still passes for every unchanged record.

## Impact

- Affected code:
  - Modified: plugins/research-submission/scripts/venue_table.py
  - Modified: plugins/research-submission/tests/test_venue_table.py
  - Modified: plugins/research-submission/tests/fixtures/venue_table_baseline.tsv
  - Modified: plugins/research-submission/skills/add-venue/SKILL.md
  - Modified: plugins/research-submission/.claude-plugin/plugin.json
  - Modified: .claude-plugin/marketplace.json
  - New: none
  - Removed: none
