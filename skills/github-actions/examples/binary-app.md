# App that ships binaries: cheap CI on PRs, release builds on tags

A Rust CLI (`mycli`) released for Linux x64/arm64, Windows and macOS. The layout applies to any project whose release produces binaries, installers, APKs or IPAs (see `references/triggers.md` §6 for Go, Flutter, Tauri/Electron). There are three workflows, one per tier of `references/triggers.md` §1:

| File | Trigger | What runs |
|---|---|---|
| `ci.yml` | every PR push, push to `main` | fmt, clippy, tests, **debug** build on one Linux runner. Windows/macOS tests only on `main` |
| `package-preview.yml` | PR with the `build-binaries` label | one Linux release build, as an artifact kept 1 day |
| `release.yml` | tag `v*.*.*`, `workflow_dispatch` | release builds for 4 targets, attestation, GitHub release (tags only) |

**Not measured.** Unlike the other examples, these workflows were not run on a bench repo. They were validated with actionlint 1.7.12 (only the known `cache-mode` false positive) and zizmor 1.32.0 (no findings). The minutes below are an estimate from stated assumptions.

## Estimated cost per month

Assumptions: 100 PR pushes, 20 merges to `main`, 2 tags. Job times: Linux check 4 min; tests on Windows 8 min and macOS 6 min; release builds of 5 min (Linux x64, arm64), 10 min (Windows) and 8 min (macOS). Multipliers: Windows 1.7, macOS 10, arm64 0.83, `ubuntu-slim` ⅓. Figures are in Linux-equivalent minutes.

| Layout | Per PR push | Per merge | Per tag | Month |
|---|---|---|---|---|
| Everything on every `pull_request` and `push` (what release-on-every-PR workflows end up doing) | 184 | 184 | 184 | **≈ 22,400** |
| This file | 4 | 78 | 107 | **≈ 2,170** |

About 10× less, and almost all of the gain comes from moving the macOS and Windows builds off the PR trigger. The same rows measured on a real repo: `references/triggers.md` §5.

## `.github/workflows/ci.yml`

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
  check:
    name: check
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    permissions:
      contents: read # checkout
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: Swatinem/rust-cache@d1527c8f67ef9af357290475d4af4b0fab8f12e0 # v2.9.3
        with:
          save-if: ${{ github.ref == 'refs/heads/main' }}
      - run: cargo fmt --check
      - run: cargo clippy --locked --all-targets -- -D warnings
      - run: cargo test --locked
      # Debug build: proves the binary links, reusing the test profile's artifacts.
      - run: cargo build --locked

  # Windows and macOS catch path, line-ending and linker problems, at 1.7× and 10× the price.
  # They run once per merge, not once per PR push.
  os-matrix:
    name: test (${{ matrix.os }})
    if: github.event_name == 'push'
    needs: check
    runs-on: ${{ matrix.os }}
    timeout-minutes: 20
    permissions:
      contents: read # checkout
    strategy:
      fail-fast: false
      matrix:
        os: [windows-2025, macos-15]
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: Swatinem/rust-cache@d1527c8f67ef9af357290475d4af4b0fab8f12e0 # v2.9.3
      - run: cargo test --locked
```

## `.github/workflows/package-preview.yml`

```yaml
name: package-preview
on:
  pull_request:
    types: [labeled, synchronize]

permissions: {}

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  package-preview:
    name: package-preview
    # Only with the label, and only when the label is added or new code is pushed.
    if: >-
      contains(github.event.pull_request.labels.*.name, 'build-binaries') &&
      (github.event.action == 'synchronize' || github.event.label.name == 'build-binaries')
    runs-on: ubuntu-24.04
    timeout-minutes: 20
    permissions:
      contents: read # checkout
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - run: cargo build --release --locked
      - uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
        with:
          name: mycli-preview-linux-x64
          path: target/release/mycli
          retention-days: 1
          if-no-files-found: error
```

## `.github/workflows/release.yml`

```yaml
name: release
on:
  push:
    tags: ['v*.*.*']
  workflow_dispatch:

permissions: {}

# Never cancel a release half-way.
concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false

env:
  CARGO_TERM_COLOR: always

jobs:
  build:
    name: build (${{ matrix.target }})
    runs-on: ${{ matrix.runner }}
    timeout-minutes: 30
    cache-mode: none # release: never restore or save a cache
    permissions:
      contents: read      # checkout
      id-token: write     # sign the provenance attestation
      attestations: write # store the attestation
    strategy:
      matrix:
        include:
          - { target: x86_64-unknown-linux-musl, runner: ubuntu-24.04 }
          - { target: aarch64-unknown-linux-musl, runner: ubuntu-24.04-arm }
          - { target: x86_64-pc-windows-msvc, runner: windows-2025, ext: .exe }
          - { target: aarch64-apple-darwin, runner: macos-15 }
    defaults:
      run:
        shell: bash
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - name: Tag must match the crate version
        if: github.ref_type == 'tag'
        env:
          TAG: ${{ github.ref_name }}
        run: test "v$(cargo metadata --no-deps --format-version 1 | jq -r '.packages[0].version')" = "$TAG"
      - if: contains(matrix.target, 'musl')
        run: sudo apt-get update -q && sudo apt-get install -y -q --no-install-recommends musl-tools
      - env:
          TARGET: ${{ matrix.target }}
        run: |
          rustup target add "$TARGET"
          cargo build --release --locked --target "$TARGET"
      - name: Package
        env:
          TARGET: ${{ matrix.target }}
          EXT: ${{ matrix.ext }}
          VERSION: ${{ github.ref_name }}
        run: |
          mkdir -p dist
          out="$PWD/dist/mycli-$VERSION-$TARGET"
          cd "target/$TARGET/release"
          if [ "$EXT" = ".exe" ]; then 7z a "$out.zip" "mycli.exe" > /dev/null; else tar -czf "$out.tar.gz" mycli; fi
      - uses: actions/attest-build-provenance@4d101475d8b20a2381f78447822ac1eab6504dd8 # v4.2.2
        with:
          subject-path: dist/*
      - uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
        with:
          name: dist-${{ matrix.target }}
          path: dist/*
          retention-days: 7
          compression-level: 0 # already compressed
          if-no-files-found: error

  github-release:
    name: github-release
    needs: build
    # A dispatch from a branch builds and attests, but never publishes.
    if: github.ref_type == 'tag'
    runs-on: ubuntu-slim
    timeout-minutes: 5
    cache-mode: none # holds publishing rights: no cache at all
    permissions:
      contents: write # create the release and upload assets
    steps:
      - uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
        with:
          pattern: dist-*
          merge-multiple: true
          path: dist/
      - env:
          GH_TOKEN: ${{ github.token }}
          GH_REPO: ${{ github.repository }}
          TAG: ${{ github.ref_name }}
        run: gh release create "$TAG" dist/* --verify-tag --generate-notes
```

## Why it looks like this

- **The release build never runs on `pull_request`.** A PR proves the code compiles with `cargo build` (debug), which reuses the artifacts `cargo test` just compiled. `--release` recompiles every dependency with another profile, and the four-target matrix multiplies that by four runners, two of them at 1.7× and 10×.
- **Windows and macOS tests run once per merge**, after `check` passes (`needs: check`), so a lint error doesn't start them. If the repo uses git-flow, run them on the `develop → main` PR instead: `if: github.event_name == 'push' || github.base_ref == 'main'` (`references/triggers.md` §3).
- **Packaging on a PR is opt-in** through a separate workflow and a label. It is not a required check, so a PR without the label is never blocked by it.
- **Native runners instead of cross-compiling**: `ubuntu-24.04-arm` builds arm64 at 0.83× the x64 price, and Windows/macOS have no practical cross-compile path from Linux for Rust binaries that link system libraries. A pure-Rust CLI can cross-compile both Linux targets on one x64 runner with `cargo-zigbuild` or `cross` instead.
- **musl targets** give static Linux binaries that run on any distro. A `-gnu` build from `ubuntu-24.04` needs glibc ≥ 2.39 on the user's machine.
- **`cache-mode: none` on both release jobs**, and no rust-cache step: the published binaries are compiled from the tagged source only (`references/security.md` §3). A release is rare, so the cold build costs little in total.
- **`workflow_dispatch`** lets you test the release pipeline from a branch: `gh workflow run release.yml --ref my-branch`. `github-release` only runs on tags.
- **One artifact per target**, then merged with `pattern` + `merge-multiple`. `compression-level: 0` skips recompressing archives.
- **The tag must match `Cargo.toml`**, so a tag pushed without a version bump fails in seconds instead of publishing a binary that reports the wrong version. On Windows the step runs in Git Bash, where `jq` is available.

## Adapting to other stacks

- **Go + GoReleaser**: `ci.yml` runs `go vet`, `go test` and `go build ./...`. `release.yml` runs `goreleaser/goreleaser-action` (pinned by SHA) with `release --clean` on tags. The preview workflow runs `release --snapshot --clean`. GoReleaser cross-compiles every target from one Linux runner, so the matrix is not needed.
- **Flutter**: `ci.yml` runs `flutter analyze` and `flutter test` on Linux, plus `flutter build apk --debug` only when `android/` or native code changed (paths filter). Android release builds (`appbundle`, signing) and iOS builds (macOS, `flutter build ipa`) belong in `release.yml`, with signing secrets in an `environment:`. An iOS build in a PR is a labelled preview at most.
- **Tauri / Electron**: the 3-OS installer matrix (`tauri build`, `electron-builder`) goes in `release.yml`. PRs build the frontend and run `cargo check`/tests on Linux.
