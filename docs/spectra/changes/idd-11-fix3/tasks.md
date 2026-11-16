## 1. Tests, written first

- [x] 1.1 Publisher cell: the test with marker `spec-example: venue-table / publisher short names` asserts the two added rows; verified by the test failing before task 2.1
- [x] 1.2 Conference records print not-applicable for journal-only columns: a test with marker `spec-example: venue-table / empty indexing of another type` asserts the three rows; verified by the test failing before task 2.1
- [x] 1.3 Additional record shapes are read: the test with marker `spec-example: venue-table / apc kind precedence` asserts the two added rows, and a test with marker `spec-example: venue-table / price keys that yield no price` asserts the four rows; verified by the tests failing before task 2.2
- [x] 1.4 Shapes the add-venue skill prescribes pass the record validator: a test with marker `spec-example: venue-table / skill text on price tiers and unpublished amounts` reads the skill text; verified by the test failing before task 3.1

## 2. Script changes

- [x] 2.1 The publisher cell matches the known names before the whole-word ACM, and an absent or empty identity.indexing does not hide a filled identity.metrics.indexing; verified by tests 1.1 and 1.2 passing [after: 1.4]
- [x] 2.2 A status-only APC amount takes its optional mark from apc_kind without the identity.open_access step, and a price key that yields no price falls through to all_other_articles and a_type; verified by test 1.3 passing [after: 2.1]
- [x] 2.3 The whole suite and the record validator pass together: `python3 plugins/research-submission/scripts/validate.py && python3 -m unittest discover -s plugins/research-submission/tests` exits 0 [after: 2.2]

## 3. Guidance

- [x] 3.1 The APC row of the add-venue skill says that list_price_usd holds only price tiers, that the first USD entry of currency_rates is used, and how an unpublished amount is marked as optional; verified by test 1.4 passing [after: 2.3]

## 4. Checks before archiving

- [x] 4.1 For the spec Example inputs and the probe inputs quoted in the three verification rounds, every cell that differs between the script at 02dad572 and the script after this change maps to an Example; verified by a comparison run whose output lists each differing cell with its Example title [after: 3.1]
- [x] 4.2 The four records that triggered issue 11 build with the script after this change; verified by a run of the script on copies of those records [after: 3.1]

## 5. Findings from the change verification

- [x] 5.1 The spec says only the first USD entry of currency_rates is considered and list_price_usd is used only when every tier is a number, names `amount` as the field whose status mapping gets the status label, the skill's APC row names all_other_articles and a_type for the identity.open_access step, and the prescribed-shapes table covers an unpublished amount and list_price_usd with other keys; verified by the tests with markers `spec-example: venue-table / prescribed column shapes validate` and `spec-example: venue-table / skill text on price tiers and unpublished amounts` passing
