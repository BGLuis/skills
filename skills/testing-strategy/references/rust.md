# Rust

## Layout
- Unit tests in the same file: `#[cfg(test)] mod tests { use super::*; }` — they may access private items.
- Integration tests in `tests/`; they see only the public API. Use them to prove the crate's contract.
- Shared helpers for integration tests go in `tests/common/mod.rs`, not `tests/common.rs`, which Cargo would compile as a test crate of its own.

## Rules
- `#[should_panic(expected = "...")]` must always carry `expected`.
- For fallible code, return `Result<(), Box<dyn Error>>` from the test and use `?` instead of unwrapping.
- `assert_eq!` with a message when the values alone are not self-explanatory.
- Property-based testing (`proptest`) for parsers, encoders, and anything with algebraic invariants (round-trip, idempotence). Commit the `proptest-regressions/` files so shrunk failures replay first.
- `#[tokio::test]` for async; assert on the awaited value, not on the future.
- Time-dependent async code: `#[tokio::test(start_paused = true)]` (needs tokio's `test-util` feature). Paused time auto-advances when the runtime is idle, so a 30 s timeout tests instantly. It only works on the default current-thread runtime, not `flavor = "multi_thread"`.
- Snapshots only through `insta`, kept small (a redacted struct, not a whole response), reviewed with `cargo insta review`. Never accept snapshots in bulk without reading them.

## Avoid
- `unwrap()` in test bodies — it hides which step failed. Use `expect("clear reason")`.
- Testing `Debug`/`Display` output as a proxy for internal state.
- `std::thread::sleep` in tests — use channels, barriers, or paused tokio time.

## Performance
- Run with **cargo-nextest** (`cargo nextest run`) when available. Each test runs in its own process, so a panic or leaked global cannot affect another test, and slow tests are scheduled across binaries instead of blocking one binary. Doctests still need `cargo test --doc`.
- Heavy tests (a container, lots of memory): declare `threads-required` in `.config/nextest.toml` so they take more than one slot. Tests that must not overlap go in a `test-group` with `max-threads = 1`.
- CI sharding: `cargo nextest run --partition count:1/3`, with an archive (`cargo nextest archive`) to build once and run on many machines.
- Flaky detection: nextest `retries` reports tests that passed on retry as FLAKY — treat that list as defects (see `references/performance.md` §5).
- Compile time dominates many Rust test runs: one integration-test crate that declares its tests as modules (`tests/it/main.rs` + `mod foo;`) links once, instead of one binary per file.
- Mutation testing: `cargo mutants --in-diff pr.diff` on PRs only.
