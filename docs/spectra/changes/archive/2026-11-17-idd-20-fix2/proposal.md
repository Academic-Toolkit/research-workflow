## Problem

The second verification round of issue 20 found two medium and eight low or informational defects:

- A field path is built by joining keys with dots. Two keys that are not addresses by themselves can join into an address, which W3 then prints.
- A conference record whose `cycle` is a string or a list makes the validator raise in the W1 check, so W3 is never computed for an input the spec names.
- The `requirements.submission` and `cycle` mappings are treated as named persons when they carry a string `name`; only `identity` was exempt.
- The address pattern misses an address that follows a slash and matches a cross-site handle of the form `@name@site`.
- The skill does not say that a record using the exception must be listed in the corpus test, its verification step does not run the test suite, its lint count is out of date, and its list of what W3 does not read is incomplete.
- A note in `ims/annals-of-statistics` makes a claim its source does not state word for word.

## Root Cause

Fix round 1 masked a key only when the key alone held an address, and never checked the joined path. It widened the named-person test to the other two sections without carrying over the exemption of the section root. The W1 check predates this work and assumed `cycle` is a mapping, which the schema requires but the contact scope of the spec does not. The corpus test added in fix round 1 was not mentioned in the skill.

## Proposed Solution

- Write a key as `<key>` when adding it would make the path contain an address.
- Skip the W1 check when `cycle` is not a mapping.
- Exempt all three section roots from the named-person test.
- Forbid `@` directly before the local part and allow `/` before it.
- State in the skill the exception list, the test-suite command, the full list of places W3 does not read, and the current lint count.
- Reduce the `ims/annals-of-statistics` note to a pointer to its source.

## Non-Goals (optional)

- The items tracked in issue 22 and issue 21.
- Telling apart two address keys of the same mapping in a field path (both are written `<address>`).

## Success Criteria

- Each Example of the modified requirements has a test with its marker.
- `python3 plugins/research-submission/scripts/validate.py && python3 -m unittest discover -s plugins/research-submission/tests` exits 0.

## Impact

- Affected specs: `venue-contacts` (three requirements modified)
- Affected code:
  - Modified: plugins/research-submission/scripts/validate.py
  - Modified: plugins/research-submission/tests/test_validate_contacts.py
  - Modified: plugins/research-submission/skills/add-venue/SKILL.md
  - Modified: plugins/research-submission/venues/ims/annals-of-statistics.yaml
  - New: none
  - Removed: none
