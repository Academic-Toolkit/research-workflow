## 1. Tests, written first and seen to fail

- [x] 1.1 Status mappings print their status label: test with marker `spec-example: venue-table / status mapping at the newer positions` asserts the three table rows; verified by the test failing before task 2.1
- [x] 1.2 Unrecognised shapes print a question mark and never raise: test with marker `spec-example: venue-table / shapes that raised before the fix round` asserts the five table rows; verified by the test failing before task 2.1
- [x] 1.3 Unrecognised shapes print a question mark and never raise: test with marker `spec-example: venue-table / quartiles format never raises` runs the script with --format quartiles on a record file; verified by the test passing
- [x] 1.4 Additional record shapes are read: test with marker `spec-example: venue-table / web of science decides the indexing cell` asserts the five table rows; verified by the test failing before task 2.2
- [x] 1.5 Additional record shapes are read: test with marker `spec-example: venue-table / single quartile mapping in the quartiles format` asserts the one detail entry; verified by the test failing before task 2.2
- [x] 1.6 Additional record shapes are read: test with marker `spec-example: venue-table / apc kind precedence` asserts the five table rows; verified by the test failing before task 2.2
- [x] 1.7 Additional record shapes are read: test with marker `spec-example: venue-table / length key that holds a mapping wins` asserts the length cell is 未公布; verified by the test failing before task 2.2
- [x] 1.8 Additional record shapes are read: test with marker `spec-example: venue-table / review model in other positions` asserts the two table rows; verified by the test failing before task 2.2
- [x] 1.9 Conference records print not-applicable for journal-only columns: test with marker `spec-example: venue-table / conference metric edge cases` asserts the four table rows; verified by the test failing before task 2.3
- [x] 1.10 Conference records print not-applicable for journal-only columns: test with marker `spec-example: venue-table / conference apc is read like a journal` asserts the three table rows, and the test with marker `spec-example: venue-table / conference journal-only columns` asserts APC is ?; verified by both failing before task 2.3
- [x] 1.11 Rows that the script produced before this change keep their cells: test with marker `spec-example: venue-table / changed record is not compared` builds a baseline row with a wrong hash and asserts it is skipped; verified by the test passing
- [x] 1.12 Publisher cell: test with marker `spec-example: venue-table / publisher short names` asserts the five table rows; verified by the test failing before task 2.5

## 2. Script and fixture changes

- [x] 2.1 Every column is read behind one guard that prints ? on an error, the quartiles format never raises, and status mappings print their label for web_of_science and for the whole review block; verified by tests 1.1 to 1.3 passing [after: 1.12]
- [x] 2.2 The single-mapping quartile, the web_of_science flags, the APC kind, the length keys and the review positions follow the Additional record shapes requirement; verified by tests 1.4 to 1.8 passing [after: 2.1]
- [x] 2.3 A conference prints 不適用 for absent or null metric fields, ? for a metrics block of an unknown shape, and reads APC like a journal; verified by tests 1.9 and 1.10 passing [after: 2.2]
- [x] 2.4 The baseline file carries the SHA-256 of each record file and the comparison skips rows whose record changed; verified by test 1.11 and the test with marker `spec-example: venue-table / baseline rows are unchanged` passing [after: 2.3]
- [x] 2.5 The publisher cell shortens ACM and matches a non-string publisher by its text; verified by test 1.12 passing [after: 2.4]
- [x] 2.6 The whole suite and the record validator pass together: `python3 plugins/research-submission/scripts/validate.py && python3 -m unittest discover -s plugins/research-submission/tests` exits 0 [after: 2.5]

## 3. Guidance and version

- [x] 3.1 The add-venue skill text tells a conference record to leave the five journal-only fields out and to state its APC, names one key for length, and says the esci flag is not shown; verified by a content review of plugins/research-submission/skills/add-venue/SKILL.md against the venue-table spec [after: 2.6]
- [x] 3.2 The plugin version reads 0.8.3 in plugins/research-submission/.claude-plugin/plugin.json and in .claude-plugin/marketplace.json; verified by `grep -c '"version": "0.8.3"'` printing 1 for each file [after: 3.1]

## 4. Findings from the change verification

- [x] 4.1 A list or mapping where a number or text is expected prints ?, a publisher mapping is matched by its name with ACM matched as a whole word, the quartiles format prints no categories for an unreadable record, a status string in the review type does not hide a stated model, and an empty indexing mapping on a conference prints ?; verified by the added rows of the Examples `shapes that raised before the fix round`, `quartiles format never raises`, `review model in other positions`, `publisher short names` and `conference metric edge cases` passing in `python3 -m unittest discover -s plugins/research-submission/tests`
