# Example: making a slow integration suite cheap

pytest + Postgres + Testcontainers. The same pattern applies to Vitest (`globalSetup` + `provide`/`inject`), Go (`TestMain`), and Rust (a `OnceLock` container).

## Before — anti-patterns to never reproduce

```python
# conftest.py
@pytest.fixture                                  # function scope: one container per test
def db():
    with PostgresContainer("postgres:17") as pg:     # 2–4 s boot, every test
        engine = create_engine(pg.get_connection_url())
        run_migrations(engine)                   # full migration, every test
        yield engine

# test_orders.py
def test_order_expires(db):
    order = create_order(db, ttl_seconds=1)
    time.sleep(2)                                # real time
    assert get_order(db, order.id).status == "expired"
```

Measured with `pytest --durations=10`: 40 tests, 96 s, 1 worker. Cannot be parallelized — would start 40 containers.

## After

```python
# conftest.py
@pytest.fixture(scope="session")
def engine():
    pg = PostgresContainer("postgres:17").with_command(
        "postgres -c fsync=off -c synchronous_commit=off -c full_page_writes=off"
    ).with_kwargs(tmpfs={"/var/lib/postgresql/data": "rw"})
    with pg:                                     # one container per worker
        engine = create_engine(pg.get_connection_url())
        run_migrations(engine)                   # once
        yield engine

@pytest.fixture
def db(engine):
    with engine.connect() as conn:
        tx = conn.begin()
        yield conn                               # the test's writes live in tx
        tx.rollback()                            # isolation without recreating anything

@pytest.fixture
def clock():
    return FakeClock(datetime(2026, 1, 1, tzinfo=UTC))

# test_orders.py
def test_order_expires_after_its_ttl(db, clock):
    order = create_order(db, ttl_seconds=60, clock=clock)
    clock.advance(seconds=61)
    assert get_order(db, order.id, clock=clock).status == "expired"
```

Run: `pytest -n auto --dist loadscope`.

## Why each change pays

| Change | Cost removed |
|---|---|
| Session-scoped container | N container boots → 1 per worker |
| Migrations once | N migration runs → 1 per worker |
| Transaction rollback | Isolation without truncate/recreate. Requires the code under test to accept a connection and not commit on its own; otherwise clone a template DB per worker |
| tmpfs + `fsync=off` | Disk flushes on every commit (test data is disposable) |
| Injected clock | Real `sleep`, plus flakiness near time boundaries |
| `-n auto --dist loadscope` | Serial execution. Safe only now that tests share no mutable state |

Report shape (illustrative numbers): "40 tests: 96 s → 7 s on 4 workers (measured, `--durations` attached). Peak memory: 1 Postgres per worker instead of 1 per test." If a number was not measured, say so.
