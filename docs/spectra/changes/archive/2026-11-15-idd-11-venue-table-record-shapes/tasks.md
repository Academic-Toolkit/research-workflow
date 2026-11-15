## 1. Baseline and test scaffold

- [x] 1.1 Rows that the script produced before this change keep their cells: store the 23 rows the unchanged script prints for the records on the default branch in plugins/research-submission/tests/fixtures/venue_table_baseline.tsv, one tab-separated row per record with the eleven table cells; verified by the file holding 23 rows and by the recording command being written in the test file's docstring
- [x] 1.2 A test module plugins/research-submission/tests/test_venue_table.py loads venue_table.py as a module and builds a row from an in-memory record, so each Example can be tested without files; verified by `python3 -m unittest discover -s plugins/research-submission/tests` collecting the module [after: 1.1]

## 2. Tests, written first and seen to fail

- [x] 2.1 Status mappings print their status label in every column: test with marker `spec-example: venue-table / review type status mapping` asserts the review cell is 未公布; verified by the test failing before task 3.1 [after: 1.2]
- [x] 2.2 Status mappings print their status label in every column: test with marker `spec-example: venue-table / publisher status mapping` asserts the publisher cell is 未公布 and lacks the text status; verified by the test failing before task 3.1 [after: 1.2]
- [x] 2.3 Unrecognised shapes print a question mark and never raise: test with marker `spec-example: venue-table / indexing as a list` asserts the indexing cell is ?; verified by the test failing before task 3.1 [after: 1.2]
- [x] 2.4 Unrecognised shapes print a question mark and never raise: test with marker `spec-example: venue-table / review type of an unknown mapping` asserts the review cell is ?; verified by the test failing before task 3.1 [after: 1.2]
- [x] 2.5 Additional record shapes are read: test with marker `spec-example: venue-table / web of science flags` asserts the three table rows; verified by the test failing before task 3.2 [after: 1.2]
- [x] 2.6 Additional record shapes are read: test with marker `spec-example: venue-table / single quartile mapping` asserts the cell Q1（SJR）; verified by the test failing before task 3.2 [after: 1.2]
- [x] 2.7 Additional record shapes are read: test with marker `spec-example: venue-table / apc from currency rates` asserts the cell USD 3,390（選付）; verified by the test failing before task 3.2 [after: 1.2]
- [x] 2.8 Additional record shapes are read: test with marker `spec-example: venue-table / apc from list price tiers` asserts the cell USD 1,800（必付）; verified by the test failing before task 3.2 [after: 1.2]
- [x] 2.9 Additional record shapes are read: test with marker `spec-example: venue-table / length limit not published` asserts the length cell is 未公布; verified by the test failing before task 3.2 [after: 1.2]
- [x] 2.10 Additional record shapes are read: test with marker `spec-example: venue-table / review model codes` asserts the three table rows; verified by the test failing before task 3.2 [after: 1.2]
- [x] 2.11 Conference records print not-applicable for journal-only columns: test with marker `spec-example: venue-table / conference journal-only columns` asserts five 不適用 cells and APC 未公布; verified by the test failing before task 3.3 [after: 1.2]
- [x] 2.12 Conference records print not-applicable for journal-only columns: test with marker `spec-example: venue-table / journal with the same gaps` asserts indexing, impact factor and quartile stay ?; verified by the test passing before and after task 3.3 [after: 1.2]
- [x] 2.13 Rows that the script produced before this change keep their cells: test with marker `spec-example: venue-table / baseline rows are unchanged` compares every baseline cell, allowing a change only where the baseline is ? or double_anonymous; verified by the test passing before and after section 3 [after: 1.2]
- [x] 2.14 Rows that the script produced before this change keep their cells: test with marker `spec-example: venue-table / record that raised now builds` runs the script on jnspg/jns-spine and asserts exit 0 and one row; verified by the test failing before task 3.1 [after: 1.2]

## 3. Script changes

- [x] 3.1 Status mappings print their status label and unrecognised shapes print ? without raising, in the review, publisher and indexing getters; verified by tests 2.1 to 2.4 and 2.14 passing [after: 2.14]
- [x] 3.2 The additional shapes for indexing, quartile, APC, length and review are read; verified by tests 2.5 to 2.10 passing [after: 3.1]
- [x] 3.3 A conference record prints 不適用 for the five journal-only columns and 未公布 for a missing APC, with no warning for them; verified by tests 2.11 and 2.12 passing [after: 3.2]
- [x] 3.4 The whole suite and the record validator pass together: `python3 plugins/research-submission/scripts/validate.py && python3 -m unittest discover -s plugins/research-submission/tests` exits 0 [after: 3.3]

## 4. Guidance for new records

- [x] 4.1 The add-venue skill names the standard shape for indexing, APC, length and review type, and states which columns a conference record may leave out, matching the shapes in the venue-table spec; verified by a content review of plugins/research-submission/skills/add-venue/SKILL.md against the spec's Additional record shapes requirement [after: 3.3]

## 5. Findings from the change verification

- [x] 5.1 Status mappings print their status label: test with marker `spec-example: venue-table / fees block status mapping` asserts the APC cell is 未取得; verified by the test failing before task 5.6
- [x] 5.2 Unrecognised shapes print a question mark and never raise: test with marker `spec-example: venue-table / indexing list warns on stderr` runs the script on a record file and asserts the warning line; verified by the test passing
- [x] 5.3 Unrecognised shapes print a question mark and never raise: test with marker `spec-example: venue-table / scalar and list values in metric fields` asserts the six table rows; verified by the test failing before task 5.6
- [x] 5.4 Additional record shapes are read: test with marker `spec-example: venue-table / apc amount with applies_when` asserts the cell USD 3,000（選付）; verified by the test failing before task 5.6
- [x] 5.5 Conference records print not-applicable for journal-only columns: test with marker `spec-example: venue-table / conference columns write no warning` runs the script on a conference record file and asserts stderr names none of the five columns; verified by the test passing
- [x] 5.6 The fees block as a status mapping prints its label, applies_when marks an APC as optional however the amount is written, and scalar or list values in metric fields print ? instead of raising; verified by tests 5.1, 5.3 and 5.4 passing and the baseline test still passing [after: 5.5]
