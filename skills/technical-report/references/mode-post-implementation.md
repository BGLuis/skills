# Mode C — Post-implementation

A report on work **already done**. It is the only mode whose axis is "before × after" — and so
the only one in which the numbers must come from real measurement, not projection.

Titles and labels below are in English; translate them with `locales.md`.

## Contents

- Skeleton
- Section 1 — Executive summary
- Section 2 — Impacts and gains
- Section 3 — Steps executed
- Section 4 — Implementation details
- Section 5 — Files touched
- Section 6 — Verification performed
- Section 7 — What was not verified
- Section 8 — Sources consulted (when applicable)

## Skeleton

```markdown
# <Short name> — <what was delivered>

| Field | Value |
|-------|-------|
| **Status** | ✅ Done |
| **Delivered scope** | <what was done, in one sentence> |
| **Actual effort** | 2.5 d |
| **Base commit** | `abc1234` → `def5678` |

---

## 1. Executive summary

---

## 2. Impacts and gains

---

## 3. Steps executed

---

## 4. Implementation details

---

## 5. Files touched

---

## 6. Verification performed

---

## 7. What was not verified

---

## 8. Sources consulted            (only if the report claims external behavior)

---

> <what did not run in a real environment or on real hardware>
```

If the delivered scope diverged from the plan, the Status becomes `🟡 Partial` and the
`**Delivered scope**` row says what was left out. Do not mark ✅ on partial work.

## Section 1 — Executive summary

What changed and why, in one to three paragraphs. Closes with `**Verdict:**` — a sentence about
the state the module was left in, not about the effort spent.

## Section 2 — Impacts and gains

The core of the report. A before/after table:

```markdown
| Metric | Before | After | Change | Source |
|---|---|---|---|---|
| Initial bundle (transferred) | 152.54 kB | 98.20 kB | **−35.6%** | `ng build`, 1 deterministic build |
| Long tasks in 5 s of scroll (median, n = 10) | 14 | 0 | **−14** | DevTools trace, CPU 4× |
| Chapter open time (median · p95, n = 10) | 840 · 1,120 ms | 310 · 390 ms | **−63%** | `hyperfine --warmup 3` |
| CPU per rendered page | 38 ms | 11 ms | **−71%** | derived from the row above ÷ 22 pages |
```

The last row is the gain **per unit of work** — at least one such row is mandatory when the work
was about performance or cost (`performance-measurement.md` §5).

Rules for this section, no exceptions:

- Each row declares **how it was measured** — in the table itself, in a `Source` column, or in a
  paragraph right below. Without an origin, the number does not go in.
- Time and latency follow the protocol in `performance-measurement.md`: environment, n, warm-up,
  hot/cold state, and median/p95 declared, **the same protocol** before and after. Before and
  after measured on different machines or conditions are not comparable — say so instead of
  publishing the change.
- Say which resource was limiting before and which limits now: the next piece of work starts
  there.
- An unmeasured gain carries `[modeled]` and the table says explicitly it is an estimate. A mixed
  table must separate the two visually.
- If nothing was measured, **the section says so on its first line** instead of showing invented
  numbers: *"No gain was measured; the values below are `[modeled]` from <basis>."*
- Qualitative gains (accessibility, maintainability) go in prose, not in a table with a fake
  percentage.

## Section 3 — Steps executed

Numbered list in the **actual order** they happened, not the planned order. Where execution
diverged from the plan, record the deviation and the reason:

```markdown
3. **Call-site migration (1 d)** — 15 of the 21 fields. The remaining 6 were left for later:
   they depend on `NgControl`, and touching them now would require removing the
   `NG_VALUE_ACCESSOR` provider in the same commit.
```

A silenced deviation is the most common defect of this kind of report. If something was skipped,
this section is the place to say it.

## Section 4 — Implementation details

Organized **by decision**, not by file. Each block: the decision, the `file:line` where it lives,
the relevant snippet, and the discarded alternative.

````markdown
### 4.2 Serialization became a struct, not a flat string

`native/src/debug_stats.h:12-38` + `app/.../DebugStatsParser.kt:20-44`

```cpp
struct DebugStats { float fps; uint32_t triangles; /* … */ };
```

The flat string would have avoided the shared header, but it breaks silently with each new
field — and the Kotlin parser has no way to detect the break.
````

## Section 5 — Files touched

Table `| File | Change |`, with `**new**`, `**deleted**`, or a description of the change. Include
tests, resources, and updated documentation.

## Section 6 — Verification performed

**This is the only section, in all three modes, where checkboxes may be born checked** — and
only for what was really executed in this session:

```markdown
**Run and passing (`npm test`):**
- [x] `chapters.spec.ts` — 3 reading-resume tests, one per content type.

**Not executed:**
- [ ] Scroll trace on the Mobile profile — depends on a physical device.
```

Every measurement item marked `[x]` points to the raw output (benchmark JSON, trace file, build
log) or the path where it was saved. Without the raw output, the measurement is not reproducible.

Marking `[x]` on something that did not run invalidates the whole report. When in doubt, leave
`- [ ]` and explain in section 7.

## Section 7 — What was not verified

Residual risks and verification gaps, in a numbered list, each item opening with a bold thesis.
Include what the implementation left open on purpose and what would only show up in production.

Also include **where we got lucky**: what went right by chance and not by decision — test data
that did not exercise the bad case, a dependency version that happened to already ship the fix.
Unrecorded luck becomes an assumption in the next piece of work.

## Section 8 — Sources consulted

Exists only when the report claims something about an external library, API, or platform
(rule 7 of `conventions.md`) — e.g. to justify a decision in section 4. Format in `research.md`.
