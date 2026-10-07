# Mode A — Analysis / proposal

A report written **before** implementing. The axis is not "before × after", it is
**"what exists" × "what is missing"**. Nothing here was executed — and the report has to say so.

It is the mode that depends most on `research.md`: do the six steps before writing section 2.
A plan without precedents and without sources is an opinion.

Titles and labels below are in English; translate them with `locales.md`.

## Contents

- Skeleton
- Section 1 — Current state (includes precedents and non-goals)
- Section 2 — Tasks or design decisions
- Section 3 — Plan
- Section 4 — Pitfalls
- Section 5 — Verification
- Section 6 — Risks
- Section 7 — Files touched
- Section 8 — Sources consulted

## Skeleton

```markdown
# <Short name> — <what the report proposes, in lowercase>

| Field | Value |
|-------|-------|
| **Status** | 🟡 Partial — <reason in one sentence> |
| **Coverage** | ~35% (3 of 8 tasks) |
| **Effort** | 5–7 dev-days for the full scope; 1–1.5 d for the minimum viable |
| **Depends on** | Nothing (can start now) |

---

## 1. Current state — evidence

---

## 2. Task-by-task analysis        |  ## 2. The <N> design decisions

---

## 3. Implementation plan

---

## 4. Pitfalls

---

## 5. Verification

---

## 6. Risks

---

## 7. Files touched

---

## 8. Sources consulted

---

> No item in this report was executed on <environment/hardware>. The whole analysis comes
> from reading the code on branch `<branch>` (commit `<sha>`); validation is listed in
> section 5 as pending.
```

Additional metadata fields, as needed: `**Blocks**`, `**Shares code with**`, `**Attention**`,
`**Closes requirement**`. The fixed core is Status / Coverage / Effort / Depends on.

## Section 1 — Current state

Prose anchored in `file:line`, short code blocks (3–8 lines) with an origin comment on the first
line, and proofs of absence by search.

Useful subsections: `### What exists`, `### What does not exist`,
`### ⚠️ Defect found: <…>`, `### 1.4 Five defects already present in the current code`.

Two subsections are **mandatory**:

- `### Precedents in the code` — what the repository already solves in a similar way (step 1 of
  `research.md`), with `file:line` and the verdict **reuse** or **diverge, because…**. If there
  is no precedent, the zero-result search goes here.

  ```markdown
  - `src/shared/virtual-list.ts:12-88` — already virtualizes the book list with fixed height.
    **Reuse** the API; **diverge** on height measurement, which is variable here [F1].
  ```

- `### Non-goals` — what the plan deliberately does **not** solve, in a short list. It keeps the
  implementation from growing silently and the reviewer from asking for what was left out on
  purpose.

When listing pre-existing defects, make clear they were not caused by the request:

> None of them is caused by the request — but all of them go through the same code that will be
> rewritten, and the cost of fixing them now is close to zero.

## Section 2 — two forms

**Task by task** (when there is a spec with numbered tasks):

```markdown
| Task | Status | Notes |
|---|---|---|
| **T1.1** Environment loading pipeline | ❌ | No directory structure, no `config.json`. |
```

**Design decisions** (when the request is a feature): numbered H3s `### 2.1`…, the last one
being `### 2.N What not to do`. Trade-offs in a table
`| Option | What it is | Cost | Basis | Verdict |`, with `**Recommended**` / `Rejected: …`.

The `Basis` column says what supports the option: a precedent (`virtual-list.ts:12`), a source
(`[F1]`), or `[modeled]`. A recommended option with a `[modeled]` basis needs a sentence saying
why no source was found.

## Section 3 — Plan

Numbered list with the effort inside the step's bold:

```markdown
1. **Scene foundation (3–4 d)** — `EnvironmentAsset` in C++: struct, loading via
   `AAssetManager`, lifecycle. Reuses the loader from `texture_cache.cpp:40-95`.
```

When the step reuses a precedent or follows a reference example, say which — that is what keeps
the implementation from creating a second version of what already exists.

Or a phase table, when there is sequencing: `| Phase | Content | Effort |`, with rows
`| **F0** | … | 0.5 d |`.

Always close with the two totals and the order:

```markdown
**Minimum viable** (only what was literally asked): F1 + F2 ≈ 1.5–2 d.
**Full scope:** F0–F6 ≈ 5.5–7 d.

Order matters: doing F3 before F4 avoids redoing the formatting for every new field.
```

## Section 4 — Pitfalls

Table `| Pitfall | Mitigation |` — granular and actionable. It is a section **distinct** from
Risks: a pitfall is technical and immediate, a risk is about schedule and strategy.

Title variants: `## 4. Confirmed pitfalls`, `## 4. Spec pitfalls × actual situation`.

## Section 5 — Verification

Checkboxes grouped by **where the test runs**, with a bold label:

```markdown
**Automatable on the host (`./gradlew testDebugUnitTest`):**
- [ ] `FeatureFlags`: `DEBUG_STATS_PANEL` defaults to `false` (the test fails if someone turns
      it on by mistake — that is what the test guards).

**Only on the Quest 3 (declare explicitly as not verified until it runs):**
- [ ] The modal opens at 1.64 m without clipping the UI quad.
```

Rules:
- **No checkbox is born checked.** Always use `- [ ]` — nothing was executed.
- The item states **the invariant the test guards**, not the test step.
- Each item points to the decision or source it validates (step 6 of `research.md`): a
  documented limit becomes a test case — *"a list of 10,000 items scrolls without a long task
  > 50 ms [F1]"*.
- A performance item declares the protocol from `performance-measurement.md`: tool, n, metric
  (median/p95), and the threshold that passes — *"`hyperfine --runs 10`, median ≤ 120 ms"*.
- An item's continuation is indented 6 spaces, aligned under the text.

If the section is hardly automatable, open with the frank sentence:
*"Automatable in CI/host: **almost nothing** — this section is essentially graphical."*

## Section 6 — Risks

Numbered list, each item opening with a **bold thesis** followed by the consequence:

```markdown
1. **3D assets are the critical path, not the code.** If it depends on in-house modeling, this
   section alone may consume half of the phase's schedule.
```

## Section 7 — Files touched

Table `| File | Change |`, with bold markers in the second column: `**new**`,
`**deleted** at the end of F2`, `same, Vulkan path`. Include test files, resources, and
documentation to update.

## Section 8 — Sources consulted

Sources table in the format of `research.md`. If a needed source could not be consulted, say
which in a sentence below the table and which claims were left `[modeled]` because of it. If the
report used no external source, the section says so in one line, and why.
