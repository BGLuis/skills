# Triggers: which event runs which job

Read this whenever a project **produces binaries or packages** (CLI, desktop or mobile app, game, library wheels, images), when a workflow has more than one trigger or branch, and in every review. The bill is `runs × minutes × multiplier`. Most reviews only look at minutes. The number of runs is set by `on:`, and a release build that runs on every PR push multiplies the most expensive job by the most frequent event.

Sources: [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows), [workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax), [minute multipliers](https://docs.github.com/en/billing/reference/actions-minute-multipliers).

## 1. Tiers: what each event is allowed to run

| Event (how often it fires) | Runs | Never runs |
|---|---|---|
| `pull_request` (every push to every open PR: the most frequent event) | format, lint, typecheck, tests, and **the cheapest build that proves the code compiles**, on one Linux runner | release-profile builds, signing, packaging/installers, macOS/Windows/extra-arch cells, publishing, deploys |
| `pull_request` into the release branch (e.g. `develop → main` in git-flow) | the PR tier plus the full OS/arch test matrix (`if: github.base_ref == 'main'`) | packaging, signing, publishing |
| `merge_group` (once per queued batch) | the full required suite, including the OS matrix | publishing |
| `push` to the default branch (and `develop`) | the PR tier again: it saves the caches PRs restore (`references/caching.md` §3) and catches merge skew. Optionally the full matrix | release builds and publishing, **unless** the product really ships a build per commit and someone consumes it |
| `push: tags: ['v*']`, `release: [published]`, `workflow_dispatch` | release builds for every target, signing, packaging, attestation, publishing (`examples/binary-app.md`, `examples/release-oidc.md`) | — |
| `schedule` (nightly) | nightly binaries, fuzzing, the long or full matrix, with `if: github.repository == 'owner/repo'`, skipped when nothing changed since the last nightly (§4) | publishing to stable channels |

The rule: **the cost of a job must be inversely proportional to how often its trigger fires.** A 12-minute macOS release build is fine once per tag and ruinous on every PR push.

## 2. "But I need to test the packaging on a PR"

Make it opt-in instead of always-on. Three ways, from cheapest to broadest:

1. **Label.** A maintainer adds `build-binaries`, and the job runs on that event and on every later push until the label is removed. Only users with triage access can label, and the job still runs in the unprivileged `pull_request` context. Put it in **its own workflow file**: adding `labeled` to the CI workflow re-runs the whole CI whenever anyone adds any label, and with `cancel-in-progress` that new run cancels the one in progress.
   ```yaml
   # .github/workflows/package-preview.yml
   on:
     pull_request:
       types: [labeled, synchronize]
   jobs:
     package-preview:
       if: >-
         contains(github.event.pull_request.labels.*.name, 'build-binaries') &&
         (github.event.action == 'synchronize' || github.event.label.name == 'build-binaries')
   ```
   `labeled` must be listed, because the default types are only `opened`, `synchronize` and `reopened`. The second condition ignores other labels being added. Use `contains()` on the **array** `labels.*.name`; on a string, it is a substring match. Full file: `examples/binary-app.md`.
2. **`workflow_dispatch` on the branch.** `gh workflow run release.yml --ref my-branch` builds the artifacts once, on demand. Gate the publishing steps with `if: startsWith(github.ref, 'refs/tags/')` so a dispatch from a branch builds but never publishes.
3. **Paths.** A job gated by `dorny/paths-filter` on the packaging files (`Cargo.toml`, `.goreleaser.yaml`, `android/`, `ios/`, `Info.plist`, the release workflow itself) runs the packaging build only when they change. This uses the same job-level pattern as `examples/monorepo-paths-filter.md`; never `on.paths` on a required workflow.

## 3. Branch models

- **Don't double-run.** `on: [push, pull_request]` without branch filters runs every commit of a same-repo PR twice: once for the branch push and once for the PR. Use `push: branches: [main]` (plus `develop` if you have it) and a bare `pull_request:`.
- **Git-flow (feature → `develop` → `main`).** PRs into `develop` get the PR tier. The PR `develop → main` is the release candidate: add the OS matrix there, with `if: github.base_ref == 'main'`. Tag on `main` to release. Pushes to `develop`/`main` only re-run the gate and save caches (`save-if` on both branches).
- **Trunk-based (feature → `main`).** PR tier on PRs, the full matrix in the merge queue or on push to `main`, and a release on tags.
- **Continuous pre-releases** (a build published on every merge to `main`) are a product decision, not a default. If nobody installs every build, publish nightly (§4) or on dispatch. If they do, publish **one** platform per merge and leave the expensive ones (macOS/iOS, Windows installers) to tags.
- **`workflow_run` chained on CI** to "release after CI passes on main" has the same frequency as push to main. It moves the trigger, not the cost. It also runs privileged, so `references/security.md` §3 applies.
- `ubuntu-latest` and the other `-latest` labels: pin them anyway (`references/performance-cost.md` §2).

## 4. Nightly that skips when nothing changed

```yaml
on:
  schedule:
    - cron: '17 3 * * *'   # off the hour: top-of-the-hour schedules are delayed under load
  workflow_dispatch:

jobs:
  changed:
    if: github.repository == 'owner/repo'
    runs-on: ubuntu-slim
    timeout-minutes: 2
    permissions:
      actions: read # list previous runs of this workflow
    outputs:
      build: ${{ steps.check.outputs.build }}
    steps:
      - id: check
        env:
          GH_TOKEN: ${{ github.token }}
          GH_REPO: ${{ github.repository }}
          WORKFLOW_REF: ${{ github.workflow_ref }}
          HEAD_SHA: ${{ github.sha }}
        run: |
          workflow_file=$(basename "${WORKFLOW_REF%@*}")
          last=$(gh run list -w "$workflow_file" --status success --limit 1 --json headSha --jq '.[0].headSha // ""')
          if [ "$last" = "$HEAD_SHA" ]; then echo "build=false" >> "$GITHUB_OUTPUT"; else echo "build=true" >> "$GITHUB_OUTPUT"; fi

  nightly:
    needs: changed
    if: needs.changed.outputs.build == 'true'
    # ... the release matrix, publishing to a "nightly" pre-release only
```

## 5. Count the runs before optimizing the minutes

In every review of a project that builds binaries, produce this table first:

| Workflow · job | Trigger(s) | Runs / month | Billable min / run | Multiplier | Min / month |
|---|---|---|---|---|---|

Get the run counts from the API instead of guessing:

```bash
R=owner/repo; SINCE=$(date -d '30 days ago' +%F)   # macOS: date -v-30d +%F
for ev in pull_request push merge_group schedule workflow_dispatch; do
  printf '%-18s %s\n' "$ev" "$(gh run list -R $R -w release.yml --event $ev --created ">=$SINCE" --limit 1000 --json databaseId --jq length)"
done
gh pr list -R $R --state open --json number --jq length   # each push to each of these triggers the PR tier
```

Billable minutes per run come from `references/review-checklist.md` §2 (Σ ceil(job seconds / 60) × multiplier). Then name the **single row with the most minutes per month**. It is almost always a release, macOS or Windows job on a frequent trigger, and moving it to the right tier beats any cache tuning.

- Public repos don't pay for standard runners, but runs still cost queue time. Concurrency is capped per account (Free plan: 20 concurrent jobs, of which 5 macOS), so release builds on every PR block every other PR's CI.
- Example: a 12-minute macOS build (multiplier 10) on 100 PR pushes a month is 12,000 Linux-equivalent minutes. Moved to tags (4 a month), it is 480.

## 6. PR build vs release build, per stack

| Stack | PR tier (Linux, cheap) | Release tier (tags/dispatch) |
|---|---|---|
| Rust | `cargo clippy`, `cargo test`, `cargo build --locked` (debug) | `cargo build --release --locked --target <t>` per target, strip, archive (`examples/binary-app.md`) |
| Go | `go vet`, `go test`, `go build ./...` | `goreleaser release --clean`. `goreleaser release --snapshot --clean` only behind a label or dispatch |
| Flutter / Android | `flutter analyze`, `flutter test`. `flutter build apk --debug` only if native code changed (paths filter) | `flutter build appbundle/apk --release` + signing, in an `environment:` |
| Flutter / iOS, Swift | nothing on macOS by default. A simulator/`--no-codesign --debug` build only when `ios/` or native code changed, as a non-required check | `flutter build ipa` / `xcodebuild archive` + signing on macOS, on tags only |
| Tauri / Electron | frontend build + tests, `cargo check` / unit tests on Linux | `tauri build` / `electron-builder` on the 3 OS matrix, signing, on tags |
| Python wheels with native code | `uv build` for one platform, tests | `cibuildwheel` across the matrix, on tags (`examples/release-oidc.md`) |
| Docker | build without push (`examples/docker-build-push.md`) | push + attest on `main`/tags |
