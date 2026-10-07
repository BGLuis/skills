# Mode B — Audit

A critical review of existing code looking for defects. Each defect becomes a **finding** with an
identifier, severity, reproduction, fix, and acceptance criteria.

Titles and labels below are in English; translate them with `locales.md`.

## Contents

- Skeleton
- Section 1 — Executive summary
- Section 2 — Methodology and limits
- Section 3 — Measured evidence
- Sections 4 and 5 — Findings (anatomy of a finding)
- Section 6 — Prioritized backlog
- Section 7 — Risks and what remains to verify
- Section 8 — Sources consulted

## Skeleton

```markdown
# Technical Analysis — `src/app/pages/chapters`

**Date:** 2026-08-23 · **Branch:** `developer` · **Base commit:** `912fc3d`
**Scope:** `src/app/pages/chapters/*` (host of the reading experience)
**Sibling report:** [`OTHER-REPORT.md`](./OTHER-REPORT.md)

---

## 1. Executive summary

---

## 2. Methodology and limits

---

## 3. Measured evidence

---

## 4. Performance findings

---

## 5. Usability and accessibility findings

---

## 6. Prioritized backlog

---

## 7. Risks and what remains to verify

---

## 8. Sources consulted

---

> <what did not run in a real environment or on real hardware>
```

The metadata is a **bold block separated by `·`**, not a table — that is what visually
distinguishes the audit from the analysis. Fields: Date, Branch, Base commit, Scope, and Sibling
report(s) when there are any.

Optional sections, when the material calls for them: `## N. What is done well` (table
`| Place | Decision |`, recording decisions that must survive a refactor),
`## N. Cross-cutting finding: <…>` (a root cause shared by several findings, placed before the
backlog), and `## N. Structural note`.

## Section 1 — Executive summary

One or two paragraphs situating the module, followed by the table of the problems that dominate
the result:

```markdown
| # | Problem | Reach | Severity |
|---|---|---|---|
| P-01 | Synchronous `cdr.detectChanges()` on every scroll tick (20 Hz) | Mobile | High |
| U-01 | Reading resume **always discarded** for text and documents | All | Critical |
```

It must close with a verdict of one to three sentences:

```markdown
**Verdict:** functionally rich, but with a scroll pipeline that spends frame budget with
nothing in return.
```

## Section 2 — Methodology and limits

Subsections: `### 2.1 What was done`, `### 2.2 What was NOT done — limits of this analysis`, and
the reference metrics with the source of each threshold:

```markdown
| Metric | "Good" threshold | Source |
|---|---|---|
| LCP (p75) | ≤ 2.5 s | Core Web Vitals |
| Touch target | ≥ 24 × 24 CSS px | WCAG 2.2 SC 2.5.8 (AA) |
| Initial bundle | 750 kB warning / 1.5 MB error | `angular.json:66-70` |
```

The limits subsection is mandatory and goes in a blockquote when it is critical. If no time was
measured, say so here, not only at the end.

When there was measurement, declare the protocol here once — environment, tool, n, warm-up,
hot/cold state, uncontrolled noise — per `performance-measurement.md` §2. The findings then only
reference it.

## Section 3 — Measured evidence

Only what was actually measured: build output, bundle search, byte count, trace, profile (flame
graph, `pprof`, browser trace — citing the specific frame). Every relevant number says **which
resource limited** the result (`performance-measurement.md` §4). Each subsection has a specific,
affirmative title — `### 3.2 The dynamic import of the PDF is well done`,
`### 3.4 Negative check: styles are NOT duplicated`.

## Sections 4 and 5 — Findings

Heading, literal format:

```markdown
### P-01 · Synchronous `detectChanges()` at 20 Hz during scroll — **High**
### U-03 · Progress bar: 4 px target, no keyboard — **High** (WCAG 2.5.8)
### P-07 · `PreloadAllModules` competes with content — **Low** (out of scope, recorded)
```

`P-NN` for performance, `U-NN` for usability and accessibility, zero-padded · separator ` · ` ·
severity in bold after ` — ` · optional suffix in parentheses for a standard or a scope caveat.

Severity in a **closed** vocabulary: **Critical** · **High** · **Medium** · **Low**.

When the report covers several components, prefix the title with the component:
`### P-05 · `document-reader`: virtualization misaligns after two pages — **Critical**`.

### Anatomy of a finding

````markdown
### P-01 · <title> — **<Severity>**

`file.ts:293-330`

```ts
this.showScrollToTopButton.set(isScrolledDown && isScrollingUp);
this.cdr.detectChanges(); // line 323
```

<paragraph explaining the mechanism — the technical why of the cost, not just the symptom>

| Reach | Impact |
|---|---|
| Mobile | High. With 4× throttling, each cycle competes with the 10 ms/frame budget. |
| Desktop | Low — masked by the CPU. |

**Cost [modeled]:** 20 detection cycles per second × 340 components.

**Reproduction:** open a 40-page chapter on the Mobile profile (CPU 4×), scroll for 5 s, and
record a trace; each `scroll` event fires a `detectChanges` visible on the main track.

**Fix:** remove the call and let the signal propagate, as `reader.component.ts:88` already does.
**Acceptance criteria:** a 5 s scroll trace shows zero long tasks above 50 ms.

---
````

Rules for the final block:
- `**Reproduction:**` gives concrete steps to trigger the defect — input, environment, sequence of
  actions, and what to observe. Whoever fixes it starts here; a finding nobody can reproduce
  cannot have its acceptance criteria checked. If the defect comes only from reading the code and
  was not triggered, say so on that same line.
- `**Fix:**` points to the internal precedent or the source that supports it whenever one exists
  (`file:line` or `[Fn]`, per `research.md`) — a fix that already has a model in the repository
  is cheaper and safer than an invented one.
- `**Fix:**` and `**Acceptance criteria:**` sit on **consecutive lines**, with no blank line
  between them.
- The criterion is always **falsifiable**: a command, a test assertion, a trace observation.
  Never "improve performance".
- Each finding closes with `---`.

Examples of well-formed criteria:

```markdown
**Acceptance criteria:** `grep -l "app-text-reader" dist/browser/*.js` returns a chunk
different from `chapters-component`.
**Acceptance criteria:** three tests, one per content type, that save progress at 50%, remount
the component, and assert the restored position is 50% and not 0.
```

Use a blockquote inside a finding only for weighty caveats:

> **Needs measurement.** The real cost varies by engine — but the fix is cheap and correct
> regardless of the measurement result.

## Section 6 — Prioritized backlog

State the ordering criterion **before** the table:

> Ordered by (user impact × reach) ÷ effort.

```markdown
| Pri | Item | Effort | Reach | Type |
|---|---|---|---|---|
| 1 | **U-01 + U-02** — reading resume (single unit) | M | All | Fix |
| 2 | **P-01** — remove `detectChanges()` from scroll | XS | Mobile | Perf |
```

Effort on the closed scale **XS / S / M / L**. Type: `Perf`, `UX`, `A11y`, `Fix`, `Quality`,
`Architecture`, or hybrids (`A11y/UX`).

Items may group coupled findings (`**U-01 + U-02**`) — and when they do, the text explains why
they are a single unit.

Close with a quick-wins paragraph: *"Items 2, 3, and 7 add up to less than an hour of work and
cover the two largest runtime costs identified."*

Performance items are applied **one at a time**, with a new measurement under the same protocol
between them (`performance-measurement.md` §6) — otherwise the gain of each one cannot be
attributed.

## Section 7 — Risks and what remains to verify

Numbered list, each item opening with a bold thesis and continuing with the verification action:

```markdown
1. **No time number in this report was measured.** Before accepting the performance fixes, run
   a trace over a 40-page chapter.
4. **U-01 has to be fixed together with U-02.** Fixing only the first exposes the second.
```

## Section 8 — Sources consulted

Sources table in the format of `research.md`, with the sources that support the fixes and the
thresholds of section 2. If no external source was used, the section says so in one line.
