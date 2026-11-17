## 1. Tests, written first

- [x] 1.1 Contact addresses are classified by position: a test in plugins/research-submission/tests/test_validate_contacts.py with marker `spec-example: venue-contacts / classification by position` asserts the kind and field path of each of the twelve rows; verified by the test failing before task 2.1
- [x] 1.2 A record that holds both kinds of address gets warning W3: tests with markers `spec-example: venue-contacts / one warning naming the personal paths`, `spec-example: venue-contacts / one kind only gives no warning` and `spec-example: venue-contacts / validator run exits zero with W3` assert the warning text, the four no-warning rows, and the exit status and summary line of a validator run on a temporary record file; verified by the tests failing before task 2.2
- [x] 1.3 The add-venue skill states the recording rule: a test with marker `spec-example: venue-contacts / skill text on contact addresses` reads the skill text and asserts the W3 row and the four phrases; verified by the test failing before task 3.1
- [x] 1.4 The bundled corpus produces no W3: a test with marker `spec-example: venue-contacts / bundled records have no W3` computes the warnings of every bundled record; verified by the test failing before tasks 4.1 and 4.2 (two records hold both kinds today)

## 2. Validator

- [x] 2.1 The validator module exposes a function that returns the personal and office field paths of a record under the position rule of the spec (scope `identity`, `requirements.submission`, `cycle`; named-person mappings only under `identity` and never `identity` itself; list positions written as `[i]`); verified by test 1.1 passing [after: 1.4]
- [x] 2.2 `lint_warnings` returns one `[W3]` warning for a record with both kinds, listing the personal field paths in document order and no address; verified by the three tests of 1.2 passing [after: 2.1]

## 3. Guidance

- [x] 3.1 The add-venue skill has a section on contact addresses that states the four parts of the rule in Traditional Chinese, and its warning table has a W3 row; verified by test 1.3 passing [after: 2.2]

## 4. Records

- [x] 4.1 `acm/tosem` no longer holds the personal address of the editor or of the former editor: the editor entry keeps name, title and source, its note points to the source instead of quoting the address, and the office address under `identity.journal_administrator` is unchanged; verified by the record producing no W3 and by a search of the file for `@` returning only the office address [after: 3.1]
- [x] 4.2 `biometrika-trust/biometrika` holds its editor mailbox as an office address outside the editor entry (it is already in `requirements.submission.queries`); the editor entry keeps name, note and source; verified by the record producing no W3 and by the mailbox still appearing in the file [after: 4.1]
- [x] 4.3 `asa/jcgs` holds its office mailbox under `identity.editorial_office.email` with its source, and the coordinator entry keeps the name only; verified by the classification function returning that path as office and no personal path for the record [after: 4.2]
- [x] 4.4 `ims/annals-of-statistics` no longer holds the personal address of the production editor (the role handles production after acceptance, not submission queries); the entry keeps name and source; verified by a search of the file for `@` returning nothing [after: 4.3]
- [x] 4.5 `ase/ase` no longer quotes the two personal addresses in its preprint-policy note; the note says the call page lists contact addresses and points to the source; verified by a search of the file for `@` returning nothing [after: 4.4]
- [x] 4.6 `apa/psychological-methods` no longer holds the personal address of the editor. The submit page, read on 2026-11-17, sends submissions through the portal and says general correspondence goes to the editorial office through a link whose target is the personal address of a person other than the current editor; the record keeps the editor's name and source and gains a note with that finding and no address. ASSUMPTION: the editor's address on that page is a link on the name, not a stated way to reach the journal about a submission, so the exception in the rule does not apply; verified by the classification function returning no personal path for the record [after: 4.5]
- [x] 4.7 The whole suite, the record validator and the venue table baseline pass together: `python3 plugins/research-submission/scripts/validate.py && python3 -m unittest discover -s plugins/research-submission/tests` exits 0, and test 1.4 passes [after: 4.6]

## 5. Version

- [x] 5.1 The plugin manifest and the marketplace entry both read version 0.8.4; verified by a search for `0.8.3` in plugins/research-submission/.claude-plugin/plugin.json and .claude-plugin/marketplace.json returning nothing [after: 4.7]
