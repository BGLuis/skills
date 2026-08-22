# Python

## Runner
`pytest`. Do not use `unittest` for new tests unless the project already standardises on it.

## Rules
- `@pytest.mark.parametrize` for table-driven cases — one test function, many rows.
- Fixtures for setup; prefer function scope. Widen to `module`/`session` scope only for genuinely expensive resources, and only when the fixture is immutable.
- `with pytest.raises(ValueError, match="daily limit"):` — always assert the message or type, never a bare `raises(Exception)`.
- `freezegun` or an injected clock for time. `monkeypatch` for environment and attributes.
- `tmp_path` for filesystem work, never a hardcoded `/tmp` path.

## Avoid
- `assert result` on its own — assert the actual value.
- Mocking with `unittest.mock.patch` on deep import paths; patch where the name is *looked up*, not where it is defined.
- Real network calls. Use `responses` / `respx`, or a container for integration level.
