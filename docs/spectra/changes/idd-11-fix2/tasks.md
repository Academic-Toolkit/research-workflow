## 1. Tests, written first

- [x] 1.1 Status mappings print their status label: test with marker `spec-example: venue-table / indexing block status mapping` asserts the indexing cell is 未取得; verified by the test passing
- [x] 1.2 Unrecognised shapes print a question mark and never raise: test with marker `spec-example: venue-table / values that are not numbers or text` asserts the seven table rows; verified by the test failing before task 2.1
- [x] 1.3 Unrecognised shapes print a question mark and never raise: test with marker `spec-example: venue-table / failed column leaves no footnote` asserts the cell is ? and no footnote is recorded; verified by the test failing before task 2.1
- [x] 1.4 Additional record shapes are read: test with marker `spec-example: venue-table / apc kind for amounts from the new price keys` asserts the four table rows; verified by the test failing before task 2.2
- [x] 1.5 Additional record shapes are read: test with marker `spec-example: venue-table / quartile list with one unreadable entry` asserts the cell and the detail; verified by the test failing before task 2.2
- [x] 1.6 Conference records print not-applicable for journal-only columns: test with marker `spec-example: venue-table / metrics indexing is still read` asserts the indexing cell is SCIE; verified by the test failing before task 2.2
- [x] 1.7 Publisher cell: the test with marker `spec-example: venue-table / publisher short names` asserts the two added table rows; verified by the test failing before task 2.2
- [x] 1.8 Shapes the add-venue skill prescribes pass the record validator: test with marker `spec-example: venue-table / prescribed length shape validates` runs validate.py on two copies of a record; verified by the test passing
- [x] 1.9 Shapes the add-venue skill prescribes pass the record validator: test with marker `spec-example: venue-table / skill text names the validating shape` reads the skill text; verified by the test failing before task 3.1
- [x] 1.10 The test with marker `spec-example: venue-table / record that raised now builds` first asserts that the record's identity.indexing is still a list, so a later change to the record is reported as a changed precondition; verified by the test passing

## 2. Script changes

- [x] 2.1 A price, a currency, a length unit and a name are read only when they have the expected type, the type check runs before the zero-amount branch, and a column that ends as ? leaves no footnote; verified by tests 1.2 and 1.3 passing [after: 1.10]
- [x] 2.2 An amount from the new price keys never gets 必付 from identity.open_access, a status-only amount honours status optional, a quartile list skips unreadable entries in both outputs, an empty identity.indexing does not hide identity.metrics.indexing, and the publisher cell reads value and matches ACM as a whole word; verified by tests 1.4 to 1.7 passing [after: 2.1]
- [x] 2.3 The whole suite and the record validator pass together: `python3 plugins/research-submission/scripts/validate.py && python3 -m unittest discover -s plugins/research-submission/tests` exits 0 [after: 2.2]

## 3. Guidance

- [x] 3.1 The add-venue skill names requirements.length_limit for a length limit that is not published, its first writing rule excepts the five journal-only fields of a conference record, and its APC sentence matches the APC kind rule; verified by test 1.9 passing and a content review of plugins/research-submission/skills/add-venue/SKILL.md against the venue-table spec [after: 2.3]
