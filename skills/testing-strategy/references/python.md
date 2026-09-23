# Python

## Runner
`pytest`. Do not use `unittest` for new tests unless the project already standardises on it.

## Rules
- `@pytest.mark.parametrize` for table-driven cases — one test function, many rows. Give rows `ids=` so failures name the case.
- Fixtures for setup; prefer function scope. Widen to `module`/`session` scope only for genuinely expensive resources, and only when the fixture is immutable (or rolls back per test — see Performance).
- `with pytest.raises(ValueError, match="daily limit"):` — always assert the message or type, never a bare `raises(Exception)`.
- An injected clock, or `time-machine` / `freezegun`, for time. `monkeypatch` for environment and attributes.
- `tmp_path` for filesystem work, never a hardcoded `/tmp` path.
- **Hypothesis** (`@given(...)`) for invariants: round-trips, parsers, anything with a "for all inputs" rule. Keep its example database in `.hypothesis/` so found counterexamples replay instantly.
- `src/` layout with `--import-mode=importlib` avoids `sys.path` collisions between test modules.

## Avoid
- `assert result` on its own — assert the actual value.
- Mocking with `unittest.mock.patch` on deep import paths; patch where the name is *looked up*, not where it is defined.
- Real network calls. Use `responses` / `respx`, or a container for integration level.
- `time.sleep` to wait for async work — poll the condition with a timeout.

## Performance
- Measure: `pytest --durations=20 --durations-min=0.5`. Fix the top entries first.
- Edit loop: `pytest --lf` (last failed), `--ff` (failed first), `--sw` (stop at first failure, resume there next run).
- Parallel: `pytest -n auto` (pytest-xdist). Pick the distribution mode:
  - `--dist load` (default) for uniform, independent tests.
  - `--dist loadscope` when a module- or class-scoped fixture is expensive: it keeps each module/class on one worker, so the fixture is not rebuilt on every worker.
  - `--dist worksteal` when durations are very uneven.
  - `@pytest.mark.xdist_group` with `--dist loadgroup` for tests that must share one worker.
- Session fixtures run once **per xdist worker**. For one-per-run resources (a container), coordinate with a file lock or start the resource outside pytest.
- Worker-scoped DB isolation: derive the database or schema name from `os.environ.get("PYTEST_XDIST_WORKER", "gw0")`.
- DB-heavy suites: session-scoped connection + a function-scoped fixture that opens a transaction and rolls it back (see `references/performance.md` §3).
- Separate slow tests with a marker (`@pytest.mark.slow`), deselected in the edit loop with `-m "not slow"`.
- Order-coupling hunt: `pytest-randomly` shuffles order and reseeds `random` per test; reproduce a failure with the printed seed: `pytest --randomly-seed=N` (or `--randomly-seed=last`).
- `tmp_path_retention_policy = "failed"` keeps disk use down on long runs.
