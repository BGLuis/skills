# Technical Analysis — `src/api/export`

<!-- Illustrative mode B example. Paths, versions, and numbers are fictional; in a real report
     each one comes from reading the repository, from measurement in this session, or from a
     cited source. -->

**Date:** 2026-09-23 · **Branch:** `main` · **Base commit:** `9f3e21a`
**Scope:** `src/api/export/*` (CSV report export)

---

## 1. Executive summary

The `GET /export` route generates the CSV for a month of orders. With 180 thousand rows, each
export holds ~1.1 GB of memory and a pool connection for 9 s. Time is not the main problem:
memory is — two simultaneous exports already bring down the 2 GB container.

| # | Problem | Reach | Severity |
|---|---|---|---|
| P-01 | Whole result loaded into memory before writing | Every export | Critical |
| P-02 | N+1 query for the customer name | Every export | High |

**Verdict:** correct in its data, but the memory cost grows linearly with the month and limits
the route to one export at a time.

---

## 2. Methodology and limits

### 2.1 What was done

Reading of `src/api/export/*` and local measurement with the protocol below.

**Protocol** (`performance-measurement.md` §2): 8-core laptop, Node 22.4, production build, local
Postgres 16 with the 180-thousand-order test database · `hyperfine --warmup 2 --runs 10` over a
`curl` of the route · hot state (Postgres buffer warmed by the warm-up runs) · memory from peak
RSS in `/proc/<pid>/status` · uncontrolled noise: turbo boost on.

### 2.2 What was NOT done — limits of this analysis

> No measurement in production nor with real concurrency. The 2 GB limit comes from the deploy
> manifest (`deploy/api.yaml:31`), not from a load test.

| Metric | "Good" threshold | Source |
|---|---|---|
| Peak memory per export | ≤ 100 MB | team budget (`docs/SLO.md:12`) |
| Pool connections per request | 1, released at the end | `src/db/pool.ts:8` (`max: 10`) |

---

## 3. Measured evidence

### 3.1 Memory, not CPU, is the limiting resource

| Metric (n = 10) | Median | p95 |
|---|---|---|
| Total time | 9.2 s | 9.8 s |
| Peak RSS | 1.12 GB | 1.15 GB |
| Process CPU | 1.4 cores | — |

During the export CPU stays at ~1.4 of 8 cores; RSS grows until the end and only drops after
sending. Doubling the CPU does not change the result — what limits is the container's memory.

### 3.2 Negative check: there is no leak between requests

After 10 exports in a row RSS returns to ~140 MB. The memory is peak, not accumulated — the leak
hypothesis is refuted and is recorded here so it is not raised again.

---

## 4. Performance findings

### P-01 · Whole result loaded into memory before writing — **Critical**

`src/api/export/handler.ts:22-40`

```ts
const rows = await db.query(sql, [month]); // line 24 — 180 thousand objects
res.send(toCsv(rows.rows));                 // line 39 — ~95 MB string
```

`query` materializes every row as a JS object and `toCsv` builds a single string; both coexist at
the peak. The cost grows linearly with the exported month.

**Reproduction:** with the test database, `curl -o /dev/null localhost:3000/export?month=2026-08`
while watching `VmHWM` in `/proc/<pid>/status`; the peak goes past 1 GB.

**Fix:** switch to a cursor + stream (`pg-query-stream` [F1]) piped into a CSV transform, as the
audit export already does in `src/api/audit/stream.ts:15-48`.
**Acceptance criteria:** peak RSS ≤ 100 MB on the same reproduction, n = 10, median.

---

### P-02 · N+1 query for the customer name — **High**

`src/api/export/handler.ts:31-35`

Each row calls `getCustomerName(id)`, one query per order: 180 thousand round-trips hold the pool
connection for the 9 s of the export.

**Reproduction:** turn on `log_statement = 'all'` in the local Postgres and export a month; the
log shows one `SELECT name FROM customers` query per order.

**Fix:** `JOIN` with `customers` in the main query.
**Acceptance criteria:** the same log shows **one** query per export.

---

## 5. Usability and accessibility findings

Out of scope for this analysis — the route has no interface.

---

## 6. Prioritized backlog

> Ordered by (user impact × reach) ÷ effort.

| Pri | Item | Effort | Reach | Type |
|---|---|---|---|---|
| 1 | **P-02** — `JOIN` instead of the N+1 | XS | Every export | Perf |
| 2 | **P-01** — cursor + stream | S | Every export | Perf/Architecture |

Apply one at a time and measure again between them with the protocol of section 2 — P-02 changes
the time, P-01 changes the memory, and measuring both together hides which one solved what.

---

## 7. Risks and what remains to verify

1. **No measurement was made with concurrency.** Before allowing simultaneous exports, run 5
   parallel requests and confirm the total peak ≤ 500 MB.
2. **The stream changes an error in the middle of the export.** Today it fails before sending the
   first byte; with a stream the client receives a truncated CSV. It needs an end-of-file marker.

---

## 8. Sources consulted

| # | Source | Type | Version | Consulted on | Supports |
|---|---|---|---|---|---|
| F1 | [`pg-query-stream` — README](https://github.com/brianc/node-postgres/tree/master/packages/pg-query-stream) | Official doc | 4.7.0 | 2026-09-23 | Fix for P-01 |

---

> Nothing was measured in production. The numbers come from 10 local runs on branch `main`
> (commit `9f3e21a`), with the protocol of section 2; the concurrency test is pending in
> section 7.
