## MODIFIED Requirements

### Requirement: Contact addresses are classified by position

The record validator SHALL classify every address in the contact scope of a record as personal or office, by where it sits and never by its domain.

- An address is a substring made of a local part, `@`, and a domain. The local part is one or more ASCII letters, digits or the characters `.`, `_`, `%`, `+`, `-`, and is not directly preceded by one of those characters or by `@`. The domain is two or more labels of ASCII letters, digits and hyphens joined by dots, its last label is at least two ASCII letters, and it is not directly followed by an ASCII letter, digit or hyphen. A handle such as `@name`, a URL whose path holds `/@name`, and a cross-site handle of the form `@name@site.example` are therefore not addresses; an address that follows a `/` is an address.
- The contact scope is everything under `identity`, everything under `requirements.submission`, and everything under `cycle`, including a section whose value is itself a string or a list. Strings elsewhere in the record (for example `warnings`, `sources`, `requirements.standards`) are outside the scope and SHALL NOT be classified.
- A named-person mapping is any mapping inside the contact scope that has a `name` key whose value is a string, except the three section roots themselves (the `identity` mapping, the `requirements.submission` mapping and the `cycle` mapping), whose `name` names the venue, the submission system or the edition. The rule reads position only and cannot tell a person from an organisation: a mapping that names an organisation and has a string `name` is a named-person mapping too.
- A string value that contains an address, at any depth inside a named-person mapping, is a personal address. Every other string value in the contact scope that contains an address is an office address.
- A mapping key that contains an address is classified the same way as a string value at that position, and the validator goes on to classify the value under that key.

The field path of a value is its keys joined by dots, with a list position written as `[i]` directly after the key of the list (for example `identity.editors[1].email`). A key that contains an address is written as `<address>` in a field path. A key that contains no address, but whose addition to the path would make the path contain an address, is written as `<key>`. A field path therefore never contains an address.

#### Scenario: An address inside an entry that names a person

- **WHEN** a mapping in the contact scope, other than a section root, has a string `name` and a string under it contains an address
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
| `cycle: {name: "Meeting 2026", portal: {email: "meeting2026@example.org"}}` | office | `cycle.portal.email` |
| `requirements.submission: {name: "Online system", contact: "office@example.org"}` | office | `requirements.submission.contact` |

The fourth row records a limit of the position rule, not the intended treatment of an editor's mailbox: a person whose `name` is not a string is not recognised. Issue 22 tracks it, and a fix there changes this row.

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
| `a.editor@example.org2` | no |
| `https://example.org/people/a.editor@example.org` | yes |
| `@aeditor@social.example` | no |
| `https://social.example/@aeditor@other.example` | no |

##### Example: an address used as a key

- **GIVEN** `identity.editor: {name: "A. Editor", contacts: {"a.editor@example.org": "primary"}}` and `identity.desk: {"office@example.org": {hours: "9-5"}}`
- **WHEN** the record is classified
- **THEN** the personal field paths are `identity.editor.contacts.<address>` and the office field paths are `identity.desk.<address>`

##### Example: keys that would join into an address

- **GIVEN** `identity.editor: {name: "A. Editor", "a.editor@example": {org: "see a.editor@example.org"}}`
- **WHEN** the record is classified
- **THEN** the only personal field path is `identity.editor.a.editor@example.<key>`, and no field path contains an address

##### Example: a section written as a string or a list

| Record fragment | Classified as | Field path |
| --- | --- | --- |
| `requirements.submission: "write to office@example.org"` | office | `requirements.submission` |
| `cycle: ["meeting2026@example.org"]` | office | `cycle[0]` |
| `identity: null`, `requirements: null`, `cycle: null` | not classified | (none) |

---

### Requirement: A record that holds both kinds of address gets warning W3

When a record holds at least one personal address and at least one office address, the record validator SHALL print exactly one warning for that record whose text starts with `[W3]` and lists the field path of every personal address in the record, in the order they appear in the record (the three sections of the contact scope are read in the order the record writes them). The warning text SHALL NOT contain any address, including when a key of the record is an address. A record that holds only personal addresses, only office addresses, or none SHALL NOT get W3. W3 is a warning: it SHALL NOT change the exit status of the validator and SHALL be counted in the warning total the validator prints.

#### Scenario: Both kinds present

- **WHEN** the validator checks a record with a personal address and an office address
- **THEN** it prints one `[W3]` warning naming the field path of the personal address, without any address, and its exit status is the one it would have without the warning

##### Example: one warning naming the personal paths

- **GIVEN** a record that is otherwise valid, with `identity.editor: {name: "A. Editor", email: "a.editor@example.org", note: "also a.editor@example.org"}` and `identity.editorial_office: {email: "office@example.org"}`
- **WHEN** the warnings of the record are computed
- **THEN** exactly one warning starts with `[W3]`, it contains `identity.editor.email` and `identity.editor.note`, and it contains neither `a.editor@example.org` nor `office@example.org` nor the character `@`

##### Example: personal paths follow the order of the record

- **GIVEN** a record that writes `cycle` first with `cycle.chairs: [{name: "C. Chair", email: "c.chair@example.org"}]`, then `requirements.submission.contact: "office@example.org"`, then `identity.editor: {name: "A. Editor", email: "a.editor@example.org"}`
- **WHEN** the warnings of the record are computed
- **THEN** exactly one warning starts with `[W3]` and `cycle.chairs[0].email` appears in it before `identity.editor.email`

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

##### Example: a conference record whose cycle is a list

- **GIVEN** a record with `kind: conference`, `identity.chair: {name: "C. Chair", email: "c.chair@example.org"}` and `cycle: ["meeting2026@example.org"]`
- **WHEN** the warnings of the record are computed
- **THEN** no error is raised and exactly one warning starts with `[W3]`

##### Example: validator run exits zero with W3

- **GIVEN** a record file that passes the schema and the lint errors, whose every source carries the date of the run as `last_verified_at`, and that holds `identity.editor: {name: "A. Editor", email: "a.editor@example.org"}` and `identity.editorial_office: {email: "office@example.org"}`
- **WHEN** `validate.py` is run on that file
- **THEN** the exit status is 0, the output has one line containing `[W3]`, and the summary line reports 1 warning

---

### Requirement: The add-venue skill states the recording rule

The add-venue skill text SHALL state the rule for contact addresses in seven parts:

1. An address is told apart by whose mailbox it is, not by its domain: a mailbox that belongs to a role or desk of the venue and passes to the successor is an office address, including one opened on a free mail service; a mailbox that belongs to one person is a personal address, even when the official site lists it as a contact.
2. When the venue publishes an office address, only that address is recorded.
3. A personal address is recorded only when the official site gives no office address and says submission matters are sent to that address, and it carries its source.
4. An office address is never placed inside an entry that names a person.
5. Notes and warnings do not quote a personal address; they point to the source page.
6. The validator treats every mapping with a string `name` as a named person, so the mailbox of an organisation is not placed inside a mapping that has a `name` either.
7. A record that uses the exception of part 3 is added to the exception list of the corpus test (`PERSONAL_ADDRESS_EXCEPTIONS` in `tests/test_validate_contacts.py`) with the source that names the address as the submission contact; without that entry the test suite fails.

The skill text SHALL NOT name the key an office address is written under as the standard; it SHALL say that the standard key is undecided and tracked in issue 21. The warning table of the skill SHALL list W3. The verification step of the skill SHALL tell the writer to run the test suite of the plugin in addition to the validator, because the validator alone prints nothing for a record that holds only a personal address.

#### Scenario: Skill text read by a maintainer adding a venue

- **WHEN** the add-venue skill text is read
- **THEN** it contains the seven parts, the W3 row, the pointer to issue 21, and the test-suite command in its verification step

##### Example: skill text on contact addresses

- **GIVEN** the file `plugins/research-submission/skills/add-venue/SKILL.md`
- **WHEN** its text is read
- **THEN** it has a table row starting `| W3 |`; it contains each of the phrases `公務信箱`, `個人信箱`, `看信箱屬於誰，不看網域`, `即使官網把它列為聯絡方式`, `不寫在具名人物底下`, `備註與警告`, `機構的信箱`, `PERSONAL_ADDRESS_EXCEPTIONS`, `unittest discover` and `#21`; and it does not contain the phrase `公務信箱寫在 \`identity.editorial_office.email\``

---
