## Purpose

The venue table is the comparison table that `plugins/research-submission/scripts/venue_table.py` builds from venue records, so that reports never copy values by hand. This capability states how a record field of each known shape, of an unknown shape, or of a conference record appears in a table cell.

## ADDED Requirements

### Requirement: Status mappings print their status label

When a field read for the publisher, indexing, impact factor, APC or review column holds a mapping whose `status` is `not_published`, `not_found` or `not_applicable` and that carries no `value` or `amount`, the script SHALL print the label of that status (`未公布`, `未取得`, `不適用`) in that column and SHALL NOT raise. For the APC column this SHALL also hold when `requirements.fees` itself is such a mapping. The quartile, acceptance rate, review time and length columns keep the labels they printed before this change; aligning them is outside this change.

#### Scenario: Review type recorded as not published

- **WHEN** `requirements.review.type` is a mapping with `status: not_published`
- **THEN** the review cell is `未公布` and the script exits 0

##### Example: review type status mapping

- **GIVEN** a journal record whose `requirements.review.type` is `{status: not_published, checked: 2026-11-15}`
- **WHEN** the row is built
- **THEN** the review cell is `未公布`

##### Example: fees block status mapping

- **GIVEN** a conference record whose `requirements.fees` is `{status: not_found, checked: 2026-11-15}`
- **WHEN** the row is built
- **THEN** the APC cell is `未取得`

##### Example: publisher status mapping

- **GIVEN** a conference record whose `identity.publisher` is `{status: not_published, checked: 2026-11-15, note: "electronic proceedings"}`
- **WHEN** the row is built
- **THEN** the publisher cell is `未公布`, and the cell does not contain the text `status`

### Requirement: Unrecognised shapes print a question mark and never raise

When a field read for a table column holds a value whose shape the script does not recognise, the script SHALL print `?` in that column, SHALL write one warning line naming the record and the column to stderr, and SHALL exit 0.

#### Scenario: Indexing recorded as a list

- **WHEN** `identity.indexing` is a list
- **THEN** the indexing cell is `?`, a warning for that column is on stderr, and the script exits 0

##### Example: indexing as a list

- **GIVEN** a journal record whose `identity.indexing` is `["Scopus", "PubMed"]`
- **WHEN** the row is built
- **THEN** the indexing cell is `?`

##### Example: indexing list warns on stderr

- **GIVEN** a record file whose `identity.indexing` is a list
- **WHEN** the script is run on that record
- **THEN** stderr contains one line naming the record and the column `收錄`

##### Example: scalar and list values in metric fields

| Field | Value | Cell | Result |
| ----- | ----- | ---- | ------ |
| identity.metrics.quartiles | "Q1" | quartile | ? |
| identity.metrics.quartiles | ["Q1"] | quartile | ? |
| identity.metrics.impact_factor | [1] | impact factor | ? |
| identity.metrics.acceptance_rate | [1] | acceptance rate | ? |
| identity.metrics | ["x"] | impact factor | ? |
| requirements | ["x"] | length | ? |

##### Example: review type of an unknown mapping

- **GIVEN** a journal record whose `requirements.review.type` is `{kind: custom}`
- **WHEN** the row is built
- **THEN** the review cell is `?`

### Requirement: Additional record shapes are read

The script SHALL read the shapes below in addition to the shapes it read before this change.

- Indexing: `identity.indexing.web_of_science` with boolean `scie` and `ssci`.
- Quartile: `identity.metrics.quartiles` as one mapping with `system` and either `quartile` or `value`.
- APC: `requirements.fees.apc.currency_rates`, a list of `{currency, value}`, from which the USD entry is taken; and `requirements.fees.apc.list_price_usd`, a mapping of price tiers, from which the highest amount is taken. ASSUMPTION: the highest tier is the undiscounted list price.
- Length: `requirements.length_limit`, read the same way as `requirements.length`.
- Review: `requirements.review.model`, and `requirements.review.model_by_track.research` when neither `type` nor `model` is present.
- Review codes `double_anonymous` and `double-anonymous` SHALL print `雙匿名`.
- APC kind: an `apc` mapping that carries `applies_when` and does not set `mandatory: true` SHALL print `選付`, whichever way the amount is written.

#### Scenario: Web of Science flags

- **WHEN** `identity.indexing.web_of_science` is `{scie: true, ssci: false}`
- **THEN** the indexing cell is `SCIE`

##### Example: web of science flags

| scie | ssci | Indexing cell |
| ---- | ---- | ------------- |
| true | false | SCIE |
| true | true | SCIE＋SSCI |
| false | false | 兩者皆無 |

##### Example: single quartile mapping

- **GIVEN** `identity.metrics.quartiles` is `{system: SJR, category: Software, value: Q1, year: 2025}`
- **WHEN** the row is built
- **THEN** the quartile cell is `Q1（SJR）`

##### Example: apc from currency rates

- **GIVEN** `requirements.fees.apc` is `{applies_when: "author chooses open access", currency_rates: [{currency: GBP, value: 2390}, {currency: USD, value: 3390}]}`
- **WHEN** the row is built
- **THEN** the APC cell is `USD 3,390（選付）`

##### Example: apc amount with applies_when

- **GIVEN** `requirements.fees.apc` is `{amount: 3000, currency: USD, applies_when: "author chooses open access"}`
- **WHEN** the row is built
- **THEN** the APC cell is `USD 3,000（選付）`

##### Example: apc from list price tiers

- **GIVEN** `requirements.fees.apc` is `{mandatory: true, list_price_usd: {member: 1300, non_member: 1800}}`
- **WHEN** the row is built
- **THEN** the APC cell is `USD 1,800（必付）`

##### Example: length limit not published

- **GIVEN** `requirements.length_limit` is `{status: not_published, checked: 2026-11-15}` and the record has no `requirements.length`
- **WHEN** the row is built
- **THEN** the length cell is `未公布`

##### Example: review model codes

| Field | Value | Review cell |
| ----- | ----- | ----------- |
| requirements.review.model | double_anonymous | 雙匿名 |
| requirements.review.model_by_track.research | double-anonymous | 雙匿名 |
| requirements.review.type | single_blind | 單盲 |

### Requirement: Conference records print not-applicable for journal-only columns

For a record whose `kind` is `conference`, when the record does not state the field for a column, the script SHALL print `不適用` in the indexing, impact factor, quartile, time to first decision and submission to acceptance columns, and SHALL print `未公布` in the APC column. A value the conference record does state SHALL be printed by the same rules as for a journal. No warning SHALL be written for these columns.

#### Scenario: Conference without journal metrics

- **WHEN** a conference record has no `identity.indexing`, no impact factor, no quartiles, no review times and no `requirements.fees`
- **THEN** those five columns are `不適用`, the APC column is `未公布`, and stderr has no warning for them

##### Example: conference journal-only columns

- **GIVEN** a record with `kind: conference`, `identity.metrics` holding only `acceptance_rate: {status: not_published}`, and no `requirements.fees`
- **WHEN** the row is built
- **THEN** indexing, impact factor, quartile, first decision and submission-to-acceptance are each `不適用`, and APC is `未公布`

##### Example: conference columns write no warning

- **GIVEN** a conference record file with no `identity.indexing`, no impact factor, no quartiles and no review times
- **WHEN** the script is run on that record
- **THEN** stderr has no warning line for `收錄`, `IF`, `分區`, `首次決定（中位）` or `投稿→接受（中位）`

##### Example: journal with the same gaps

- **GIVEN** a record with `kind: journal` and the same missing fields
- **WHEN** the row is built
- **THEN** indexing, impact factor and quartile are each `?`

### Requirement: Rows that the script produced before this change keep their cells

For the records present on the default branch when this change was written, a cell SHALL stay the same after this change unless the cell was `?` before, or the cell was the raw review code `double_anonymous`. A record that made the script raise before this change SHALL produce a row.

#### Scenario: Baseline comparison

- **WHEN** the table is built for every record that has a stored baseline row
- **THEN** each cell equals the baseline cell, except cells whose baseline is `?` or `double_anonymous`

##### Example: baseline rows are unchanged

- **GIVEN** the baseline file `plugins/research-submission/tests/fixtures/venue_table_baseline.tsv`, holding the 23 rows the script produced on the default branch
- **WHEN** each of those records is built again
- **THEN** every cell equals its baseline, except where the baseline cell is `?` or `double_anonymous`

##### Example: record that raised now builds

- **GIVEN** the record `jnspg/jns-spine`, whose `identity.indexing` is a list
- **WHEN** the table is built for it
- **THEN** the script exits 0 and prints one row
