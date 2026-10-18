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
- Acceptance criteria
- Feasibility
- Open questions
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
- `spike`: `true` for a task whose job is to answer a feasibility question (see Feasibility). Only a
  task can be a spike, and a spike needs no `**Feasibility:**` field.
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
- With `--repo <repository-root>`, the validator opens every `file:line` in prose and every
  permalink of the manifest's repository at its commit, and rejects a file that is not there or a
  line past its end. A location in another repository goes as a permalink to that repository; it
  is not checked.

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
**Goal:** <what the user or the system gets once this is closed, in one sentence>

**Evidence:** `src/api/export/handler.ts:22-40` · **Base commit:** `9f3e21a`

```ts
const rows = await db.query(sql, [month]); // line 24 — 180 thousand objects
res.send(toCsv(rows.rows));                 // line 39 — ~95 MB string
```

<mechanism: the technical why, not just the symptom>

**Baseline:** peak RSS 1.12 GB median, n = 10 (protocol in the epic)  (when a criterion has a threshold)

**Severity:** Critical · **Effort:** S · **Reach:** every export · **Depends on:** P-02

**Reproduction:** <input, environment, steps, what to observe — or "found by reading the code, not triggered">

**Fix:** <what to change, pointing to the internal precedent `file:line` or the source [F1]>
**Acceptance criteria:**
- [ ] <condition, with its check in `code`: `npm test -- export.stream`, `VmHWM` ≤ 100 MB>

**Not verified:** <what stayed `[modeled]` or did not run; "nothing beyond the epic" when the epic says it all>

### Sources
| # | Source | Type | Version | Consulted on |
|---|---|---|---|---|
| F1 | [`pg-query-stream` — README](https://…) | Official doc | 4.7.0 | 2026-09-23 |
````

- `**Goal:**` comes first, so the issue makes sense in a notification without its epic. In a
  repository whose sections include a `Goal` heading (`Objetivo` in pt-BR), that heading counts.
- `**Fix:**` and `**Acceptance criteria:**` on consecutive lines, as in the report.
- `**Not verified:**` is in every issue: whoever picks up a sub-issue does not read the epic first.
- Citations `[Fn]` are numbered per issue, starting at F1, and every one is in that issue's table.
- `**Severity:**`, `**Effort:**`, and `**Reach:**` stay out of the body when the profile says
  those live elsewhere (a Project field, a label).

## Sub-issue body (task)

Same as a finding, with `**Feasibility:**` and `**Implementation:**` in place of
`**Reproduction:**` + `**Fix:**`:

````markdown
**Goal:** the chapter list opens and scrolls without rendering the 2,400 items off screen.

**Evidence:** `src/reader/ChapterList.tsx:41-58` — renders all 2,400 `<li>` with no window. **Base commit:** `4c1d7e2`

**Feasibility:** `src/shared/virtual-list.tsx:12-88` already windows a fixed-height list — **reuse** the window math; **diverge** on height, measured per item [F1].

**Effort:** 0.5 d · **Depends on:** T1

**Implementation:** <the steps, reusing the precedent; what not to do>
**Acceptance criteria:**
- [ ] 1-line and 3-line items do not overlap with `dynamicHeight` (`npm test -- virtual-list`).
- [ ] Restoring chapter 1,800 puts item 1,800 at the top, asserted on `scrollTop` (`npm test -- restore`).

**Not verified:** <what stayed `[modeled]` or did not run>
````

`**Goal:**` comes first, as in a finding. `**Implementation:**` and `**Acceptance criteria:**` on
consecutive lines. A task's absence of code ("nothing exists yet") is proven with the zero-result
search in `**Evidence:**`.

## Acceptance criteria

An issue is closed when its criteria hold, so each criterion is the test of the issue. The
validator rejects a criterion that breaks the first three rules; the last two are yours to check
before the preview.

1. **Each criterion names its check** — the command, the test, the assertion, or the trace
   observation, in `code`, or the source `[Fn]` it is checked against. A checklist item is one
   criterion and names its own check; always unchecked `- [ ]`, since nothing in a new issue has
   been done. ❌ "Restoring chapter 1,800 puts it at the top." ✅ "… asserted on `scrollTop`
   (`npm test -- restore`)."
2. **No vague term without a threshold.** *Faster*, *better*, *cleaner*, *improves*, *as expected*,
   *properly* (pt-BR: *mais rápido*, *melhorar*, *corretamente*, *como esperado*…) say nothing
   until a number says how much: ❌ "export is faster" ✅ "export takes ≤ 2 s median, n = 10".
3. **Every threshold has a baseline.** A criterion with `≤`, `<`, `at most`, `no máximo`… needs a
   `**Baseline:**` field with today's value — measured, with the protocol, or marked `[modeled]`
   with the model. Without it, nobody knows whether the threshold is a 10× change or none.
4. **Every item of the scope is covered.** Each `**Fix:**` or `**Implementation:**` step, and each
   item of a `Scope` section, is closed by at least one criterion. A step with no criterion is
   either not needed or not verifiable: cut it or write its criterion.
5. **A destructive or one-way change has a negative criterion.** A migration that drops data, a
   delete, a flag that changes a default: say what must still hold (the rows that survive, the
   rollback that restores the previous state, the request that is still refused).

## Feasibility

A task estimated as work but resting on an untested assumption is a guess. Every task carries a
`**Feasibility:**` field with the proof that it can be built as written, and the validator rejects
the field when it names none of:

- an **internal precedent**, `file:line`: the repository already does something like it;
- a **source** `[Fn]` of the installed version: the library or platform supports it;
- a **probe**: the throwaway experiment that tried it, as a link (a gist, a branch, a CL) or as its
  commands and output in a code block. A probe "outside the repository" with neither cannot be
  repeated by a reviewer, and does not count;
- the **spike** that answers it: a task of the manifest with `"spike": true`, which must also be in
  `blocked_by`, since the answer comes first.

When none exists, the task is a spike: its goal is the question, its criterion is the answer (yes
or no, with the number that decides it), and the work it unblocks is a separate task that waits
for it. In mode B, the `**Fix:**` field plays this role: point it to the precedent or the source
whenever one exists.

## Open questions

An open question is work that is not done yet. When the analysis leaves one, list it under
`### Open questions` (`### Perguntas em aberto`) as an unchecked checklist, one question per item;
the validator rejects prose or plain bullets there. The criteria never depend on an unanswered
question: write the criterion once the answer is in the body. The preview lists the open
questions, so the user decides whether the issue can be filed before they are answered.

## Labels per language

Validated labels are marked **(v)**. For other languages, translate once, use consistently, and
check by hand. Keep `LOCALES` in `scripts/validate_issues.py` in sync with this table.

| en | pt-BR |
|---|---|
| `**Goal:**` · `## Goal` **(v, finding and task)** | `**Objetivo:**` · `## Objetivo` |
| `**Evidence:**` **(v)** | `**Evidência:**` |
| `**Reproduction:**` **(v, finding)** | `**Reprodução:**` |
| `**Fix:**` **(v, finding)** | `**Correção:**` |
| `**Implementation:**` **(v, task)** | `**Implementação:**` |
| `**Feasibility:**` **(v, task)** | `**Viabilidade:**` |
| `**Acceptance criteria:**` **(v)** | `**Critério de aceite:**` |
| `**Baseline:**` **(v, when a criterion has a threshold)** | `**Linha de base:**` |
| `**Verdict:**` **(v, audit epic)** | `**Veredicto:**` |
| `**Not verified:**` **(v)** | `**Não verificado:**` |
| `**Base commit:**` **(v)** | `**Commit base:**` |
| `**Depends on:**` · `## Depends on` **(v)** | `**Depende de:**` · `## Depende de` |
| `**Severity:**` · `**Effort:**` · `**Reach:**` | `**Severidade:**` · `**Esforço:**` · `**Alcance:**` |
| `### Open questions` **(v)** | `### Perguntas em aberto` |
| `### Sources` · `### Risks` · `### Limits of this analysis` · `### Non-goals` | `### Fontes` · `### Riscos` · `### Limites desta análise` · `### Não-objetivos` |
| `Audit:` · `Proposal:` (epic title) | `Auditoria:` · `Proposta:` |

Severity, effort, and source-type vocabularies are the report's, from `locales.md`. The vague
terms and threshold words of each language are in `LOCALES` (`vague`, `threshold`).

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
