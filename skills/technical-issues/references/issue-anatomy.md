# Issue anatomy — drafts, manifest, and bodies

An issue is read alone: in a notification, in a board column, months later. Each body carries its
own evidence, its own sources, and its own definition of done. Nothing points to "the report".

The rules of the technical-report skill's `conventions.md` still apply inside the bodies —
`file:line`, zero-result searches, `[modeled]`, `[Fn]`, the closed emoji set, bold only in its
three roles — except the report's shape (numbered H2s, `---` between sections, closing
blockquote), which an issue does not use.

## Contents

- Drafts directory and manifest
- Titles
- Epic body
- Sub-issue body (finding)
- Sub-issue body (task)
- Labels per language
- Repository issue templates

## Drafts directory and manifest

```text
<drafts-dir>/
  manifest.json
  epic.md
  p-02.md
  p-01.md
```

```json
{
  "repo": "acme/shop-api",
  "language": "en",
  "issues": [
    {"key": "epic", "kind": "epic", "file": "epic.md",
     "title": "Audit: CSV export holds the whole month in memory", "labels": ["performance"]},
    {"key": "P-02", "kind": "finding", "file": "p-02.md", "parent": "epic",
     "title": "Export: N+1 query for the customer name", "labels": ["performance"]},
    {"key": "P-01", "kind": "finding", "file": "p-01.md", "parent": "epic",
     "title": "Export: stream rows instead of loading the whole result", "labels": ["performance"]}
  ]
}
```

- `language`: `en` or `pt-BR` get full validation; any other code gets structural checks only.
- `kind`: `epic`, `finding` (mode B), or `task` (mode A). A single issue is a `finding` or `task`
  with no `parent`.
- `key`: the finding ID (`P-01`, `U-03`, `P-01+P-02`), the task ID (`T1`, `F2`), or `epic`. The
  epic's table refers to the sub-issues by key until the real numbers exist.
- `parent`: the key of an `epic`. One level only: an epic has no parent.
- The order of `issues` is the creation order: epic first, then the sub-issues in priority order.

## Titles

- Plain text, no Markdown, no emoji, no trailing period, ≤ ~80 characters so it fits a board card.
- Sub-issue: `<component>: <what is wrong or what to do>` — `Export: N+1 query for the customer
  name`, `ChapterList: virtualize with variable height`. The finding ID and severity go in the body
  and in labels, not in the title.
- Epic: `<Audit|Proposal>: <outcome in one line>` — translated per language.

## Epic body

````markdown
**Branch:** `main` · **Base commit:** `9f3e21a` · **Scope:** `src/api/export/*`

<one or two paragraphs: what was analyzed and what dominates the result>

**Verdict:** <one to three sentences>

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

Every sub-issue key appears in the epic's table. After publishing, the key column is replaced by the
real `#N` (`github-publishing.md`). Sources used only by one sub-issue live in that sub-issue, not
here.

## Sub-issue body (finding)

````markdown
**Evidence:** `src/api/export/handler.ts:22-40`

```ts
const rows = await db.query(sql, [month]); // line 24 — 180 thousand objects
res.send(toCsv(rows.rows));                 // line 39 — ~95 MB string
```

<mechanism: the technical why, not just the symptom>

**Severity:** Critical · **Effort:** S · **Reach:** every export

**Reproduction:** <input, environment, steps, what to observe — or "found by reading the code,
not triggered">

**Fix:** <what to change, pointing to the internal precedent `file:line` or the source [F1]>
**Acceptance criteria:** <falsifiable: a command, a test assertion, a trace observation>

**Not verified:** <optional here; mandatory when the issue has no parent>

### Sources
| # | Source | Type | Version | Consulted on |
|---|---|---|---|---|
| F1 | [`pg-query-stream` — README](https://…) | Official doc | 4.7.0 | 2026-09-23 |
````

- `**Fix:**` and `**Acceptance criteria:**` on consecutive lines, as in the report.
- The acceptance criterion may be a checklist when there is more than one condition — always
  unchecked `- [ ]`; nothing in a new issue has been done.
- Citations `[Fn]` are numbered per issue, starting at F1, and every one is in that issue's table.

## Sub-issue body (task)

Same as a finding, with `**Implementation:**` in place of `**Reproduction:**` + `**Fix:**`:

````markdown
**Evidence:** `src/reader/ChapterList.tsx:41-58` — renders all 2,400 `<li>` with no window.

**Precedent:** `src/shared/virtual-list.tsx:12-88` — **reuse** the hook; **diverge** on height [F1].

**Effort:** 0.5 d · **Depends on:** T1

**Implementation:** <the steps, reusing the precedent; what not to do>
**Acceptance criteria:**
- [ ] 1-line and 3-line items do not overlap with `dynamicHeight` (`npm test`).
- [ ] Restoring chapter 1,800 puts item 1,800 at the top [F1].
````

A task's absence of code ("nothing exists yet") is proven with the zero-result search in
`**Evidence:**`.

## Labels per language

Validated labels are marked **(v)**. For other languages, translate once, use consistently, and
check by hand.

| en | pt-BR |
|---|---|
| `**Evidence:**` **(v)** | `**Evidência:**` |
| `**Reproduction:**` **(v, finding)** | `**Reprodução:**` |
| `**Fix:**` **(v, finding)** | `**Correção:**` |
| `**Implementation:**` **(v, task)** | `**Implementação:**` |
| `**Acceptance criteria:**` **(v)** | `**Critério de aceite:**` |
| `**Verdict:**` **(v, epic)** | `**Veredicto:**` |
| `**Not verified:**` **(v, epic or single issue)** | `**Não verificado:**` |
| `**Severity:**` · `**Effort:**` · `**Reach:**` · `**Depends on:**` · `**Precedent:**` | `**Severidade:**` · `**Esforço:**` · `**Alcance:**` · `**Depende de:**` · `**Precedente:**` |
| `### Sources` · `### Risks` · `### Limits of this analysis` · `### Non-goals` | `### Fontes` · `### Riscos` · `### Limites desta análise` · `### Não-objetivos` |
| `Audit:` · `Proposal:` (epic title) | `Auditoria:` · `Proposta:` |

Severity, effort, and source-type vocabularies are the report's, from `locales.md`.

## Repository issue templates

If `.github/ISSUE_TEMPLATE/` exists, read it before writing:

- **Markdown template** (`*.md`): keep its headings in order and put the anatomy above inside
  them (evidence and mechanism under the description heading, reproduction under the steps
  heading, and so on). Use its `labels:` from the front matter unless the user says otherwise.
- **Issue form** (`*.yml`): a form is a web UI; an issue created with `--body-file` gets free
  Markdown, not the form. Reproduce the form's structure instead: each field `label` becomes a
  `###` heading, in the form's order, filled with the matching part of the anatomy, and the form's
  `labels:` are applied with `--label`.

The validated labels above must still appear — the template organizes the body, it does not
replace the evidence.
