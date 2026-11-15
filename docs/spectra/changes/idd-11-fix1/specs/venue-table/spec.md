## MODIFIED Requirements

### Requirement: Status mappings print their status label

When a field read for the publisher, indexing, impact factor, APC or review column holds a mapping whose `status` is `not_published`, `not_found` or `not_applicable` and that carries no `value` or `amount`, the script SHALL print the label of that status (`未公布`, `未取得`, `不適用`) in that column and SHALL NOT raise. For the APC column this SHALL also hold when `requirements.fees` itself is such a mapping, for the indexing column when `identity.indexing.web_of_science` is such a mapping, and for the review column when `requirements.review` itself is such a mapping. A status mapping in `requirements.review.type` SHALL NOT hide a review model the record states in `requirements.review.model` or `requirements.review.model_by_track.research`. The quartile, acceptance rate, review time and length columns keep the labels they printed before this change; aligning them is outside this change.

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

##### Example: status mapping at the newer positions

| Field | Value | Column | Cell |
| ----- | ----- | ------ | ---- |
| identity.indexing.web_of_science | {status: not_found} | indexing | 未取得 |
| requirements.review | {status: not_published} | review | 未公布 |
| requirements.review | {type: {status: not_published}, model: double_anonymous} | review | 雙匿名 |

##### Example: publisher status mapping

- **GIVEN** a conference record whose `identity.publisher` is `{status: not_published, checked: 2026-11-15, note: "electronic proceedings"}`
- **WHEN** the row is built
- **THEN** the publisher cell is `未公布`, and the cell does not contain the text `status`

---

### Requirement: Unrecognised shapes print a question mark and never raise

When a field read for a table column holds a value whose shape the script does not recognise, the script SHALL print `?` in that column, SHALL write one warning line naming the record and the column to stderr, and SHALL exit 0. This SHALL hold for every column of the table: an error raised while a column is being read SHALL be turned into `?` for that column and SHALL NOT stop the other columns or the other records. With `--format quartiles`, a record whose quartiles cannot be read SHALL print its id with no categories and the script SHALL exit 0.

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

##### Example: shapes that raised before the fix round

| Field | Value | Column | Cell |
| ----- | ----- | ------ | ---- |
| identity.metrics.quartiles | {system: JCR, quartile: {status: not_found}} | quartile | 未取得 |
| identity.metrics.quartiles | {system: SJR, value: 1} | quartile | 未取得 |
| identity.metrics.quartiles | [{system: JCR, quartile: {status: not_found}}] | quartile | ? |
| identity.metrics.jcr_category_rank.ranks | "Q1" | quartile | ? |
| requirements.review.type | "" | review | ? |

##### Example: quartiles format never raises

- **GIVEN** a record file whose `identity.metrics.quartiles` is the string `Q1`
- **WHEN** the script is run on that record with `--format quartiles`
- **THEN** the script exits 0 and prints one line that starts with the record id

##### Example: review type of an unknown mapping

- **GIVEN** a journal record whose `requirements.review.type` is `{kind: custom}`
- **WHEN** the row is built
- **THEN** the review cell is `?`

---

### Requirement: Additional record shapes are read

The script SHALL read the shapes below in addition to the shapes it read before this change.

- Indexing: `identity.indexing.web_of_science` with boolean `scie` and `ssci`. When `web_of_science` is present it decides the cell and the older indexing keys are not read: two boolean flags print the indexes, a status mapping prints its label, and anything else (a flag that is not a boolean, a missing flag, another shape) prints `?`. The `esci` flag is not shown in the table.
- Quartile: `identity.metrics.quartiles` as one mapping with `system` and either `quartile` or `value`, read only when that value is one of the strings `Q1`, `Q2`, `Q3`, `Q4`. Any other single mapping prints what it printed before this change (`未取得`). With `--format quartiles` the single mapping prints its category like a one-item list.
- APC: `requirements.fees.apc.currency_rates`, a list of `{currency, value}`, from which the USD entry is taken; and `requirements.fees.apc.list_price_usd`, a mapping of price tiers, from which the highest amount is taken. ASSUMPTION: the highest tier is the undiscounted list price.
- Length: `requirements.length_limit`, read the same way as `requirements.length`. Of `length`, `length_policy`, `length_note` and `length_limit`, the first one that holds a mapping is used; a key that holds something else does not hide a later key.
- Review: of `requirements.review.type`, `requirements.review.model` and `requirements.review.model_by_track.research`, the first one that states a review model is used. A value written as `{value: <code>}` is read as the code. An empty string states nothing.
- Review codes `double_anonymous` and `double-anonymous` SHALL print `雙匿名`.
- APC kind: one rule decides `必付` or `選付` however the amount is written, in this order: `mandatory: true` or false; `status` starting with `mandatory`, or equal to `optional`; `identity.open_access` set, which prints `必付`; `applies_when` present, which prints `選付`. When none applies, an amount prints with `?` as its kind, and a status-only amount prints its label alone.

#### Scenario: Web of Science flags

- **WHEN** `identity.indexing.web_of_science` is `{scie: true, ssci: false}`
- **THEN** the indexing cell is `SCIE`

##### Example: web of science flags

| scie | ssci | Indexing cell |
| ---- | ---- | ------------- |
| true | false | SCIE |
| true | true | SCIE＋SSCI |
| false | false | 兩者皆無 |

##### Example: web of science decides the indexing cell

| identity.indexing | Indexing cell |
| ----------------- | ------------- |
| {web_of_science: {scie: "false", ssci: false}} | ? |
| {web_of_science: {scie: {status: not_found}, ssci: false}} | ? |
| {web_of_science: {scie: true}} | ? |
| {web_of_science: {scie: false, ssci: false}, clarivate_wos: {in_ssci: {value: true}}} | 兩者皆無 |
| {web_of_science: {scie: true, ssci: false, esci: true}} | SCIE |

##### Example: single quartile mapping in the quartiles format

- **GIVEN** `identity.metrics.quartiles` is `{system: SJR, category: Software, value: Q1, year: 2025}`
- **WHEN** the per-category detail is built
- **THEN** it holds one entry, `Software Q1（SJR 2025）`

##### Example: apc kind precedence

| requirements.fees.apc | identity.open_access | APC cell |
| --------------------- | -------------------- | -------- |
| {amount: 2000, currency: USD, status: mandatory, applies_when: "on acceptance"} | absent | USD 2,000（必付） |
| {amount: 2000, currency: USD, applies_when: "on acceptance"} | true | USD 2,000（必付） |
| {amount: 2000, currency: USD, mandatory: false} | true | USD 2,000（選付） |
| {amount: {status: not_published}, mandatory: true, applies_when: "on acceptance"} | absent | 未公布 |
| {amount: {status: not_published}, applies_when: "on acceptance"} | absent | 未公布（選付） |

##### Example: length key that holds a mapping wins

- **GIVEN** `requirements.length` is the string `see guidelines` and `requirements.length_limit` is `{status: not_published}`
- **WHEN** the row is built
- **THEN** the length cell is `未公布`

##### Example: review model in other positions

| requirements.review | Review cell |
| ------------------- | ----------- |
| {type: {value: single_blind}} | 單盲 |
| {type: "", model: double_anonymous} | 雙匿名 |

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

---

### Requirement: Conference records print not-applicable for journal-only columns

For a record whose `kind` is `conference`, when the field for a column is absent or null, the script SHALL print `不適用` in the indexing, impact factor, quartile, time to first decision and submission to acceptance columns, and SHALL write no warning for them. A value the conference record does state SHALL be printed by the same rules as for a journal. When `identity.metrics` is present and is not a mapping, the four metric columns SHALL print `?` with a warning, as for a journal. The APC column has no conference default: it is read by the same rules as for a journal, so a conference record that states no APC prints `?`, and the record is expected to state `requirements.fees.apc` as an amount or a status mapping.

#### Scenario: Conference without journal metrics

- **WHEN** a conference record has no `identity.indexing`, no impact factor, no quartiles, no review times and no `requirements.fees`
- **THEN** those five columns are `不適用` and stderr has no warning for them

##### Example: conference journal-only columns

- **GIVEN** a record with `kind: conference`, `identity.metrics` holding only `acceptance_rate: {status: not_published}`, and no `requirements.fees`
- **WHEN** the row is built
- **THEN** indexing, impact factor, quartile, first decision and submission-to-acceptance are each `不適用`, and APC is `?`

##### Example: conference columns write no warning

- **GIVEN** a conference record file with no `identity.indexing`, no impact factor, no quartiles and no review times
- **WHEN** the script is run on that record
- **THEN** stderr has no warning line for `收錄`, `IF`, `分區`, `首次決定（中位）` or `投稿→接受（中位）`

##### Example: conference metric edge cases

| identity.metrics | Column | Cell |
| ---------------- | ------ | ---- |
| ["x"] | impact factor | ? |
| ["x"] | first decision | ? |
| {time_to_first_decision: null} | first decision | 不適用 |
| {impact_factor: null, quartiles: null} | quartile | 不適用 |

##### Example: conference apc is read like a journal

| requirements.fees | APC cell |
| ----------------- | -------- |
| absent | ? |
| {registration: {amount: 500, currency: USD}} | ? |
| {apc: {status: not_published}} | 未公布 |

##### Example: journal with the same gaps

- **GIVEN** a record with `kind: journal` and the same missing fields
- **WHEN** the row is built
- **THEN** indexing, impact factor and quartile are each `?`

---

### Requirement: Rows that the script produced before this change keep their cells

For the records present on the default branch when this change was written, a cell SHALL stay the same after this change unless the cell was `?` before, or the cell was the raw review code `double_anonymous`. The baseline file stores, with each row, the SHA-256 of the record file the row was built from; a row whose record file has since changed is not compared, so that later updates to a record do not fail the check. A record that made the script raise before this change SHALL produce a row.

#### Scenario: Baseline comparison

- **WHEN** the table is built for every record that has a stored baseline row
- **THEN** each cell equals the baseline cell, except cells whose baseline is `?` or `double_anonymous`

##### Example: baseline rows are unchanged

- **GIVEN** the baseline file `plugins/research-submission/tests/fixtures/venue_table_baseline.tsv`, holding the 23 rows the script produced on the default branch
- **WHEN** each of those records is built again
- **THEN** every cell equals its baseline, except where the baseline cell is `?` or `double_anonymous`

##### Example: changed record is not compared

- **GIVEN** a baseline row whose stored SHA-256 differs from the SHA-256 of the record file
- **WHEN** the baseline comparison runs
- **THEN** that row is skipped and the comparison reports how many rows it compared

##### Example: record that raised now builds

- **GIVEN** the record `jnspg/jns-spine`, whose `identity.indexing` is a list
- **WHEN** the table is built for it
- **THEN** the script exits 0 and prints one row

## ADDED Requirements

### Requirement: Publisher cell

The publisher cell SHALL print a short name when the publisher text contains a known publisher name, including `ACM` for the Association for Computing Machinery and for text that starts with `ACM`. A publisher written as a mapping or a list that is not a status mapping SHALL be matched by its text in the same way; when no known name matches, the cell SHALL be `?`.

#### Scenario: Publisher written as a mapping

- **WHEN** `identity.publisher` is `{name: "Elsevier B.V."}`
- **THEN** the publisher cell is `Elsevier`

##### Example: publisher short names

| identity.publisher | Publisher cell |
| ------------------ | -------------- |
| Association for Computing Machinery | ACM |
| ACM Digital Library（2026 proceedings） | ACM |
| {name: "Elsevier B.V."} | Elsevier |
| {name: "Unknown House"} | ? |
| ["Unknown House"] | ? |
