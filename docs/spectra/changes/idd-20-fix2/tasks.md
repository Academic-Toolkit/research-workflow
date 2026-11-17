## 1. Tests, written first

- [ ] 1.1 Contact addresses are classified by position: the tests in plugins/research-submission/tests/test_validate_contacts.py with markers `spec-example: venue-contacts / named persons in every section of the scope` and `spec-example: venue-contacts / what counts as an address` assert the added rows, and a test with marker `spec-example: venue-contacts / keys that would join into an address` asserts the masked path; verified by the new rows and the new test failing before task 2.1
- [ ] 1.2 A record that holds both kinds of address gets warning W3: a test with marker `spec-example: venue-contacts / a conference record whose cycle is a list` asserts one W3 and no error; verified by the test raising AttributeError before task 2.1
- [ ] 1.3 The add-venue skill states the recording rule: the test with marker `spec-example: venue-contacts / skill text on contact addresses` asserts the two added phrases; verified by the test failing before task 3.1

## 2. Validator

- [ ] 2.1 The classifier exempts the three section roots from the named-person test, forbids an at-sign directly before the local part and allows a slash there, writes a key as `<key>` when adding it would make the path contain an address, and the W1 check skips a cycle that is not a mapping; the module description states four error lints and three warning lints; verified by the tests of 1.1 and 1.2 passing [after: 1.3]

## 3. Guidance and records

- [ ] 3.1 The add-venue skill names the exception list of the corpus test, tells the writer in its verification step to run the test suite, lists warnings, sources, the other parts of requirements and YAML comments as places W3 does not read, and states the current number of lints; verified by test 1.3 passing and by a search of the skill for `5 條 lint` returning nothing [after: 2.1]
- [ ] 3.2 The production-editor note of `ims/annals-of-statistics` only says that the personal address is not recorded and points to the source; verified by reading the note [after: 3.1]
- [ ] 3.3 The whole suite and the record validator pass together: `python3 plugins/research-submission/scripts/validate.py && python3 -m unittest discover -s plugins/research-submission/tests` exits 0 [after: 3.2]
