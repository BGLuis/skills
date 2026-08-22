# JavaScript / TypeScript

## Runner
- Prefer **Vitest** for new projects (ESM native, fast, Jest-compatible API). Use **Jest** only when the project already uses it.
- Match the project's existing runner. Never introduce a second one.

## Rules
- `test.each` / `it.each` for table-driven cases instead of copy-pasted blocks.
- Fake timers (`vi.useFakeTimers()`) for anything time-dependent; always restore in cleanup.
- `await expect(fn()).rejects.toThrow(SpecificError)` — assert the error type, not just that it rejected.
- Reset mocks between tests (`restoreMocks: true` in config) so state never leaks.
- Type-level guarantees do not need runtime tests. Test what TypeScript cannot prove.

## Avoid
- `toMatchSnapshot()` on large objects. Assert the two or three fields that carry the business rule.
- `jest.mock()` on the module under test.
- Testing React implementation details. Use Testing Library: query by role and accessible name, never by class name or test id when a role exists.

## End-to-end (Playwright)
- Web-first assertions (`await expect(locator).toBeVisible()`) — they auto-retry. Never `waitForTimeout`.
- One journey per spec file. Independent auth state per worker.
