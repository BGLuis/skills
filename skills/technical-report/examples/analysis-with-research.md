# Chapter list — virtualization with variable height

<!-- Illustrative mode A example. Paths, versions, and numbers are fictional; in a real report
     each one comes from reading the repository and from the sources consulted in the session. -->

| Field | Value |
|-------|-------|
| **Status** | ❌ Not started — the list renders all 2,400 items at once |
| **Coverage** | ~0% (0 of 5 tasks) · ~40% reusable from `virtual-list.tsx` |
| **Effort** | 2–3 dev-days for the full scope; 1 d for the minimum viable |
| **Depends on** | Nothing (can start now) |

---

## 1. Current state — evidence

`ChapterList` mounts one `<li>` per chapter, with no window (`src/reader/ChapterList.tsx:41-58`).
A reference book opens 2,400 chapters; the component has no stable `key` per chapter — it uses
the index (`:47`).

### Precedents in the code

- `src/shared/virtual-list.tsx:12-88` — already virtualizes the bookshelf with
  `@tanstack/react-virtual`. **Reuse** the hook and the scroll container; **diverge** on height:
  the bookshelf uses a fixed `estimateSize` (`:30`), and here titles wrap over 1–3 lines, which
  requires dynamic measurement with `measureElement` [F1] [F2].
- `src/shared/virtual-list.test.tsx:8-40` — test with a fake `ResizeObserver`; it is the mold for
  the tests in section 5.

### Non-goals

- Search inside the chapter list — stays as it is.
- Horizontal scrolling or grid.
- Replacing the virtualization library.

### What does not exist

No other use of `measureElement` in the repository:

```bash
grep -rn "measureElement" src/
# → 0 results
```

---

## 2. The 3 design decisions

### 2.1 Height measurement

| Option | What it is | Cost | Basis | Verdict |
|---|---|---|---|---|
| Fixed `estimateSize` | Same as the bookshelf | 0.5 d | `virtual-list.tsx:30` | Rejected: 3-line titles overlap |
| `measureElement` + `ResizeObserver` | Measures each item on mount | 1 d | [F1] [F2] | **Recommended** |

### 2.2 Library version

`package-lock.json:2210` pins `@tanstack/react-virtual` at `3.10.8`. `measureElement` exists in
that version [F1]; there is no reason to upgrade within this scope.

### 2.3 What not to do

Do not create a second virtual list component: extending `virtual-list.tsx` with a
`dynamicHeight` option keeps a single place to fix scrolling defects.

---

## 3. Implementation plan

1. **`dynamicHeight` option in `virtual-list.tsx` (0.5 d)** — wires `measureElement` to the
   item's ref, as in the maintainer example [F2]. Reuses the container from `:52-70`.
2. **Migrate `ChapterList` (0.5 d)** — replace the `map` with `VirtualList` and the `key` with
   `chapter.id`.
3. **Restore the reading position (0.5–1 d)** — `scrollToIndex` with `align: 'start'` [F1].

**Minimum viable** (only what was literally asked): steps 1 and 2 ≈ 1 d.
**Full scope:** steps 1–3 ≈ 1.5–2 d, plus 0.5 d of tests.

Order matters: step 1 first leaves the bookshelf as the regression test for the change to the
shared component.

---

## 4. Pitfalls

| Pitfall | Mitigation |
|---|---|
| `scrollToIndex` before measurement lands on the estimated position | Call it after the first `measure`, as documented [F1] |
| Height flicker while the font is still loading | Measure again on `document.fonts.ready` |
| Open issue about scroll jumps with `smooth` and dynamic height [F3] | Use `behavior: 'auto'` for the restore |

---

## 5. Verification

**Automatable on the host (`npm test`):**
- [ ] `virtual-list.test.tsx`: with `dynamicHeight`, 1-line and 3-line items do not overlap —
      guards decision 2.1.
- [ ] The bookshelf still renders at most 20 mounted items — guards the precedent.
- [ ] Restoring chapter 1,800 puts item 1,800 at the top — guards pitfall 1 [F1].

**Performance (protocol from `performance-measurement.md`):**
- [ ] Open the 2,400-chapter list, `hyperfine --warmup 3 --runs 10` over the mount test:
      median ≤ 50 ms (unmeasured today — the current value is the first step).
- [ ] 5 s scroll trace with CPU 4×: zero long tasks > 50 ms.

---

## 6. Risks

1. **The gain depends on the real size of the books.** Below ~200 chapters virtualization changes
   nothing noticeable; the effort only pays off in the reference catalog.
2. **Changing a shared component affects the bookshelf.** Mitigated by the order of the plan.

---

## 7. Files touched

| File | Change |
|---|---|
| `src/shared/virtual-list.tsx` | `dynamicHeight` option |
| `src/shared/virtual-list.test.tsx` | 2 new tests |
| `src/reader/ChapterList.tsx` | migrates to `VirtualList`; `key` by `chapter.id` |
| `src/reader/ChapterList.test.tsx` | **new** — position restore |

---

## 8. Sources consulted

| # | Source | Type | Version | Consulted on | Supports |
|---|---|---|---|---|---|
| F1 | [TanStack Virtual — Virtualizer API](https://tanstack.com/virtual/latest/docs/api/virtualizer) | Official doc | 3.10.8 | 2026-09-23 | 2.1, 2.2, step 3, pitfall 1 |
| F2 | `TanStack/virtual` — `examples/react/dynamic` | Maintainer example | 3.10.8 | 2026-09-23 | 2.1, step 1 |
| F3 | `TanStack/virtual` — issue about `smooth` with dynamic height | Issue | 3.x | 2026-09-23 | Pitfall 3 |

---

> No item in this report was executed. The whole analysis comes from reading the code on branch
> `main` (commit `a1b2c3d`) and from the sources in section 8; the baseline measurement is
> pending in section 5.
