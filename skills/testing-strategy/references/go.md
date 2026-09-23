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
- `t.Parallel()` when tests share no state. Capture the loop variable (`tt := tt`) only if the `go` directive in `go.mod` is below 1.22; from 1.22 each iteration has its own variable.
- `t.Cleanup()` instead of defer for teardown that must survive helper functions.
- `t.Helper()` in every assertion helper so failures report the caller's line.
- `t.Context()` (Go 1.24+) for code under test that takes a context; it is canceled just before cleanups run.
- `errors.Is` / `errors.As` for error assertions, never string comparison.
- Accept interfaces in production code so tests can substitute fakes without a mocking framework.
- **Fuzzing** (`func FuzzX(f *testing.F)`, `go test -fuzz=FuzzX`) for parsers and decoders; commit crashers under `testdata/fuzz/`, where they become regular regression cases.

## Time and concurrency
- `testing/synctest` (Go 1.25+): run the test in `synctest.Test(t, func(t *testing.T) {...})`. Time is virtual inside the bubble, and `synctest.Wait()` returns once every goroutine is blocked — timer and timeout logic tests in microseconds, with no `time.Sleep`. Do not call `t.Run`, `t.Parallel`, or `t.Deadline` on the bubble's `t`.
- Always run `-race` in CI (supported on linux/amd64, linux/arm64, darwin, windows/amd64). It slows execution several times, so keep it off in the fast local loop if needed, but never off in CI.

## Avoid
- Heavy mocking libraries. Hand-written fakes are idiomatic and clearer.
- `httptest.NewServer` when a direct handler call (`handler.ServeHTTP(rec, req)` with `httptest.NewRecorder`) would do.
- `time.Sleep` to wait for goroutines — use channels, `sync.WaitGroup`, or `synctest`.

## Performance
- The test cache is free speed: `go test ./...` skips unchanged packages. It works only in package-list mode and with cacheable flags (`-run`, `-short`, `-v`, `-parallel`, `-timeout`, …). Use `-count=1` only when a fresh run is required (e.g. tests reading external state).
- `-short` + `if testing.Short() { t.Skip("needs Postgres") }` splits medium/large tests out of the edit loop.
- Expensive shared resources (a container, a migrated DB) go in `TestMain(m *testing.M)`, started once per package.
- `-p N` bounds packages built and tested at once; `-parallel N` bounds `t.Parallel` tests within a package (defaults to GOMAXPROCS). Lower them on memory-constrained runners.
- `-shuffle=on` exposes order coupling; the printed seed reproduces it (`-shuffle=<seed>`).
- The fuzz corpus cache is separate: clean it with `go clean -fuzzcache`, not `-cache`.
