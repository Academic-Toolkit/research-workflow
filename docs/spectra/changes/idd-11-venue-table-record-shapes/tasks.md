## 1. Baseline and test scaffold

- [ ] 1.1 Rows that the script produced before this change keep their cells: store the 23 rows the unchanged script prints for the records on the default branch in plugins/research-submission/tests/fixtures/venue_table_baseline.tsv, one tab-separated row per record with the eleven table cells; verified by the file holding 23 rows and by the recording command being written in the test file's docstring
- [ ] 1.2 A test module plugins/research-submission/tests/test_venue_table.py loads venue_table.py as a module and builds a row from an in-memory record, so each Example can be tested without files; verified by `python3 -m unittest discover -s plugins/research-submission/tests` collecting the module [after: 1.1]

## 2. Tests, written first and seen to fail

- [ ] 2.1 Status mappings print their status label in every column: test with marker `spec-example: venue-table / review type status mapping` asserts the review cell is 未公布; verified by the test failing before task 3.1 [after: 1.2]
- [ ] 2.2 Status mappings print their status label in every column: test with marker `spec-example: venue-table / publisher status mapping` asserts the publisher cell is 未公布 and lacks the text status; verified by the test failing before task 3.1 [after: 1.2]
- [ ] 2.3 Unrecognised shapes print a question mark and never raise: test with marker `spec-example: venue-table / indexing as a list` asserts the indexing cell is ?; verified by the test failing before task 3.1 [after: 1.2]
- [ ] 2.4 Unrecognised shapes print a question mark and never raise: test with marker `spec-example: venue-table / review type of an unknown mapping` asserts the review cell is ?; verified by the test failing before task 3.1 [after: 1.2]
- [ ] 2.5 Additional record shapes are read: test with marker `spec-example: venue-table / web of science flags` asserts the three table rows; verified by the test failing before task 3.2 [after: 1.2]
- [ ] 2.6 Additional record shapes are read: test with marker `spec-example: venue-table / single quartile mapping` asserts the cell Q1（SJR）; verified by the test failing before task 3.2 [after: 1.2]
- [ ] 2.7 Additional record shapes are read: test with marker `spec-example: venue-table / apc from currency rates` asserts the cell USD 3,390（選付）; verified by the test failing before task 3.2 [after: 1.2]
- [ ] 2.8 Additional record shapes are read: test with marker `spec-example: venue-table / apc from list price tiers` asserts the cell USD 1,800（必付）; verified by the test failing before task 3.2 [after: 1.2]
- [ ] 2.9 Additional record shapes are read: test with marker `spec-example: venue-table / length limit not published` asserts the length cell is 未公布; verified by the test failing before task 3.2 [after: 1.2]
- [ ] 2.10 Additional record shapes are read: test with marker `spec-example: venue-table / review model codes` asserts the three table rows; verified by the test failing before task 3.2 [after: 1.2]
- [ ] 2.11 Conference records print not-applicable for journal-only columns: test with marker `spec-example: venue-table / conference journal-only columns` asserts five 不適用 cells and APC 未公布; verified by the test failing before task 3.3 [after: 1.2]
- [ ] 2.12 Conference records print not-applicable for journal-only columns: test with marker `spec-example: venue-table / journal with the same gaps` asserts indexing, impact factor and quartile stay ?; verified by the test passing before and after task 3.3 [after: 1.2]
- [ ] 2.13 Rows that the script produced before this change keep their cells: test with marker `spec-example: venue-table / baseline rows are unchanged` compares every baseline cell, allowing a change only where the baseline is ? or double_anonymous; verified by the test passing before and after section 3 [after: 1.2]
- [ ] 2.14 Rows that the script produced before this change keep their cells: test with marker `spec-example: venue-table / record that raised now builds` runs the script on jnspg/jns-spine and asserts exit 0 and one row; verified by the test failing before task 3.1 [after: 1.2]

## 3. Script changes

- [ ] 3.1 Status mappings print their status label and unrecognised shapes print ? without raising, in the review, publisher and indexing getters; verified by tests 2.1 to 2.4 and 2.14 passing [after: 2.14]
- [ ] 3.2 The additional shapes for indexing, quartile, APC, length and review are read; verified by tests 2.5 to 2.10 passing [after: 3.1]
- [ ] 3.3 A conference record prints 不適用 for the five journal-only columns and 未公布 for a missing APC, with no warning for them; verified by tests 2.11 and 2.12 passing [after: 3.2]
- [ ] 3.4 The whole suite and the record validator pass together: `python3 plugins/research-submission/scripts/validate.py && python3 -m unittest discover -s plugins/research-submission/tests` exits 0 [after: 3.3]

## 4. Guidance for new records

- [ ] 4.1 The add-venue skill names the standard shape for indexing, APC, length and review type, and states which columns a conference record may leave out, matching the shapes in the venue-table spec; verified by a content review of plugins/research-submission/skills/add-venue/SKILL.md against the spec's Additional record shapes requirement [after: 3.3]
