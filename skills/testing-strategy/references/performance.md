# Performance and resource playbook

Goal: the most confidence per second of runtime and per worker. Always measure before and after; report both numbers.

## 1. Commands per stack

| Need | Vitest | Jest | Playwright | pytest | Go | Rust (nextest) |
|---|---|---|---|---|---|---|
| Find slow parts | summary line splits `transform / setup / import / tests / environment`; `--experimental.importDurations.print` lists the slowest imports | per-file time in default reporter; `--verbose` per test | HTML report durations; `--reporter=list` | `--durations=20 --durations-min=0.5` | `-v` + `-json` (e.g. through gotestsum) | per-test time printed by default; slow-test warnings via `slow-timeout` |
| Parallel workers | `maxWorkers` (top-level in v4) | `--maxWorkers=50%` | `workers`, `fullyParallel: true` | `-n auto` (pytest-xdist) | `-p` (packages), `-parallel` (tests with `t.Parallel`) | `--test-threads` |
| Only what changed | `--changed [ref]` | `--onlyChanged`, `--changedSince=origin/main` | `--only-changed [ref]` | — (use `--lf`) | package-level result cache (free, automatic) | — |
| Failures first | — | — | `--last-failed` | `--lf`, `--ff`, `--sw` | — | fail-fast by default; `--no-fail-fast` to see all |
| Shard across machines | `--shard=i/n --reporter=blob`, then `--merge-reports` | `--shard=i/n` | `--shard=i/n` + blob reporter, then `npx playwright merge-reports` | split by marker/path, or pytest-split | split package list | `--partition count:i/n` (or `hash:i/n`) |
| Random order (find hidden coupling) | `sequence.shuffle` | `--randomize --seed=N` | — | pytest-randomly (plugin) | `-shuffle=on` | — |

Interpretation hints:
- Vitest: when `import`/`transform` dominate `tests`, the cost is the module graph (barrel files, heavy deps loaded per file), not the assertions.
- Go: results are cached only in package-list mode (`go test ./...` or `go test .`, not bare `go test`) and only with cacheable flags such as `-run`, `-short`, `-v`, `-parallel`, `-timeout`. `-count=1` is the idiomatic way to force a fresh run — don't add it to the local loop; the cache is free speed.
- Jest: `--detectOpenHandles` forces serial execution. Debugging only, never in CI.

## 2. Worker sizing

- Default worker counts assume a dedicated machine. Shared CI runners usually have 2–4 vCPUs: cap workers at the real CPU count. Oversubscribing only adds context switching and memory pressure.
- More workers only help when tests are independent **and** the bottleneck is CPU. If one shared DB is the bottleneck, more workers just queue on it.
- Uneven durations: pytest-xdist `--dist worksteal` rebalances. Tests sharing an expensive module/class fixture: `--dist loadscope`, so each module/class stays on one worker and its fixture is not rebuilt on every worker.
- Worker memory leaks in long runs: Jest `workerIdleMemoryLimit` recycles workers; fix the leak afterwards.

## 3. Databases and containers

The biggest wins in integration suites usually come from setup cost, not from assertions.

- **One container per run.** Start it in a session-scoped fixture / global setup (Vitest: `globalSetup` + `provide`/`inject`; Jest: `globalSetup` passing the URL via an env var; pytest: `scope="session"`; Go: `TestMain`). Never one per test or per file.
- **Migrate once**, then isolate each test by:
  - **transaction + rollback** in teardown — fastest; not usable when the code under test commits or opens its own transactions, or when the test needs data visible to another connection; or
  - **template database**: `CREATE DATABASE test_N TEMPLATE app_template` per worker or per test — a cheap copy of a migrated schema.
  - Truncating tables is the fallback. Dropping and recreating the schema per test is never acceptable.
- **Durability off** (test data is disposable): Postgres on `tmpfs`, with `-c fsync=off -c synchronous_commit=off -c full_page_writes=off`.
- **Wait strategies**, never `sleep`: wait for the log line or port the container itself reports (Testcontainers `wait.For…` / `wait_for_logs` / `Wait.forLogMessage`).
- **Reuse across runs** (`withReuse`, `testcontainers.reuse.enable`) speeds up local development. Disable it in CI (`TESTCONTAINERS_REUSE_ENABLE=false`), where every run must start clean.
- Per-worker isolation for parallel runs: one schema or database per worker, keyed by the worker id (`PYTEST_XDIST_WORKER`, `VITEST_POOL_ID`, `JEST_WORKER_ID`, Playwright `testInfo.parallelIndex`).

## 4. Mutation testing, cheaply

Mutation runs cost many times the suite's runtime. Scope them:

- StrykerJS: `--incremental` reuses the previous report and only re-tests mutants in changed code or tests.
- mutmut: re-tests only functions changed since its last run; the run is resumable.
- cargo-mutants: `git diff origin/main > pr.diff && cargo mutants --in-diff pr.diff`.
- Go: no mature incremental tool — pass only the changed packages.

Run on the diff in PRs and on the whole codebase on a schedule. Treat each surviving mutant as a missing or weak assertion.

## 5. Flakiness budget

- A test that passes on retry is a defect, not a success. Keep `retries` at 0 locally; allow 1–2 in CI only together with trace capture on the first retry, and list the tests that needed a retry.
- Before admitting a new test that touches concurrency or time, run it repeatedly (`--repeat-each`, `-count=50`, pytest-repeat) to prove it is stable.
- Quarantine with a named owner and a deadline. Never delete or skip it silently.

## Sources
- vitest.dev/guide/improving-performance, vitest.dev/guide/profiling-test-performance
- jestjs.io/docs/cli, jestjs.io/docs/configuration
- playwright.dev/docs/test-parallel, /test-sharding, /test-retries
- pytest-xdist.readthedocs.io/en/stable/distribution.html, docs.pytest.org/en/stable/how-to/cache.html
- `go help testflag`, go.dev/blog/synctest
- nexte.st/docs/running, nexte.st/docs/design/why-process-per-test
- testcontainers.com/guides, node.testcontainers.org
- stryker-mutator.io/docs/stryker-js/incremental, mutants.rs/in-diff.html
- testing.googleblog.com/2010/12/test-sizes.html, martinfowler.com/articles/nonDeterminism.html
