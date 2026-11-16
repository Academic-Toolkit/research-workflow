## Problem

The third verification round of issue 11 found three medium defects and several low ones. Fix round 2 made the whole-word `ACM` match run before the known publisher names, so `Springer on behalf of ACM SIGLOG` prints `ACM` where it printed `Springer Nature` before. Every numeric value of `list_price_usd` is read as a price tier, so a stray number such as a year becomes the price. The spec promises `?` for an unrecognised shape in every column, while a few sub-fields still print raw values as they did before this work. Fix round 2 also narrowed the indexing fallback to the empty mapping, gave a status-only APC amount its own optional rule, and made a price key that yields no price hide the older amount shapes.

## Root Cause

Fix round 2 added branches beside the rules in force before this work instead of restoring them: the `ACM` check was put ahead of the existing loop, the indexing fallback was rewritten as a new condition instead of the original truthiness test, and the status-only amount got a second precedence rule. The spec sentence for unrecognised shapes was written for the whole table, while only the fields this capability names were changed.

## Proposed Solution

- Match the known publisher names first and the whole-word `ACM` only when none matches.
- Read `identity.metrics.indexing` whenever `identity.indexing` is absent or empty, as the original truthiness test did.
- Decide the optional mark of a status-only amount with the same order as a known amount, without the `identity.open_access` step.
- Let a price key that yields no price fall through to `all_other_articles` and `a_type`.
- Narrow the unrecognised-shape requirement to the fields this capability names, list the sub-fields that keep their earlier output, and track them in issue 17.
- State in the spec and the add-venue skill that `list_price_usd` holds only price tiers, that the first USD entry of `currency_rates` is used, and that skipped quartile entries write no warning.

## Non-Goals (optional)

- Type checks for `recommended_range`, the acceptance-rate sub-fields and the `--format quartiles` detail (issue 17).
- The truthiness of `identity.open_access` for amounts written as `amount` (issue 14).
- The archived changes `idd-11-fix1` and `idd-11-fix2`.

## Success Criteria

- Each Example of the modified requirements has a test with its marker.
- `python3 plugins/research-submission/scripts/validate.py && python3 -m unittest discover -s plugins/research-submission/tests` exits 0.
- The baseline comparison still passes for every unchanged record.
- For the spec Example inputs and the probe inputs quoted in the three verification rounds, every cell where the script before this work and the script after this change differ maps to an Example.

## Impact

- Affected code:
  - Modified: plugins/research-submission/scripts/venue_table.py
  - Modified: plugins/research-submission/tests/test_venue_table.py
  - Modified: plugins/research-submission/skills/add-venue/SKILL.md
  - New: none
  - Removed: none
