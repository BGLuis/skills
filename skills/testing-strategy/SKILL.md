---
name: testing-strategy
description: Writes new tests, audits existing test suites, and makes suites fast and cheap to run — each test must be able to fail when the business rule it guards changes, and the suite must get maximum signal from minimum CPU, memory, and CI time. Use when the user asks to write, add, or improve tests, asks what to test for a feature, reports a flaky or slow suite, wants tests to run faster or use fewer resources, asks whether coverage is meaningful, or asks for a review of an existing test file. Covers unit, integration, and end-to-end levels across JavaScript/TypeScript, Python, Go, and Rust. Do NOT use for writing the production code under test, for CI pipeline configuration (workflow YAML, runners, job matrices, caching) — this skill supplies the test-runner flags, not the pipeline — or for load and performance benchmarking of the application itself.
---

# Testing Strategy

Act as a senior engineer who treats the test suite as executable specification. A test exists to encode **why** a behaviour matters, not to restate what the code happens to do today. A suite is only useful if it is fast enough that people run it: every second and every worker it consumes must buy real signal.

## 0. Before writing anything

Read the code under test and its immediate callers. Identify:

- The **business rule** the code enforces (not its implementation steps).
- The **contract**: inputs, outputs, side effects, error paths.
- What is already covered. Never duplicate an existing assertion.

If the rule is not clear from the code, ask the user rather than inventing an intent. A test that guards an invented rule is worse than no test.

## 1. The falsifiability rule (non-negotiable)

For every test, ask: **"which realistic change to the business logic would make this fail?"**

If the answer is "none", delete or rewrite the test. This eliminates the common failure modes:

- **Tautologies**: mocking the thing under test, or asserting a literal you just hardcoded.
- **Mirror tests**: reimplementing the production algorithm inside the assertion.
- **Snapshot dumps**: a large snapshot nobody reviews; it fails on formatting, passes on real regressions.
- **Coverage padding**: calling a function without asserting anything meaningful about the result.

**Prove it mechanically when possible.** Mutation testing is the automated form of this rule: it changes the code and checks that some test fails. If the project already has a mutation tool (Stryker, mutmut, cargo-mutants), run it **only on the changed code** — full runs cost many times the suite's runtime. Every surviving mutant is a test to fix. Never install a mutation tool without asking.

## 2. What to test, in priority order

1. **Business rules and invariants** — the reason the code exists.
2. **Boundaries** — empty, one, many, max, off-by-one, unicode, zero, negative.
3. **Error paths** — assert the specific failure (type, message, code), never a bare "it throws".
4. **Concurrency and ordering**, where the code is genuinely concurrent.

For invariants that hold over a whole input space (round-trip, idempotence, ordering, "never negative"), prefer one **property-based test** (fast-check, Hypothesis, proptest) over dozens of hand-picked examples: less code, wider coverage, and the framework shrinks failures to a minimal case.

Do not test: language/framework behaviour, third-party libraries, private helpers reachable only through a public API (test them through it), or getters with no logic.

## 3. Test level

Guard each rule at the **cheapest level that can fail for it**. If a higher-level test catches a bug that no lower-level test caught, the missing lower-level test is the real fix.

- **Unit**: pure logic, branching, calculations. Fast, no I/O.
- **Integration**: the seam between your code and a real dependency (DB, HTTP, filesystem). Prefer a real dependency in a container over a mock — a mock encodes your *assumption* about the dependency, and assumptions drift.
- **End-to-end**: only for critical user journeys that lower levels structurally cannot cover. Expensive and flaky; keep the count small and deliberate.

Mock only what you cannot control: network calls to third parties, clocks, randomness, payment providers. Never mock the unit under test. Prefer a hand-written **fake** (an in-memory implementation of the interface) over a call-recording mock — fakes test outcomes, mocks test call sequences that break on every refactor.

## 4. Structure and naming

- Name by **behaviour and expectation**, not by method: `rejects a transfer that exceeds the daily limit`, never `test_transfer_2`.
- One logical behaviour per test. Multiple assertions are fine if they describe one behaviour.
- Arrange / Act / Assert, visually separated.
- Deterministic: inject clocks and seeds. Never `sleep`; wait on a condition.
- Isolated: any test must pass when run alone and in any order. Shared mutable state between tests is a defect.

## 5. Performance and resource budget

Maximum confidence per second of runtime and per worker. Apply in this order:

1. **Measure first.** Before changing any configuration, list the slowest tests and the slowest imports/fixtures with the runner's own timing report. Never optimize blind; most suites are slow because of a handful of tests.
2. **Budget by size**, not by label. *Small*: one process, no network, no disk, no `sleep`, no subprocess — milliseconds each. *Medium*: localhost only (container DB, local server). *Large*: external systems. A "unit" test that touches I/O is medium: tag it and make it skippable in the fast loop.
3. **Pay expensive setup once.** Start one container per test run, not per file or per test. Apply migrations once. Isolate each test with a **transaction rolled back in teardown** or a database cloned from a template — never drop-and-recreate. Run test databases on tmpfs with durability off (`fsync=off`). Container *reuse across runs* is for local development only, never CI.
4. **Parallelize only independent tests.** Parallelism multiplies throughput only when tests share no state; otherwise it multiplies flakiness. Cap workers at the CPUs actually available (shared CI runners have 2–4). Shard across machines only when one machine is saturated, and merge the reports.
5. **Run the least that proves the change.** In the edit loop, run changed-only or last-failed-first. Run the full suite as the gate before merge, not on every keystroke.
6. **Retries are diagnosis, not a fix.** A test that passes on retry is flaky — a defect. Record traces only on the first retry; quarantine flaky tests with a deadline to fix them, never silently.

Commands and configuration per stack are in `references/performance.md`; stack-specific traps are in each stack file below.

## 6. Auditing an existing suite

When reviewing rather than writing, report findings in this order:

1. Tests that cannot fail (apply §1) — the most damaging, since they buy false confidence.
2. Missing coverage of business rules and error paths.
3. Flakiness sources: real clocks, real network, ordering dependence, shared fixtures.
4. Slowness and waste, **with numbers**: total runtime, the top slow tests and what they spend time on, and the estimated saving of each fix (see §5).

Quantify where possible ("14 of 31 tests assert only that no exception was thrown"; "6 tests account for 71% of the 48 s runtime"). End with the single highest-value fix. See `examples/audit-report.md` for the expected shape.

## 7. Stack-specific rules

Read the matching file before writing tests:

- `references/javascript.md` — Vitest, Jest, Playwright
- `references/python.md` — pytest
- `references/go.md` — table-driven tests, `testing`
- `references/rust.md` — `#[test]`, integration layout, nextest
- `references/performance.md` — measuring, parallelism, changed-only runs, cheap databases, mutation testing (read whenever speed or resources are in scope)

For a worked optimization of a slow suite, see `examples/slow-suite-before-after.md`.

## 8. Report

After writing tests, state: what business rules are now guarded, what is deliberately left uncovered and why, and the command to run them. After optimizing a suite, state the runtime (and workers/memory when relevant) **before and after, as measured** — if you could not measure, say so rather than estimating silently. Never claim a suite passes without having run it — if you could not run it, say so explicitly.
