## MODIFIED Requirements

### Requirement: Contact addresses are classified by position

The record validator SHALL classify every address in the contact scope of a record as personal or office, by where it sits and never by its domain.

- An address is a substring made of a local part, `@`, and a domain. The local part is one or more ASCII letters, digits or the characters `.`, `_`, `%`, `+`, `-`, and is not directly preceded by one of those characters or by `/`. The domain is one or more labels of ASCII letters, digits and hyphens joined by dots, and its last label is at least two ASCII letters. A handle such as `@name`, and a URL whose path holds `/@name`, are therefore not addresses.
- The contact scope is everything under `identity`, everything under `requirements.submission`, and everything under `cycle`, including a section whose value is itself a string or a list. Strings elsewhere in the record (for example `warnings`, `sources`, `requirements.standards`) are outside the scope and SHALL NOT be classified.
- A named-person mapping is any mapping inside the contact scope that has a `name` key whose value is a string, except the `identity` mapping itself, whose `name` is the name of the venue. The rule reads position only and cannot tell a person from an organisation: a mapping that names an organisation and has a string `name` is a named-person mapping too.
- A string value that contains an address, at any depth inside a named-person mapping, is a personal address. Every other string value in the contact scope that contains an address is an office address.
- A mapping key that contains an address is classified the same way as a string value at that position, and the validator goes on to classify the value under that key.

The field path of a value is its keys joined by dots, with a list position written as `[i]` directly after the key of the list (for example `identity.editors[1].email`). A key that contains an address is written as `<address>` in a field path, so that a field path never contains an address.

#### Scenario: An address inside an entry that names a person

- **WHEN** a mapping in the contact scope, other than `identity` itself, has a string `name` and a string under it contains an address
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
| `cycle.portal: {email: "meeting2026@example.org"}` | office | `cycle.portal.email` |
| `warnings: ["report fakes to abuse@example.org"]` | not classified | (none) |
| `identity.editor: {name: "A. Editor", twitter: "@aeditor"}` | not classified | (none) |

##### Example: named persons in every section of the scope

| Record fragment | Classified as | Field path |
| --- | --- | --- |
| `cycle.chairs: [{name: "C. Chair", email: "c.chair@example.org"}]` | personal | `cycle.chairs[0].email` |
| `requirements.submission: {helper: {name: "H. Helper", email: "h.helper@example.org"}}` | personal | `requirements.submission.helper.email` |
| `identity.owner: {name: "Example Trust", email: "trust@example.org"}` | personal | `identity.owner.email` |
| `identity.editor: {name: {en: "A. Editor"}, email: "a.editor@example.org"}` | office | `identity.editor.email` |

##### Example: what counts as an address

| String | Contains an address |
| --- | --- |
| `a.editor@example.org` | yes |
| `write to <a.editor@example.org>.` | yes |
| `主編信箱a.editor@example.org。` | yes |
| `https://social.example/@aeditor/intro.html` | no |
| `@aeditor` | no |
| `帳號@aeditor，網站 example.org` | no |
| `a.editor@localhost` | no |

##### Example: an address used as a key

- **GIVEN** `identity.editor: {name: "A. Editor", contacts: {"a.editor@example.org": "primary"}}` and `identity.desk: {"office@example.org": {hours: "9-5"}}`
- **WHEN** the record is classified
- **THEN** the personal field paths are `identity.editor.contacts.<address>` and the office field paths are `identity.desk.<address>`

##### Example: a section written as a string or a list

| Record fragment | Classified as | Field path |
| --- | --- | --- |
| `requirements.submission: "write to office@example.org"` | office | `requirements.submission` |
| `cycle: ["meeting2026@example.org"]` | office | `cycle[0]` |
| `identity: null`, `requirements: null`, `cycle: null` | not classified | (none) |

### Requirement: A record that holds both kinds of address gets warning W3

When a record holds at least one personal address and at least one office address, the record validator SHALL print exactly one warning for that record whose text starts with `[W3]` and lists the field path of every personal address in the record, in document order. The warning text SHALL NOT contain any address, including when a key of the record is an address. A record that holds only personal addresses, only office addresses, or none SHALL NOT get W3. W3 is a warning: it SHALL NOT change the exit status of the validator and SHALL be counted in the warning total the validator prints.

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

##### Example: warning text when a key is an address

- **GIVEN** `identity.editor: {name: "A. Editor", contacts: {"a.editor@example.org": "primary"}}` and `identity.editorial_office: {email: "office@example.org"}`
- **WHEN** the warnings of the record are computed
- **THEN** exactly one warning starts with `[W3]`, it contains `identity.editor.contacts.<address>`, and it does not contain the character `@`

##### Example: validator run exits zero with W3

- **GIVEN** a record file that passes the schema and the lint errors, whose every source carries the date of the run as `last_verified_at`, and that holds `identity.editor: {name: "A. Editor", email: "a.editor@example.org"}` and `identity.editorial_office: {email: "office@example.org"}`
- **WHEN** `validate.py` is run on that file
- **THEN** the exit status is 0, the output has one line containing `[W3]`, and the summary line reports 1 warning

### Requirement: The add-venue skill states the recording rule

The add-venue skill text SHALL state the rule for contact addresses in six parts:

1. An address is told apart by whose mailbox it is, not by its domain: a mailbox that belongs to a role or desk of the venue and passes to the successor is an office address, including one opened on a free mail service; a mailbox that belongs to one person is a personal address, even when the official site lists it as a contact.
2. When the venue publishes an office address, only that address is recorded.
3. A personal address is recorded only when the official site gives no office address and says submission matters are sent to that address, and it carries its source.
4. An office address is never placed inside an entry that names a person.
5. Notes and warnings do not quote a personal address; they point to the source page.
6. The validator treats every mapping with a string `name` as a named person, so the mailbox of an organisation is not placed inside a mapping that has a `name` either.

The skill text SHALL NOT name the key an office address is written under as the standard; it SHALL say that the standard key is undecided and tracked in issue 21. The warning table of the skill SHALL list W3.

#### Scenario: Skill text read by a maintainer adding a venue

- **WHEN** the add-venue skill text is read
- **THEN** it contains the six parts, the W3 row, and the pointer to issue 21

##### Example: skill text on contact addresses

- **GIVEN** the file `plugins/research-submission/skills/add-venue/SKILL.md`
- **WHEN** its text is read
- **THEN** it has a table row starting `| W3 |`; it contains each of the phrases `公務信箱`, `個人信箱`, `看信箱屬於誰，不看網域`, `即使官網把它列為聯絡方式`, `不寫在具名人物底下`, `備註與警告`, `機構的信箱` and `#21`; and it does not contain the phrase `公務信箱寫在 \`identity.editorial_office.email\``

### Requirement: The bundled corpus produces no W3

Every record under `plugins/research-submission/venues/` SHALL produce no W3 warning. No bundled record SHALL hold a personal address, except a record that the test of this requirement lists as using the exception of the recording rule, each with the source that names the address as the submission contact. The list is empty when this requirement is written.

#### Scenario: Validating the bundled records

- **WHEN** the warnings and the classification of every bundled record are computed
- **THEN** no warning starts with `[W3]` and no record outside the exception list has a personal field path

##### Example: bundled records have no W3

- **GIVEN** every `*.yaml` file under `plugins/research-submission/venues/`
- **WHEN** the warnings of each record are computed
- **THEN** no warning of any record starts with `[W3]`

##### Example: bundled records hold no personal address

- **GIVEN** every `*.yaml` file under `plugins/research-submission/venues/` and an empty exception list
- **WHEN** each record is classified
- **THEN** the list of personal field paths of every record is empty
