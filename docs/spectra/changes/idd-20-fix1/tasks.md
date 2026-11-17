## 1. Tests, written first

- [ ] 1.1 Contact addresses are classified by position: tests in plugins/research-submission/tests/test_validate_contacts.py with markers `spec-example: venue-contacts / classification by position`, `spec-example: venue-contacts / named persons in every section of the scope`, `spec-example: venue-contacts / what counts as an address`, `spec-example: venue-contacts / an address used as a key` and `spec-example: venue-contacts / a section written as a string or a list` assert every row of the five Examples; verified by the new rows failing before task 2.1
- [ ] 1.2 A record that holds both kinds of address gets warning W3: a test with marker `spec-example: venue-contacts / warning text when a key is an address` asserts the masked path and the absence of `@`, and the test with marker `spec-example: venue-contacts / validator run exits zero with W3` writes the date of the run into every source of its fixture; verified by the key test failing before task 2.1 and by the validator-run test passing when the fixture dates are the only thing changed
- [ ] 1.3 The add-venue skill states the recording rule: the test with marker `spec-example: venue-contacts / skill text on contact addresses` asserts the W3 row, the eight phrases and the absence of the key prescription; verified by the test failing before task 3.1
- [ ] 1.4 The bundled corpus produces no W3: a test with marker `spec-example: venue-contacts / bundled records hold no personal address` classifies every bundled record against an empty exception list; verified by the test passing on the records as they are and failing when a personal address is put back into a copy of one record

## 2. Validator

- [ ] 2.1 The classifier treats a mapping with a string name as a named person in all three sections, uses the address pattern of the spec, classifies a key that holds an address and writes it as `<address>` in field paths; verified by the tests of 1.1 and the key test of 1.2 passing [after: 1.4]

## 3. Guidance and records

- [ ] 3.1 The contact-address section of the add-venue skill states the six parts in Traditional Chinese, says the standard key is undecided and tracked in issue 21, and no longer prescribes a key; verified by test 1.3 passing [after: 2.1]
- [ ] 3.2 The plugin README describes validate.py as having 3 warning lints; verified by a search of plugins/research-submission/README.md for `2 警告` returning nothing [after: 3.1]
- [ ] 3.3 The editor note of `acm/tosem` keeps the quoted words of the author guidelines without the address and no longer suggests writing to the journal administrator; verified by reading the note and by a search of the file for `@` returning only the office address [after: 3.2]
- [ ] 3.4 The editor note of `apa/psychological-methods` gives the reason under the ownership rule: the link the page labels editorial office points to one person's own mailbox, the page gives no office address, and submissions go through the portal, so no address is recorded; verified by reading the note and by the record having no address in the contact scope [after: 3.3]
- [ ] 3.5 The whole suite and the record validator pass together: `python3 plugins/research-submission/scripts/validate.py && python3 -m unittest discover -s plugins/research-submission/tests` exits 0 [after: 3.4]
