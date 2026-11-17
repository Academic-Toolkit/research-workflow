## Purpose

Defines how contact addresses in a venue record are told apart as personal or office addresses, the validator warning for a record that holds both kinds, and the recording rule the add-venue skill states. It exists so that records keep the address a venue publishes for its office and do not collect the personal addresses of editors.

## ADDED Requirements

### Requirement: Contact addresses are classified by position

The record validator SHALL classify every address-bearing string in the contact scope of a record as personal or office, by where the string sits and never by its domain.

- An address-bearing string is a string value that contains a substring of the form `local@domain.tld` (one `@`, at least one dot in the domain part).
- The contact scope is everything under `identity`, everything under `requirements.submission`, and everything under `cycle`. Strings elsewhere in the record (for example `warnings`, `sources`, `requirements.standards`) are outside the scope and SHALL NOT be classified.
- A named-person mapping is any mapping under `identity`, other than the `identity` mapping itself, that has a `name` key whose value is a string. The `identity` mapping itself is excluded because its `name` is the name of the venue.
- An address-bearing string at any depth inside a named-person mapping is a personal address. Every other address-bearing string in the contact scope is an office address.
- Mappings under `requirements.submission` and `cycle` are never named-person mappings.

The field path of a string is its keys joined by dots, with a list position written as `[i]` directly after the key of the list (for example `identity.editors[1].email`).

#### Scenario: An address inside an entry that names a person

- **WHEN** a mapping under `identity` has a string `name` and a string under it contains an address
- **THEN** that string is classified as a personal address

##### Example: classification by position

| Record fragment | Classified as | Field path |
| --- | --- | --- |
| `identity.editor: {name: "A. Editor", email: "a.editor@example.org"}` | personal | `identity.editor.email` |
| `identity.editor: {name: "A. Editor", note: "write to a.editor@example.org"}` | personal | `identity.editor.note` |
| `identity.editors: [{name: "A. Editor"}, {name: "B. Editor", email: "b.editor@example.org"}]` | personal | `identity.editors[1].email` |
| `identity.editors: {board: {name: "A. Editor", contact: {email: "a.editor@example.org"}}}` | personal | `identity.editors.board.contact.email` |
| `identity.editorial_office: {email: "office@example.org"}` | office | `identity.editorial_office.email` |
| `identity.editors: {desk: {role: "Reproducibility editors", email: "repro@example.org"}}` | office | `identity.editors.desk.email` |
| `identity: {name: "Journal of Examples", contact: "office@example.org"}` | office | `identity.contact` |
| `requirements.submission: {contact: "office@example.org"}` | office | `requirements.submission.contact` |
| `requirements.submission: {helper: {name: "Help desk", email: "help@example.org"}}` | office | `requirements.submission.helper.email` |
| `cycle.portal: {email: "meeting2026@example.org"}` | office | `cycle.portal.email` |
| `warnings: ["report fakes to abuse@example.org"]` | not classified | (none) |
| `identity.editor: {name: "A. Editor", twitter: "@aeditor"}` | not classified | (none) |

### Requirement: A record that holds both kinds of address gets warning W3

When a record holds at least one personal address and at least one office address, the record validator SHALL print exactly one warning for that record whose text starts with `[W3]` and lists the field path of every personal address in the record, in document order. The warning text SHALL NOT contain any address. A record that holds only personal addresses, only office addresses, or none SHALL NOT get W3. W3 is a warning: it SHALL NOT change the exit status of the validator and SHALL be counted in the warning total the validator prints.

#### Scenario: Both kinds present

- **WHEN** the validator checks a record with a personal address and an office address
- **THEN** it prints one `[W3]` warning naming the field path of the personal address, without any address, and its exit status is the one it would have without the warning

##### Example: one warning naming the personal paths

- **GIVEN** a record that is otherwise valid, with `identity.editor: {name: "A. Editor", email: "a.editor@example.org", note: "also a.editor@example.org"}` and `identity.editorial_office: {email: "office@example.org"}`
- **WHEN** the warnings of the record are computed
- **THEN** exactly one warning starts with `[W3]`, it contains `identity.editor.email` and `identity.editor.note`, and it contains neither `a.editor@example.org` nor `office@example.org` nor the character `@`

##### Example: one kind only gives no warning

| Record | W3 |
| --- | --- |
| `identity.editor: {name: "A. Editor", email: "a.editor@example.org"}` and no other address | none |
| `identity.editorial_office: {email: "office@example.org"}` and `requirements.submission.contact: "office@example.org"` | none |
| no address anywhere in the contact scope | none |
| `identity.editor: {name: "A. Editor", email: "a.editor@example.org"}` and `warnings: ["write to office@example.org"]` | none |

##### Example: validator run exits zero with W3

- **GIVEN** a record file that passes the schema and the lint errors, and holds `identity.editor: {name: "A. Editor", email: "a.editor@example.org"}` and `identity.editorial_office: {email: "office@example.org"}`
- **WHEN** `validate.py` is run on that file
- **THEN** the exit status is 0, the output has one line containing `[W3]`, and the summary line reports 1 warning

### Requirement: The add-venue skill states the recording rule

The add-venue skill text SHALL state the rule for contact addresses: an address is an office address by what the venue uses it for, not by its domain; when the venue publishes an office address, only that address is recorded; a personal address is recorded only when the official site gives no office address and names that address as the way to reach the venue about a submission, and it carries its source; an office address is never placed inside an entry that names a person. The warning table of the skill SHALL list W3.

#### Scenario: Skill text read by a maintainer adding a venue

- **WHEN** the add-venue skill text is read
- **THEN** it contains the rule and the W3 row

##### Example: skill text on contact addresses

- **GIVEN** the file `plugins/research-submission/skills/add-venue/SKILL.md`
- **WHEN** its text is read
- **THEN** it has a table row starting `| W3 |`, and it contains each of the phrases `公務信箱`, `個人信箱`, `看用途，不看網域` and `不寫在具名人物底下`

### Requirement: The bundled corpus produces no W3

Every record under `plugins/research-submission/venues/` SHALL produce no W3 warning.

#### Scenario: Validating the bundled records

- **WHEN** the warnings of every bundled record are computed
- **THEN** none starts with `[W3]`

##### Example: bundled records have no W3

- **GIVEN** every `*.yaml` file under `plugins/research-submission/venues/`
- **WHEN** the warnings of each record are computed
- **THEN** no warning of any record starts with `[W3]`
