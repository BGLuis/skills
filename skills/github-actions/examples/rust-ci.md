# Rust CI

Measured on GitHub-hosted public runners (`ubuntu-24.04`) on 2026-09-23, using an axum + tokio + serde service with clippy, tests and a release build. The naive workflow: clippy / test / release build as three jobs, each installing the toolchain with `dtolnay/rust-toolchain@stable`, no cache. actionlint and zizmor: clean.

Format: wall-clock / Σ job time / billable minutes.

| Run | Naive (3 jobs) | This file (1 job) |
|---|---|---|
| Cold | 57 s / 72 s / **3** | 57 s / 54 s / **1** |
| Warm (2 runs) | 52–62 s / 66–68 s / **3** | 18–40 s / 13–36 s / **1** |
| Code change | 52 s / 64 s / 3 | 14 s / 10 s / 1 |
| Cache stored | — | 112 MB |

The warm range is runner noise: the same cache hit took clippy 2 s in one run and 15 s in the other.

## Why it looks like this

1. **`Swatinem/rust-cache`** caches `~/.cargo` (registry, git deps, installed binaries) **and `target/` for dependencies**. It strips workspace crates before saving, so the cache doesn't grow with every commit. A code change then recompiles only your crate: clippy + test + release build took 10 s of job time.
2. **`save-if: main` only.** PRs restore main's cache and never save their own copy, which would be PR-scoped, useless to others, and would evict main's under the 10 GB limit.
3. **No toolchain action.** rustup, cargo, clippy and rustfmt are preinstalled on GitHub-hosted Ubuntu images. Add `rust-toolchain.toml` to the repo and rustup installs the pinned version automatically on the first `cargo` call. `dtolnay/rust-toolchain@stable` is a mutable branch ref, one more third-party action to pin.
4. **One job**: clippy, test and build share one `target/` and one cache restore. In the naive layout each job compiled the full dependency graph (13–25 s each).
5. **`--locked`** fails if `Cargo.lock` doesn't match `Cargo.toml`, instead of silently updating it in CI.
6. Rust-cache sets `CARGO_INCREMENTAL=0`. Incremental artifacts are large and useless on a fresh runner.

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

env:
  CARGO_TERM_COLOR: always

jobs:
  ci:
    name: ci
    runs-on: ubuntu-24.04
    timeout-minutes: 20
    permissions:
      contents: read # checkout
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      # rustup/cargo/clippy are preinstalled; rust-toolchain.toml pins the version.
      - uses: Swatinem/rust-cache@6323deb102c322ba6fcbdcafc7e3dddab59af2b6 # v2.9.2
        with:
          save-if: ${{ github.ref == 'refs/heads/main' }}
      - run: cargo fmt --check
      - run: cargo clippy --locked --all-targets -- -D warnings
      - run: cargo test --locked
```

- The bench also ran `cargo build --release --locked` in this job, to compare with the naive layout. Only keep it on PRs if you ship the artifact from the PR. It compiles every dependency a second time with a different profile.
- Subdirectory crate: `workspaces: <dir>` on rust-cache and `defaults.run.working-directory: <dir>` (the bench's `rust-opt.yml`).
- Large test suites: `cargo nextest run` (install it with `taiki-e/install-action` pinned by SHA) runs tests in parallel per process and supports `--partition count:N/M` for sharding across jobs.
- Several jobs that need the same dependencies (for example a matrix over features): set the same `shared-key` so they share one cache instead of one per job.
