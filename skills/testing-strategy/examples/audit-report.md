# Example: audit report

The expected shape of an audit (§6). The numbers are illustrative; in a real audit every number comes from reading the files or running the suite.

---

**Scope:** `tests/billing/` — 31 tests, 4 files. Ran `pytest tests/billing --durations=10`: 31 passed in 48.2 s on 1 worker.

### 1. Tests that cannot fail (15 of 31)
- `test_invoice.py::test_create_invoice` and 13 others only call the function and assert `result is not None`. Removing the discount logic entirely would still pass them. → Assert `total`, `tax`, and `discount_applied` against values derived from the rule, not from the output.
- `test_tax.py::test_vat` patches `compute_vat` — the function under test — and asserts the patched return value. A tautology. → Delete it and replace it with a parametrized table of (country, amount, expected VAT).

### 2. Missing business-rule coverage
- The rule "credit notes can never exceed the original invoice" (`billing/credit.py:42`) has no test. Its error path (`CreditExceedsInvoice`) is never asserted.
- The rounding boundary (0.005) is untested for both HALF_UP and bankers' rounding.

### 3. Flakiness sources
- `test_due_date.py` uses `datetime.now()` directly: 2 tests fail when run between 23:00 and 00:00 UTC. → Inject a clock.
- `test_webhooks.py` calls `time.sleep(2)` to wait for a background thread. → Poll the condition with a timeout.

### 4. Slowness and waste
| Cause | Tests | Time | Fix | Estimated saving |
|---|---|---|---|---|
| New Postgres container per test (function-scoped fixture) | 9 | 29.7 s (62%) | Session container + per-test transaction rollback | ~27 s |
| `time.sleep(2)` in webhook tests | 4 | 8.0 s (17%) | Wait on the condition | ~7.5 s |
| Serial run of independent tests | all | — | `-n auto --dist loadscope` after the two fixes above | ~2× on 4 cores |

The unit tests in `test_tax.py` and `test_invoice.py` take 0.3 s together. The suite is slow because of 13 tests, not 31.

### Highest-value fix
Replace the per-test container with a session-scoped container and a rolled-back transaction per test (see `examples/slow-suite-before-after.md`). One fixture change removes ~60% of the runtime, and it is a prerequisite for safe parallelism.
