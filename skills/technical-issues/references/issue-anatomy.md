# Issue anatomy — drafts, manifest, and bodies

An issue is read alone: in a notification, in a board column, months later. Each body carries its
own evidence, its own base commit, its own sources, and its own definition of done. Nothing points
to "the report".

The rules of the technical-report skill's `conventions.md` still apply inside the bodies —
`file:line`, zero-result searches, `[modeled]`, `[Fn]`, the closed emoji set, bold only in its
three roles — except the report's shape: no numbered H2s, no `---` between sections, no closing
blockquote, and **no hard wrap**. GitHub renders a newline inside an issue as a line break, so a
paragraph wrapped at ~100 columns comes out ragged: write each paragraph and each list item on one
line.

When the drafts directory has a `profile.json` (`repo-profile.md`), the repository's title,
labels, sections, and fields replace the defaults below; the evidence fields stay, inside its
sections.

## Contents

- Drafts directory and manifest
- Keys, numbers, and dependencies
- Titles
- Evidence and base commit
- Epic body
- Sub-issue body (finding)
- Sub-issue body (task)
- Labels per language
- Repository issue templates

## Drafts directory and manifest

```text
<drafts-dir>/
  manifest.json
  profile.json        (only when the repository has issue rules)
  epic.md
  p-02.md
  p-01.md
```

```json
{
  "repo": "acme/shop-api",
  "language": "en",
  "mode": "audit",
  "visibility": "private",
  "issues": [
    {"key": "epic", "kind": "epic", "file": "epic.md",
     "title": "Audit: CSV export holds the whole month in memory", "labels": ["performance"]},
    {"key": "P-02", "kind": "finding", "file": "p-02.md", "parent": "epic",
     "title": "Export: N+1 query for the customer name", "labels": ["performance"]},
    {"key": "P-01", "kind": "finding", "file": "p-01.md", "parent": "epic",
     "title": "Export: stream rows instead of loading the whole result", "labels": ["performance"],
     "blocked_by": ["P-02"]}
  ]
}
```

Top level:

- `language`: `en` or `pt-BR` get full validation; any other code gets structural checks only.
- `mode`: `audit` or `proposal`. An audit epic needs a verdict; a proposal epic does not.
- `visibility`: `public`, `private`, or `internal`, read from `gh repo view --json visibility`.
  The publisher compares it with the live value before creating anything.
- `profile`: optional, the file name of the repository profile.

Per issue:

- `kind`: `epic`, `finding` (mode B), or `task` (mode A). A single issue is a `finding` or `task`
  with no manifest parent.
- `key`: the finding ID (`P-01`, `U-03`, `P-01+P-02`), the task ID (`T1`, `F2`), or `epic`.
- `parent`: the key of an `epic` in this manifest, or an existing issue (`#98` or its URL). An epic
  can only have an existing issue as parent: one level of nesting inside the manifest.
- `blocked_by`: keys of this manifest or existing issues (`#92`). Each one becomes a native
  blocked-by link and must be mirrored under Depends on in the body.
- `labels`, `milestone`, `type` (issue type), `project` (Project title), `assignees`: optional,
  applied at creation. A label, milestone, or type that does not exist makes `gh` fail, so check
  them in step 8.
- `security`: `true` for a security finding; refused when `visibility` is `public`.
- `number`, `url`: written by `publish_issues.py`. Never fill them by hand.
- The order of `issues` is the creation order: epic first, then the sub-issues in priority order.

## Keys, numbers, and dependencies

Until the issues exist, bodies refer to each other by key: the epic's table lists `P-02`, a task
says `**Depends on:** T1`. After creating them, `publish_issues.py` replaces every sub-issue key
with its `#N` in every body, outside code. So:

- write a key only where the issue number belongs;
- pick keys that never occur as ordinary words (`P-01`, `T1.2`, not `fix`);
- the epic's own key is never replaced — nothing links to the epic by key, the parent is native.

A dependency lives in two places that must agree: `blocked_by` in the manifest (the native link
the board and the tools read) and the Depends on field or section in the body (what a reader
sees). The validator checks both directions.

## Titles

- Plain text, no Markdown, no emoji, no trailing period, ≤ ~80 characters so it fits a board card
  (warning above 80, error above 100 or the profile's `title_max`).
- Sub-issue: `<component>: <what is wrong or what to do>` — `Export: N+1 query for the customer
  name`, `ChapterList: virtualize with variable height`. The finding ID and severity go in the body
  and in labels, not in the title.
- Epic: `<Audit|Proposal>: <outcome in one line>` — translated per language.
- A profile's `title_pattern` replaces both (for example `fix: <subject>` and `Epic: <outcome>`).

## Evidence and base commit

- `**Evidence:**` holds a `file:line` (`src/api/export/handler.ts:22-40`), a permalink, or a
  zero-result search — in the field itself, not elsewhere in the body.
- Every issue names the commit its line numbers refer to: a `**Base commit:**` field, or a
  permalink with the commit SHA. Lines drift as the code changes; the commit keeps them checkable.
- A permalink (`https://github.com/<owner>/<repo>/blob/<sha>/<path>#L31-L35`) renders as a code
  snippet in an issue of the same repository, so it can replace a pasted excerpt. Paste the code
  only when annotating it, and never paste secrets: the validator rejects tokens and keys.

## Epic body

````markdown
**Branch:** `main` · **Base commit:** `9f3e21a` · **Scope:** `src/api/export/*`

<one or two paragraphs: what was analyzed and what dominates the result>

**Verdict:** <one to three sentences>  (audit only)

| Order | Key | Sub-issue | Severity | Effort |
|---|---|---|---|---|
| 1 | P-02 | N+1 query for the customer name | High | XS |
| 2 | P-01 | Stream rows instead of loading the whole result | Critical | S |

> Ordered by (user impact × reach) ÷ effort. Apply one at a time and measure between them.

### Limits of this analysis
<what was not done: no production measurement, no concurrency…>  (mode A: ### Non-goals)

### Risks
1. **<thesis>** <consequence and verification action>

**Not verified:** <what stayed `[modeled]`, what has not run on real hardware or in production>

### Sources
| # | Source | Type | Version | Consulted on |
|---|---|---|---|---|
| F1 | … | Official doc | 4.7.0 | 2026-09-23 |
````

Every sub-issue key appears in a body row of the epic's table — or as an item of a checklist
(`- [ ] P-02 …`) when the repository lists children that way. Drop the Severity and Effort columns
when the profile forbids those fields. Sources used only by one sub-issue live in that sub-issue,
not here.

## Sub-issue body (finding)

````markdown
**Evidence:** `src/api/export/handler.ts:22-40` · **Base commit:** `9f3e21a`

```ts
const rows = await db.query(sql, [month]); // line 24 — 180 thousand objects
res.send(toCsv(rows.rows));                 // line 39 — ~95 MB string
```

<mechanism: the technical why, not just the symptom>

**Severity:** Critical · **Effort:** S · **Reach:** every export · **Depends on:** P-02

**Reproduction:** <input, environment, steps, what to observe — or "found by reading the code, not triggered">

**Fix:** <what to change, pointing to the internal precedent `file:line` or the source [F1]>
**Acceptance criteria:** <falsifiable: a command, a test assertion, a trace observation>

**Not verified:** <optional here; mandatory when the issue has no parent in the manifest>

### Sources
| # | Source | Type | Version | Consulted on |
|---|---|---|---|---|
| F1 | [`pg-query-stream` — README](https://…) | Official doc | 4.7.0 | 2026-09-23 |
````

- `**Fix:**` and `**Acceptance criteria:**` on consecutive lines, as in the report.
- The acceptance criterion may be a checklist when there is more than one condition — always
  unchecked `- [ ]`; nothing in a new issue has been done. It names a command, a number, or a
  source; the validator warns when it names none.
- Citations `[Fn]` are numbered per issue, starting at F1, and every one is in that issue's table.
- `**Severity:**`, `**Effort:**`, and `**Reach:**` stay out of the body when the profile says
  those live elsewhere (a Project field, a label).

## Sub-issue body (task)

Same as a finding, with `**Implementation:**` in place of `**Reproduction:**` + `**Fix:**`:

````markdown
**Evidence:** `src/reader/ChapterList.tsx:41-58` — renders all 2,400 `<li>` with no window. **Base commit:** `4c1d7e2`

**Precedent:** `src/shared/virtual-list.tsx:12-88` — **reuse** the hook; **diverge** on height [F1].

**Effort:** 0.5 d · **Depends on:** T1

**Implementation:** <the steps, reusing the precedent; what not to do>
**Acceptance criteria:**
- [ ] 1-line and 3-line items do not overlap with `dynamicHeight` (`npm test`).
- [ ] Restoring chapter 1,800 puts item 1,800 at the top [F1].
````

`**Implementation:**` and `**Acceptance criteria:**` on consecutive lines. A task's absence of code
("nothing exists yet") is proven with the zero-result search in `**Evidence:**`.

## Labels per language

Validated labels are marked **(v)**. For other languages, translate once, use consistently, and
check by hand. Keep `LOCALES` in `scripts/validate_issues.py` in sync with this table.

| en | pt-BR |
|---|---|
| `**Evidence:**` **(v)** | `**Evidência:**` |
| `**Reproduction:**` **(v, finding)** | `**Reprodução:**` |
| `**Fix:**` **(v, finding)** | `**Correção:**` |
| `**Implementation:**` **(v, task)** | `**Implementação:**` |
| `**Acceptance criteria:**` **(v)** | `**Critério de aceite:**` |
| `**Verdict:**` **(v, audit epic)** | `**Veredicto:**` |
| `**Not verified:**` **(v, epic or issue with no manifest parent)** | `**Não verificado:**` |
| `**Base commit:**` **(v)** | `**Commit base:**` |
| `**Depends on:**` · `## Depends on` **(v)** | `**Depende de:**` · `## Depende de` |
| `**Severity:**` · `**Effort:**` · `**Reach:**` · `**Precedent:**` | `**Severidade:**` · `**Esforço:**` · `**Alcance:**` · `**Precedente:**` |
| `### Sources` · `### Risks` · `### Limits of this analysis` · `### Non-goals` | `### Fontes` · `### Riscos` · `### Limites desta análise` · `### Não-objetivos` |
| `Audit:` · `Proposal:` (epic title) | `Auditoria:` · `Proposta:` |

Severity, effort, and source-type vocabularies are the report's, from `locales.md`.

## Repository issue templates

If `.github/ISSUE_TEMPLATE/` exists, read it before writing and turn what it asks into the profile
(`repo-profile.md`, "Mapping an issue form"):

- **Markdown template** (`*.md`): keep its headings in order and put the anatomy above inside
  them (evidence and mechanism under the description heading, reproduction under the steps
  heading, and so on). Use its `labels:` from the front matter unless the user says otherwise.
- **Issue form** (`*.yml`): a form is a web UI; an issue created with `--body-file` gets free
  Markdown, not the form. Reproduce it: the form's `title:` prefix, its `labels:`, each field as a
  heading in the form's order at the level the recent issues use, its default `value:` lines, and
  its `markdown` instructions as `post_create` steps.

The validated labels above must still appear — the template organizes the body, it does not
replace the evidence.
