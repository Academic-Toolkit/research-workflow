## Problem

The second verification round of issue 11 found five medium defects. The new APC price readers accept a boolean, so `value: false` prints a free-of-charge cell. The add-venue skill prescribes a length shape the record schema rejects. An amount read from the new price keys gets a mandatory label from `identity.open_access` on hybrid journals, where the script printed a question mark before. The first of the skill's three writing rules still tells every record to write a status mapping, against the new conference guidance. The spec's status rule for the indexing column reads as covering the older indexing keys, which the script does not handle.

## Root Cause

`bool` is a subclass of `int` in Python and the type check ran after the zero-amount branch. The skill text was changed without running the validator on the shape it names. The APC kind rule was written for the amounts the script read before, then reused for the new keys. The skill's older rule was not revisited when the conference paragraph was added. The spec sentence named the column, not the fields.

## Proposed Solution

- Read a price only when it is a number, never a boolean, and check the type before the zero-amount branch; print `?` otherwise.
- Do not consult `identity.open_access` for an amount taken from `currency_rates` or `list_price_usd`.
- Narrow the indexing status rule to `identity.indexing` itself and `web_of_science`, and say the older keys are unchanged.
- Point the skill's not-published length case at `requirements.length_limit`, add a requirement that prescribed shapes pass the validator, and add the conference exception to the first writing rule.
- Close the remaining low findings: non-text values in the APC currency, the fallback amount, the length unit and the name; a footnote left behind by a failed column; `identity.metrics.indexing` hidden by an empty `identity.indexing`; publisher mappings written with `value`; quartile lists with one unreadable entry; `status: optional` on a status-only amount; and the precondition of the test that depends on a real record.

## Non-Goals (optional)

- The truthiness of `identity.open_access` for amounts written as `amount` (issue 14).
- The older indexing keys' handling of non-boolean values, which predates this work.
- The task row counts in the archived change `idd-11-fix1`.

## Success Criteria

- Each Example of the modified and added requirements has a test with its marker.
- `python3 plugins/research-submission/scripts/validate.py && python3 -m unittest discover -s plugins/research-submission/tests` exits 0.
- The baseline comparison still passes for every unchanged record.

## Impact

- Affected code:
  - Modified: plugins/research-submission/scripts/venue_table.py
  - Modified: plugins/research-submission/tests/test_venue_table.py
  - Modified: plugins/research-submission/skills/add-venue/SKILL.md
  - New: none
  - Removed: none
