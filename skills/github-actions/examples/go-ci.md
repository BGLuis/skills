# Go CI

Measured on GitHub-hosted public runners (`ubuntu-24.04`) on 2026-09-23, using a chi + prometheus client service with `go vet`, `go test -race` and `go build`. The module lives in `go/`, as in most monorepos. The naive workflow: vet / test / build as three jobs, `setup-go` with `go-version: stable` and no `cache-dependency-path`. actionlint and zizmor: clean.

Format: wall-clock / Σ job time / billable minutes.

| Run | Naive (3 jobs) | This file (1 job) |
|---|---|---|
| Cold | 80 s / 107 s / **3** | 85 s / 80 s / **2** |
| Warm (median of 2) | 77 s / 100 s / **3** | 19 s / 16 s / **1** |
| Code change | 78 s / 107 s / 3 | 18 s / 15 s / 1 |
| Cache stored | nothing (see 1) | 104 MB (module + build cache) |

Warm and code-change runs are **5–6× faster** and use a third of the minutes.

## Why it looks like this

1. **The naive cache never worked.** `setup-go` caches by default, but it looks for its dependency file at the repo root. With the module in `go/`, every job logged
   `##[warning]Restore cache failed: Dependencies file is not found in /home/runner/work/…. Supported file pattern: go.mod`
   and stayed green, so nobody notices. Each run recompiled the dependency graph from scratch (vet 15–18 s, test 24–27 s, build 15–17 s). `cache-dependency-path: go/go.sum` fixes it.
2. **setup-go caches the build cache, not just modules.** With a warm `~/.cache/go-build`, `go vet`, `go test -race` and `go build` only recompile the package that changed. All three together took under 5 s after a code change.
3. **`go-version-file: go.mod`** pins the toolchain the module declares. `stable` changes under you on release day.
4. **One job**: vet, test and build share the build cache. Split jobs each paid the cache-less compile again.
5. **Cold, the single job is not faster.** It runs vet, test and build one after another without a cache (18 + 26 + 15 s), plus a 4 s post step saving 104 MB. The naive layout ran them on three VMs in parallel. Wall-clock is about the same, and it still bills 2 minutes instead of 3. The gain comes from every run after that.

## Code

```yaml
name: ci
on:
  push:
    branches: [main]
  pull_request:

permissions: {}

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

jobs:
  ci:
    name: ci
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    permissions:
      contents: read # checkout
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: actions/setup-go@b7ad1dad31e06c5925ef5d2fc7ad053ef454303e # v7.0.0
        with:
          go-version-file: go.mod
          cache-dependency-path: go.sum
      - run: go vet ./...
      - run: go test -race ./...
      - run: go build -trimpath -o /dev/null ./...
```

- Subdirectory module: `go-version-file: <dir>/go.mod`, `cache-dependency-path: <dir>/go.sum`, `defaults.run.working-directory: <dir>` (this is the bench's `go-opt.yml`).
- setup-go only saves the cache when the key is new (key = OS + Go version + `go.sum` hash). A PR that only changes code reuses main's cache, and it can't write its own. That's the behavior you want.
- golangci-lint: use `golangci/golangci-lint-action` pinned by SHA, with `version:` pinned. It has its own cache, so put it in the same job after setup-go.
- Release jobs: `cache: false`, so a published binary is never built from a restored cache.
