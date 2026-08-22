# Go

## Rules
- **Table-driven tests** are the default idiom:
  ```go
  tests := []struct{ name string; in Input; want Output; wantErr error }{...}
  for _, tt := range tests {
      t.Run(tt.name, func(t *testing.T) { ... })
  }
  ```
- `t.Run` subtests for every row, so failures name the case.
- `t.Parallel()` when tests share no state — but capture the loop variable in Go versions before 1.22.
- `t.Cleanup()` instead of defer for teardown that must survive helper functions.
- `t.Helper()` in every assertion helper so failures report the caller's line.
- `errors.Is` / `errors.As` for error assertions, never string comparison.
- Accept interfaces in production code so tests can substitute fakes without a mocking framework.

## Avoid
- Heavy mocking libraries. Hand-written fakes are idiomatic and clearer.
- `httptest.NewServer` when a direct handler call would do.
