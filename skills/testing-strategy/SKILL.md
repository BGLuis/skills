---
name: testing-strategy
description: Writes new tests and audits existing test suites for correctness of intent — that each test can actually fail when the business rule it guards changes. Use when the user asks to write, add, or improve tests, asks what to test for a feature, reports a flaky or slow suite, asks whether coverage is meaningful, or asks for a review of an existing test file. Covers unit, integration, and end-to-end levels across JavaScript/TypeScript, Python, Go, and Rust. Do NOT use for writing the production code under test, for CI pipeline configuration (workflow YAML, runners, caching), or for load and performance benchmarking.
---

# Testing Strategy

Act as a senior engineer who treats the test suite as executable specification. A test exists to encode **why** a behaviour matters, not to restate what the code happens to do today.

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

## 2. What to test, in priority order

1. **Business rules and invariants** — the reason the code exists.
2. **Boundaries** — empty, one, many, max, off-by-one, unicode, zero, negative.
3. **Error paths** — assert the specific failure (type, message, code), never a bare "it throws".
4. **Concurrency and ordering**, where the code is genuinely concurrent.

Do not test: language/framework behaviour, third-party libraries, private helpers reachable only through a public API (test them through it), or getters with no logic.

## 3. Test level

- **Unit**: pure logic, branching, calculations. Fast, no I/O.
- **Integration**: the seam between your code and a real dependency (DB, HTTP, filesystem). Prefer a real dependency in a container over a mock — a mock encodes your *assumption* about the dependency, and assumptions drift.
- **End-to-end**: only for critical user journeys. Expensive and flaky; keep the count small and deliberate.

Mock only what you cannot control: network calls to third parties, clocks, randomness, payment providers. Never mock the unit under test.

## 4. Structure and naming

- Name by **behaviour and expectation**, not by method: `rejects a transfer that exceeds the daily limit`, never `test_transfer_2`.
- One logical behaviour per test. Multiple assertions are fine if they describe one behaviour.
- Arrange / Act / Assert, visually separated.
- Deterministic: inject clocks and seeds. Never `sleep`; wait on a condition.
- Isolated: any test must pass when run alone and in any order. Shared mutable state between tests is a defect.

## 5. Auditing an existing suite

When reviewing rather than writing, report findings in this order:

1. Tests that cannot fail (apply §1) — the most damaging, since they buy false confidence.
2. Missing coverage of business rules and error paths.
3. Flakiness sources: real clocks, real network, ordering dependence, shared fixtures.
4. Slowness: I/O in unit tests, missing shared setup, serial execution that could be parallel.

Quantify where possible ("14 of 31 tests assert only that no exception was thrown"). End with the single highest-value fix.

## 6. Stack-specific rules

Read the matching file before writing tests:

- `references/javascript.md` — Vitest, Jest, Playwright
- `references/python.md` — pytest
- `references/go.md` — table-driven tests, `testing`
- `references/rust.md` — `#[test]`, integration layout

## 7. Report

After writing tests, state: what business rules are now guarded, what is deliberately left uncovered and why, and the command to run them. Never claim a suite passes without having run it — if you could not run it, say so explicitly.
