# JavaScript / TypeScript

## Runner
- Prefer **Vitest** for new projects (ESM native, fast, Jest-compatible API). Use **Jest** only when the project already uses it.
- Match the project's existing runner. Never introduce a second one.

## Rules
- `test.each` / `it.each` for table-driven cases instead of copy-pasted blocks.
- Fake timers (`vi.useFakeTimers()`) for anything time-dependent; always restore in cleanup. They do not fake `process.nextTick` or `queueMicrotask` unless listed in `toFake`.
- `await expect(fn()).rejects.toThrow(SpecificError)` — assert the error type, not just that it rejected.
- Wait on a condition, never a delay: `expect.poll(() => read())` or `vi.waitFor(...)` instead of `setTimeout`.
- **Mock hygiene** — no single flag does it all:
  - `restoreMocks: true` restores only spies created with `vi.spyOn` / `jest.spyOn`.
  - Use `clearMocks` (call history) or `mockReset` (history + implementation) for `vi.fn()` / `jest.fn()`.
  - Do not use `mockReset` with `test.concurrent`: it resets mocks that tests still running in the same file depend on.
- Type-level guarantees do not need runtime tests. Test what TypeScript cannot prove.
- Property-based tests with **fast-check** (`fc.assert(fc.property(...))`) for parsers, serializers, and invariants.

## Avoid
- `toMatchSnapshot()` on large objects. Assert the two or three fields that carry the business rule.
- `jest.mock()` / `vi.mock()` on the module under test.
- Testing React implementation details. Use Testing Library: query by role and accessible name, never by class name or test id when a role exists.

## Performance (Vitest v4)
- `pool: 'forks'` is the default (most compatible). `pool: 'threads'` is faster on large suites when no native module or `process.*` API gets in the way.
- `isolate: false` skips re-evaluating the module graph per file — a large win, but only when no test leaves module-level state behind. Enable it per project, not globally, if only some files are clean.
- Worker count is the top-level `maxWorkers` in v4 (`poolOptions.*.maxThreads/maxForks` were removed). `fileParallelism: false` runs files one at a time, for CPU-starved runners.
- `projects` replaces the deprecated `workspace`: split fast unit tests (node env) from DOM or integration tests so each gets its own pool and isolation.
- DOM environment: `happy-dom` is lighter than `jsdom`. Use a DOM environment only for files that need it, not globally.
- In tests, import from the source module, not from barrel files (`index.ts` re-exporting everything) — a barrel loads its whole module graph into every test file.
- Coverage: `provider: 'v8'` (default) is cheaper than istanbul. Collect it in CI, not in the edit loop.

## Performance (Jest)
- `--maxWorkers` defaults to cores − 1. On shared CI, set it explicitly (`--maxWorkers=2` or `50%`).
- `workerIdleMemoryLimit: '512MB'` recycles leaking workers; then find the leak.
- `--detectOpenHandles` forces serial runs — debugging only.

## End-to-end (Playwright)
- Web-first assertions (`await expect(locator).toBeVisible()`) — they auto-retry. Never `waitForTimeout`.
- One journey per spec file.
- **Authentication**: log in once in a **setup project** that saves `storageState` to a file, and make the browser projects depend on it (`dependencies: ['setup']`). Every worker reuses that file instead of logging in again. Give each worker its own account (indexed by `testInfo.parallelIndex`) only when tests change server-side state that other workers would see. Never commit the state file.
- `fullyParallel: true` parallelizes tests within a file and balances shards per test instead of per file.
- `retries: process.env.CI ? 2 : 0` with `trace: 'on-first-retry'` — tracing every run is expensive.
- In CI, install only the browsers the config uses (`npx playwright install --with-deps chromium`).
- Prefer seeding state through the API (`request` fixture) over clicking through the UI in every test.
