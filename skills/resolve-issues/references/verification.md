# Verification — from acceptance criteria to checks, and the report

The issue is the contract: its acceptance criteria say when the work is done. Each one becomes a
check before any code is written, and each check runs before the issue is called resolved.

## Contents

- The criteria table
- Rules for a criterion
- Reproducing a defect
- What cannot be verified here
- Report

## The criteria table

Build it in step 5 of the skill, show it at the plan gate when there is one, and fill the result
column in step 8:

```markdown
| # | Criterion (from the issue) | Check | Result |
|---|---|---|---|
| 1 | Peak RSS ≤ 100 MB on a month's export | `VmHWM` over `curl …/export?month=2026-08`, n = 10, median — baseline 1.12 GB | ✅ 84 MB |
| 2 | A query error ends the CSV without the end-of-file marker | new test `export.stream.test.ts` › "truncated on error" | ✅ |
| 3 | `npm test` and `npm run lint` pass | the two commands | ✅ |
| 4 | Works on the production database | — | not verified: no access from here |
```

The *Criterion* column quotes the issue; a criterion you derived says so ("derived: …").

## Rules for a criterion

A criterion the issue gives is checked as written. A criterion you derive — the issue had none,
or had a vague one — follows these rules:

1. **It names its check**: the command, the test, the assertion, or the trace observation that
   proves it. "Restoring chapter 1,800 puts it at the top" becomes "… asserted on `scrollTop`
   (`npm test -- restore`)".
2. **No vague term without a threshold.** *Faster*, *better*, *cleaner*, *works as expected*
   (*mais rápido*, *melhor*, *funciona corretamente*) mean nothing until a number says how much.
3. **A threshold has a baseline**: today's value, measured with the same protocol before the
   change, or `[modeled]` with the model it came from.
4. **Every scope item is covered.** Each step of the issue's scope or fix is closed by at least one
   criterion; a step with none is either not needed or not verifiable — say which.
5. **A destructive or one-way change has a negative criterion**: what must still hold after it —
   the rows a migration keeps, the request still refused, the rollback that restores the previous
   state.

## Reproducing a defect

For a bug, the first check is the reproduction: a test or a command that fails **before** the fix,
for the reason the issue gives. Run it and read the failure: a test that fails for another reason
(a typo, a missing fixture) proves nothing. After the fix the same check passes, and it stays in
the suite as the regression test. When the defect cannot be triggered here (it needs hardware,
production data, a race), say so, and make the closest check that can run: a unit test of the
faulty function with the input that triggers it.

## What cannot be verified here

A criterion whose check cannot run in this environment is **not verified** — not met, not "should
work". Say what would verify it and who can run it: a test on a device, a query on production, a
manual check of a screen. Never mark the issue's checklist items as done on GitHub; the person who
merges does that.

## Report

One block per work unit, in the language of the conversation:

```markdown
### perf/140-export-memory — epic #140: #141, #142

- Worktree: `../shop-api-140` · base `origin/main` at `9f3e21a`
- Commits: `a1b2c3d fix(export): join the customer name in the main query (#141)` · `d4e5f6a perf(export): stream rows instead of loading the month (#142)`

| # | Criterion | Check | Result |
|---|---|---|---|
| … | … | … | … |

- Sources: F1 `pg-query-stream` 4.7.0 (official doc); precedent `src/api/audit/stream.ts:15-48`
- ⚠️ Divergence: the issue suggested `res.write` per row; the docs recommend `pipeline` for backpressure [F1]
- Related, not handled: #150 (same module, different cause)
- Follow-ups: the audit export has the same N+1 (`src/api/audit/handler.ts:30`) — file with technical-issues?
- Not verified: criterion 4 (production)
- Left for you: review, push, pull request
```
