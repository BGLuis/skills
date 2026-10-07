<!-- Illustrative example: the mode B audit in technical-report's examples/performance-audit.md,
     delivered as issues. Paths, versions, and numbers are fictional. -->

**Branch:** `main` · **Base commit:** `9f3e21a` · **Scope:** `src/api/export/*`

The `GET /export` route generates the CSV for a month of orders. With 180 thousand rows, each
export holds ~1.1 GB of memory and a pool connection for 9 s. Memory, not time, is the limiting
resource: two simultaneous exports already bring down the 2 GB container (`deploy/api.yaml:31`).

**Verdict:** correct in its data, but the memory cost grows linearly with the month and limits
the route to one export at a time.

| Order | Key | Sub-issue | Severity | Effort |
|---|---|---|---|---|
| 1 | P-02 | N+1 query for the customer name | High | XS |
| 2 | P-01 | Stream rows instead of loading the whole result | Critical | S |

> Ordered by (user impact × reach) ÷ effort. Apply one at a time and measure between them with
> the same protocol: P-02 changes the time, P-01 changes the memory.

### Limits of this analysis

Measured locally: 8-core laptop, Node 22.4, production build, local Postgres 16 with the
180-thousand-order test database · `hyperfine --warmup 2 --runs 10` · hot state · peak RSS from
`/proc/<pid>/status` · turbo boost not controlled. No measurement in production nor with real
concurrency.

### Risks

1. **No measurement was made with concurrency.** Before allowing simultaneous exports, run 5
   parallel requests and confirm the total peak ≤ 500 MB.
2. **The stream changes an error in the middle of the export.** Today it fails before the first
   byte; with a stream the client receives a truncated CSV. It needs an end-of-file marker.

**Not verified:** nothing ran in production or under concurrency; the 2 GB limit comes from the
deploy manifest, not from a load test.
