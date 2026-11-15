# venue-table Specification

## Purpose

The venue table is the comparison table that `plugins/research-submission/scripts/venue_table.py` builds from venue records, so that reports never copy values by hand. This capability states how a record field of each known shape, of an unknown shape, or of a conference record appears in a table cell.

## Requirements

### Requirement: Status mappings print their status label

A status mapping is a mapping whose `status` is `not_published`, `not_found` or `not_applicable` and that carries no `value` or `amount`. When one of the positions listed here holds a status mapping, the script SHALL print the label of that status (`未公布`, `未取得`, `不適用`) in the column and SHALL NOT raise:

- publisher: `identity.publisher`
- indexing: `identity.indexing`, `identity.indexing.web_of_science`, and `identity.metrics.indexing` when it is read in place of an absent `identity.indexing`
- impact factor: `identity.metrics.impact_factor`
- APC: `requirements.fees`, `requirements.fees.apc`, `requirements.fees.apc.amount`
- review: `requirements.review`, `requirements.review.type`, `requirements.review.model`, `requirements.review.model_by_track.research`

A status mapping in `requirements.review.type` SHALL NOT hide a review model the record states in `requirements.review.model` or `requirements.review.model_by_track.research`. A status mapping at any other position read for these columns (for example inside `web_of_science.scie`, `currency_rates`, `list_price_usd`, the older indexing keys `clarivate_wos`, `wos_ssci_scie` and `clarivate_mjl`, or `identity.metrics` itself) is outside this requirement and prints what the rules for unrecognised shapes or the rules in force before this change give. The quartile, acceptance rate, review time and length columns keep the labels they printed before this change; aligning them is outside this change.

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

##### Example: indexing block status mapping

- **GIVEN** a journal record whose `identity.indexing` is `{status: not_found, checked: 2026-11-15}`
- **WHEN** the row is built
- **THEN** the indexing cell is `未取得`

##### Example: publisher status mapping

- **GIVEN** a conference record whose `identity.publisher` is `{status: not_published, checked: 2026-11-15, note: "electronic proceedings"}`
- **WHEN** the row is built
- **THEN** the publisher cell is `未公布`, and the cell does not contain the text `status`

---
### Requirement: Unrecognised shapes print a question mark and never raise

When a field read for a table column holds a value whose shape the script does not recognise, the script SHALL print `?` in that column, SHALL write one warning line naming the record and the column to stderr, and SHALL exit 0. This SHALL hold for every column of the table: an error raised while a column is being read SHALL be turned into `?` for that column and SHALL NOT stop the other columns or the other records. With `--format quartiles`, a record whose quartiles cannot be read SHALL print its id with no categories and the script SHALL exit 0. A column that ends as `?` SHALL NOT leave a footnote behind. The name cell SHALL be `?` when `identity.name` is present and is not text; an absent or empty name prints the record id, as before this change.

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
| identity.metrics.time_to_first_decision | [30] | first decision | ? |
| identity.metrics.impact_factor | {value: {x: 1}} | impact factor | ? |
| identity.metrics.acceptance_rate | {value: [1]} | acceptance rate | ? |
| requirements.length | {value: [1], unit: words} | length | ? |
| requirements.fees.apc | {amount: [2000], currency: USD, mandatory: true} | APC | ? |

##### Example: values that are not numbers or text

| Field | Value | Column | Cell |
| ----- | ----- | ------ | ---- |
| requirements.fees.apc | {amount: false, currency: USD} | APC | ? |
| requirements.fees.apc | {currency_rates: [{currency: USD, value: false}]} | APC | ? |
| requirements.fees.apc | {mandatory: true, list_price_usd: {non_member: false}} | APC | ? |
| requirements.fees.apc | {amount: 2000, currency: [USD], mandatory: true} | APC | ? |
| requirements.fees.apc | {all_other_articles: {amount: [1]}, mandatory: true} | APC | ? |
| requirements.length | {value: 10, unit: [pages]} | length | ? |
| requirements.length | {value: 10, unit: 5} | length | ? |
| requirements.length | {value: 10, unit: true} | length | ? |
| identity.name | [A, B] | name | ? |

##### Example: failed column leaves no footnote

- **GIVEN** a record whose `identity.metrics.time_submission_to_acceptance` is `{status: not_published}` and whose `identity.metrics.estimates.sub_to_acceptance` is `{value: "fast", n: 10}`
- **WHEN** the row is built
- **THEN** the submission-to-acceptance cell is `?` and no footnote is recorded for the record

##### Example: quartiles format never raises

- **GIVEN** a record file whose `identity.metrics.quartiles` is the list `[Q1]`, a shape that raised before this change
- **WHEN** the script is run on that record with `--format quartiles`
- **THEN** the script exits 0 and prints one line holding the record id and no categories

##### Example: review type of an unknown mapping

- **GIVEN** a journal record whose `requirements.review.type` is `{kind: custom}`
- **WHEN** the row is built
- **THEN** the review cell is `?`

---
### Requirement: Additional record shapes are read

The script SHALL read the shapes below in addition to the shapes it read before this change.

- Indexing: `identity.indexing.web_of_science` with boolean `scie` and `ssci`. When `web_of_science` is present it decides the cell and the older indexing keys are not read: two boolean flags print the indexes, a status mapping prints its label, and anything else (a flag that is not a boolean, a missing flag, another shape) prints `?`. The `esci` flag is not shown in the table.
- Quartile lists: an entry that is not a mapping, or whose `quartile` is not text, is left out, both in the table and with `--format quartiles`. A list that is not empty and has no readable entry prints `?` in the table; an empty list prints `未取得`, as before this change.
- Quartile: `identity.metrics.quartiles` as one mapping with `system` and either `quartile` or `value`, read only when that value is one of the strings `Q1`, `Q2`, `Q3`, `Q4`. Any other single mapping prints what it printed before this change (`未取得`). With `--format quartiles` the single mapping prints its category like a one-item list.
- APC: `requirements.fees.apc.currency_rates`, a list of `{currency, value}`, from which the USD entry is taken; and `requirements.fees.apc.list_price_usd`, a mapping of price tiers, from which the highest amount is taken. ASSUMPTION: the highest tier is the undiscounted list price. A price inside `currency_rates` or `list_price_usd` is read only when it is a number; a boolean is not a number. An `amount` keeps the forms it accepted before this change, text included, and a boolean `amount` prints `?`.
- Length: `requirements.length_limit`, read the same way as `requirements.length`. Of `length`, `length_policy`, `length_note` and `length_limit`, the first one that holds a mapping is used; a key that holds something else does not hide a later key.
- Review: of `requirements.review.type`, `requirements.review.model` and `requirements.review.model_by_track.research`, the first one that states a review model is used. A value written as `{value: <code>}` is read as the code. An empty string states nothing.
- Review codes `double_anonymous` and `double-anonymous` SHALL print `雙匿名`.
- APC kind, when the amount is known: `必付` or `選付` is decided in this order: `mandatory: true` or false; `status` starting with `mandatory`, or equal to `optional`; `identity.open_access` set, which prints `必付` as it did before this change, and is consulted only when the amount was written as `amount` or in one of the shapes read before this change; `applies_when` present, which prints `選付`. When none applies the amount prints with `?` as its kind. An amount taken from `currency_rates` or `list_price_usd` never gets `必付` from `identity.open_access`, because those records printed `?` before this change. When the amount is a status mapping, the cell is the status label followed by `（選付）` if `mandatory` is false or `status` is `optional`, or if `applies_when` is present and `mandatory` is not true; otherwise the label alone. `identity.open_access` is not read in that case, as before this change.

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

##### Example: apc kind for amounts from the new price keys

| identity.open_access | requirements.fees.apc | APC cell |
| -------------------- | --------------------- | -------- |
| hybrid | {applies_when: "author chooses open access", currency_rates: [{currency: USD, value: 3390}]} | USD 3,390（選付） |
| hybrid | {list_price_usd: {member: 1300, non_member: 1800}} | USD 1,800（?） |
| hybrid | {mandatory: true, list_price_usd: {member: 1300, non_member: 1800}} | USD 1,800（必付） |
| hybrid | {amount: {status: not_published}, status: optional} | 未公布（選付） |

##### Example: quartile list with one unreadable entry

- **GIVEN** `identity.metrics.quartiles` is `[{system: JCR, category: A, quartile: {status: not_found}}, {system: SJR, category: B, quartile: Q1, year: 2025}]`
- **WHEN** the row and the per-category detail are built
- **THEN** the quartile cell is `Q1（SJR）` and the detail holds one entry, `B Q1（SJR 2025）`

##### Example: quartile list edge cases

| identity.metrics.quartiles | Quartile cell |
| -------------------------- | ------------- |
| [] | 未取得 |
| ["Q1", {system: SJR, category: B, quartile: Q1}] | Q1（SJR） |
| ["Q1"] | ? |

##### Example: length key that holds a mapping wins

- **GIVEN** `requirements.length` is the string `see guidelines` and `requirements.length_limit` is `{status: not_published}`
- **WHEN** the row is built
- **THEN** the length cell is `未公布`

##### Example: review model in other positions

| requirements.review | Review cell |
| ------------------- | ----------- |
| {type: {value: single_blind}} | 單盲 |
| {type: "", model: double_anonymous} | 雙匿名 |
| {type: not_published, model: double_anonymous} | 雙匿名 |
| {type: not_published} | 未公布 |

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

For a record whose `kind` is `conference`, when the field for a column is absent or null (an empty mapping is not absent), the script SHALL print `不適用` in the indexing, impact factor, quartile, time to first decision and submission to acceptance columns, and SHALL write no warning for them. A value the conference record does state SHALL be printed by the same rules as for a journal. When `identity.metrics` is present and is not a mapping, the four metric columns SHALL print `?` with a warning, as for a journal. The APC column has no conference default: it is read by the same rules as for a journal, so a conference record that states no APC prints `?`, and the record is expected to state `requirements.fees.apc` as an amount or a status mapping.

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

A conference record whose `identity.indexing` is the empty mapping `{}` prints `?` in the indexing cell, as a journal does. For every record, an absent `identity.indexing`, or one that is the empty mapping, does not hide a filled `identity.metrics.indexing`, which is read instead as before this change. An `identity.metrics.indexing` that is itself empty is not a filled one: it prints `?`, for a conference as for a journal.

##### Example: metrics indexing is still read

- **GIVEN** a journal record whose `identity.indexing` is `{}` and whose `identity.metrics.indexing` is `{web_of_science: {scie: true, ssci: false}}`
- **WHEN** the row is built
- **THEN** the indexing cell is `SCIE`

##### Example: empty metrics indexing on a conference

- **GIVEN** a conference record with no `identity.indexing` and with `identity.metrics.indexing` equal to `{}`
- **WHEN** the row is built
- **THEN** the indexing cell is `?`

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

For the records present on the default branch when this change was written, a cell SHALL stay the same after this change unless the cell was `?` before, or the cell was the raw review code `double_anonymous`. The baseline file stores, with each row, the SHA-256 of the record file the row was built from; a row whose record file has since changed is not compared, so that later updates to a record do not fail the check. The check SHALL fail when it compares no row at all. A record that made the script raise before this change SHALL produce a row.

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

---
### Requirement: Publisher cell

The publisher cell SHALL print a short name when the publisher text contains a known publisher name, including `ACM` for the Association for Computing Machinery and for text that holds `ACM` as a whole word. A publisher written as a mapping that is not a status mapping SHALL be matched by its `name` when that is text, otherwise by its `value` when that is text, and one written as a list by its first string item, in the same way; when no known name matches such a mapping or list, the cell SHALL be `?`.

#### Scenario: Publisher written as a mapping

- **WHEN** `identity.publisher` is `{name: "Elsevier B.V."}`
- **THEN** the publisher cell is `Elsevier`

##### Example: publisher short names

| identity.publisher | Publisher cell |
| ------------------ | -------------- |
| Association for Computing Machinery | ACM |
| ACM Digital Library（2026 proceedings） | ACM |
| {name: "Elsevier B.V."} | Elsevier |
| {name: "ACM Press"} | ACM |
| {value: "Elsevier"} | Elsevier |
| IEEE and ACM | ACM |
| Acme Books | Acme Books |
| {name: "Unknown House", note: "formerly Wiley"} | ? |
| {name: "Unknown House"} | ? |
| ["Unknown House"] | ? |

---
### Requirement: Shapes the add-venue skill prescribes pass the record validator

Every record shape that `plugins/research-submission/skills/add-venue/SKILL.md` tells a writer to use for a table column SHALL be accepted by `plugins/research-submission/scripts/validate.py`. For a length limit the official page does not state, the prescribed shape is `requirements.length_limit: {status: not_published, checked: <date>}`, because the schema requires `value` and `unit` under `requirements.length`.

#### Scenario: Length limit not published

- **WHEN** a valid journal record has its `requirements.length` replaced by `requirements.length_limit: {status: not_published, checked: 2026-11-15}`
- **THEN** `validate.py` reports no error for that record

##### Example: prescribed length shape validates

- **GIVEN** a copy of the record `psychometric-society/psychometrika` in which `requirements.length` is removed and `requirements.length_limit` is `{status: not_published, checked: 2026-11-15}`
- **WHEN** `validate.py` is run on that file
- **THEN** it exits 0, and the same copy with `requirements.length: {status: not_published, checked: 2026-11-15}` makes it exit 1

##### Example: prescribed column shapes validate

| Shape written into a copy of a valid record |
| ------------------------------------------- |
| identity.indexing.web_of_science: {scie: true, ssci: false, esci: false} |
| requirements.fees.apc: {amount: 3000, currency: USD, mandatory: false} |
| requirements.fees.apc: {currency_rates: [{currency: USD, value: 3390}], applies_when: "author chooses open access"} |
| requirements.fees.apc: {list_price_usd: {member: 1300, non_member: 1800}, mandatory: true} |
| requirements.fees.apc: {status: not_published, checked: 2026-11-15} |
| requirements.review.type: double_anonymized |
| requirements.review.type: {status: not_published, checked: 2026-11-15} |
| requirements.review.model_by_track: {research: double_anonymized} |
| identity.publisher: {status: not_published, checked: 2026-11-15} |

Each row, written into a copy of `psychometric-society/psychometrika`, makes `validate.py` exit 0.

##### Example: skill text names the validating shape

- **GIVEN** the text of `plugins/research-submission/skills/add-venue/SKILL.md`
- **WHEN** it is searched for the length row of the standard-shape table
- **THEN** the row names `requirements.length_limit: {status: not_published, checked}` and does not name `requirements.length: {status: not_published, checked}`
