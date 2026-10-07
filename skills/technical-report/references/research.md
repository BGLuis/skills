# Research and grounding — before writing

A report that only describes the code says **what exists**. To say **what to do**, it needs a
basis: what the repository itself has already solved, what the official documentation of the
installed version guarantees, and how mature projects do the same thing. Without that basis, the
plan reinvents what exists, uses an API from the wrong version, or repeats a known mistake — and
the implementation inherits all of it.

## Contents

- Depth per mode
- The six steps
- Evidence hierarchy
- Research budget
- How to record it in the report

## Depth per mode

| Mode | Depth | Mandatory steps |
|---|---|---|
| **A — Analysis/proposal** | Full | 1 to 6 |
| **B — Audit** | Medium — only to support each `**Fix:**` | 1, 2, 3, and 5 |
| **C — Post-implementation** | Minimal — confirm the delivered work follows the docs | 2 and 3, and only where the report claims something about an external API |

## The six steps

In increasing order of cost. Do not jump to 4 without having done 1.

1. **Internal precedents.** Search the repository for what already solves a similar problem: the
   same library used in another module, the same pattern (cache, queue, retry, virtualization),
   a sibling feature, the area's tests, and the written conventions (ADRs, `CONTRIBUTING`, lint
   configs). Search by API name, by pattern, and by symptom — not only by module name. Record
   each precedent with `file:line` and decide explicitly:
   - **reuse** — the plan calls or extends what exists;
   - **diverge** — and say why (the precedent has a defect, the version differs, the requirement
     differs). A divergence without justification becomes an inconsistency in the code.

   If there is no precedent, prove it with the zero-result search (rule 2 of `conventions.md`).

2. **Pin versions.** Read the manifest and the lockfile (`package-lock.json`, `pnpm-lock.yaml`,
   `poetry.lock`, `go.sum`, `Cargo.lock`, `build.gradle`…) and note the **installed** version of
   each dependency involved. Every lookup in steps 3 to 5 is made against that version. If the
   library's current version is different, record the deprecations and the migration guide
   between the two — the solution recommended today often does not exist in the installed
   version.

3. **Official documentation.** Consult the documentation for the pinned version: use an
   up-to-date documentation lookup tool when the environment offers one (e.g. Context7), or the
   project's official site. Look for the page of the feature used, the documented limits (size,
   concurrency, timeouts), and the performance notes. **Never cite the model's memory as a
   source**: API behavior not checked in this session is `[modeled]`.

4. **Reference implementations.** Look for code in mature repositories that use the same API:
   first the examples maintained by the library's authors, then widely used, active projects.
   Extract the **pattern** (call order, error handling, configuration), do not paste the code. If
   any snippet is copied, note the license.

5. **Known pitfalls.** Read the changelog and the release notes of the pinned version and look
   for open issues about the feature. An open bug that affects the plan goes into Pitfalls
   (mode A) or Risks, with the source.

6. **Derive the validation.** For each decision in the report, close the chain:

   ```text
   decision → source that supports it ([Fn] or file:line) → verification that confirms it
   ```

   The verification comes from the source itself whenever possible: the documented limit becomes
   the test case, the maintainer's example becomes the expected behavior, the internal precedent
   becomes the regression test. Performance numbers follow `performance-measurement.md`.

## Evidence hierarchy

When two sources disagree, the higher one wins — and the disagreement is recorded as ⚠️:

1. Repository code (`file:line`) and measurements made in this session.
2. Official documentation of the installed version.
3. Examples and code maintained by the library's authors.
4. Mature third-party projects.
5. Articles, forum answers, posts — only as a lead to find a level 1 to 4 source. They never
   support a recommendation on their own.

## Research budget

The goal is maximum grounding for minimum reading. **Stop when each decision in the report has a
level 1 to 3 basis.** Indicative limits per decision:

| Step | Indicative limit |
|---|---|
| Internal precedents | up to 3 places — the most similar, not all of them |
| Official documentation | 2–4 pages |
| Reference implementations | up to 2 projects |
| Pitfalls | changelog of the version + 1 issue search |

Going past the limit is allowed when the decision still has no basis — and that becomes a
sentence in the report. Research that supports no decision does not go into the report.

If a source cannot be consulted (no network, private doc, undocumented version), say so in the
sources section and mark as `[modeled]` the claims that depended on it.

## How to record it in the report

Internal precedents go in the body, with `file:line` (mode A: `### Precedents in the code`, in
section 1). External sources are cited inline as `[F1]`, `[F2]`… and listed in the **last
numbered section**, `## N. Sources consulted`, before the closing blockquote:

```markdown
| # | Source | Type | Version | Consulted on | Supports |
|---|---|---|---|---|---|
| F1 | [TanStack Virtual — `useVirtualizer`](https://tanstack.com/virtual/latest/docs/api/virtualizer) | Official doc | 3.10.8 | 2026-09-23 | Decision 2.1; verification 5.2 |
| F2 | `TanStack/virtual` — `examples/react/dynamic` | Maintainer example | 3.10.8 | 2026-09-23 | Dynamic height measurement |
```

`Type` uses the hierarchy's vocabulary: `Official doc`, `Maintainer example`, `Third-party
project`, `Changelog`, `Issue`, `Article` (translations in `locales.md`). Every listed source is
cited at least once in the text, and every citation points to a row of the table.
