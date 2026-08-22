# Rust

## Layout
- Unit tests in the same file: `#[cfg(test)] mod tests { use super::*; }` — they may access private items.
- Integration tests in `tests/`; they see only the public API. Use them to prove the crate's contract.

## Rules
- `#[should_panic(expected = "...")]` must always carry `expected`.
- For fallible code, return `Result<(), Box<dyn Error>>` from the test and use `?` instead of unwrapping.
- `assert_eq!` with a message when the values alone are not self-explanatory.
- Property-based testing (`proptest`) for parsers, encoders, and anything with algebraic invariants (round-trip, idempotence).
- `#[tokio::test]` for async; assert on the awaited value, not on the future.

## Avoid
- `unwrap()` in test bodies — it hides which step failed. Use `expect("clear reason")`.
- Testing `Debug`/`Display` output as a proxy for internal state.
