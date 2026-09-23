# Performance and cost: maximum throughput, minimum minutes

Read this whenever the user says CI is slow or expensive, or wants "the same pipeline on fewer resources". It is also the reference for choosing runners, job layout, filters and matrices.

Sources: [GitHub-hosted runners reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners), [minute multipliers and prices](https://docs.github.com/en/billing/reference/actions-minute-multipliers), [workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax), [limits](https://docs.github.com/en/actions/reference/limits). Prices and specs are as of 2026-09.

## 1. How you are billed (and why job count matters)

- **Every job is rounded up to a whole minute.** A 9-second lint job costs one minute, the same as a 59-second one.
- Each job pays a fixed setup cost too: VM allocation, checkout, runtime install, dependency restore. On the bench repo that was **6–10 s per job before any real work**.
- Standard runners are **free on public repos**. Private repos spend included minutes (Free 2,000/month, Pro/Team 3,000, Enterprise Cloud 50,000), then pay per minute. Larger runners never use included minutes.
- macOS costs about **10×** Linux, and Windows about **1.7×**.

Consequence: for small and medium projects, **the number of jobs dominates the bill, not how long they run**. Measured on the bench repo (Node/TS app): 6 jobs (lint, typecheck, 3-version test matrix, build) came to **6 billable minutes**. One job running the same checks came to **1 billable minute**, at about the same wall-clock time. See `examples/node-ci.md`.

**Rule:** merge short sequential jobs that share a setup into one job. Split into parallel jobs only when a job is long enough (several minutes) that parallelism cuts wall-clock time meaningfully, or when the jobs need different runners or permissions.

## 2. Pick the smallest runner that holds the job

| Label | vCPU / RAM (public) | Private repos | $/min (private) | Use for |
|---|---|---|---|---|
| `ubuntu-slim` | 1 / 5 GB, **container not a VM, 15-min job cap** | same | $0.002 | gatekeeping jobs: paths-filter, labelers, aggregate "all green" checks, API calls, notifications |
| `ubuntu-24.04` (x64) | 4 / 16 GB | **2 vCPU** / 8 GB | $0.006 | default |
| `ubuntu-24.04-arm` | 4 / 16 GB | 2 vCPU (private since 2026-01-29) | $0.005 | cheaper Linux when the toolchain supports arm64; native arm64 images without QEMU |
| `windows-2025` | 4 / 16 GB | 2 vCPU | $0.010 | only when you ship to Windows |
| `macos-15` / `macos-26` (M1) | 3 / 7 GB | same | $0.062 | only when you ship to Apple platforms; keep to one cell |
| larger runners | 2–96 vCPU | — | from $0.006 | long CPU-bound builds where wall-clock time costs more than money |

- **Pin the image** (`ubuntu-24.04`, not `ubuntu-latest`). `ubuntu-latest` moves to Ubuntu 26.04 gradually between 2026-10-19 and 2026-11-19, and `macos-latest` moved to macOS 26 in mid-2026. A label that moves under you breaks toolchains on a random day.
- Private-repo standard runners have **2 vCPU**. Parallel test runners (`-j`, `--workers`, parallel steps) beyond 2 just contend for CPU there.
- `ubuntu-slim` has a hard 15-minute limit, a minimal tool set, and runs as an **unprivileged container**: no Docker, no mounts. Don't run builds on it.
- A larger runner can be **cheaper** for a CPU-bound build: 4× the cores at 2× the price is a win if the build scales. Measure before you switch.

## 3. Don't run what didn't change

- **`concurrency`**: cancel superseded PR runs, but not runs on main:
  ```yaml
  concurrency:
    group: ${{ github.workflow }}-${{ github.ref }}
    cancel-in-progress: ${{ github.event_name == 'pull_request' }}
  ```
  For deploys, use a fixed group (`deploy-production`) with `cancel-in-progress: false`. Add `queue: max` to process every deploy in order instead of replacing the pending one; it cannot be combined with `cancel-in-progress: true`.
- **Path filtering, the correct way.** `on.push.paths` / `on.pull_request.paths` skips the **whole workflow**, and a required status check from a skipped workflow stays **Pending forever**, which blocks the merge. Use these instead:
  - `on.paths` **only** for workflows that are not required checks (docs build, release notes), or
  - job-level gating: a cheap `changes` job on `ubuntu-slim` with `dorny/paths-filter` (on PRs it uses the API and needs no checkout), `if:` on the expensive jobs, and **one aggregate job with `if: always()` that is the only required check**. See `examples/monorepo-paths-filter.md`.
- `paths-ignore: ['**.md', 'docs/**']` on test workflows only if they are not required checks.
- `merge_group` (merge queue): run the full or expensive suite once per batch in the queue, and a fast subset on `pull_request`. setup-uv skips cache saving on `merge_group`, because those caches can't be read later anyway.
- `schedule:` workflows on forks and inactive repos burn minutes. Add `if: github.repository == 'owner/repo'`.

## 4. Order jobs so failures are cheap

- Cheap static checks (lint, format, typecheck) run **first in the same job**, before tests. If they fail, the job stops in seconds.
- If you need a matrix, gate it: `needs: [static]` so a lint error doesn't spin up 12 VMs.
- `fail-fast: true` (the default) cancels the rest of the matrix on the first failure, which saves minutes. Set `false` only when you need the full compatibility picture, for example on main or nightly.
- `timeout-minutes` on **every** job, at about 2–3× its normal duration. The default is 360 minutes, which means a hung test costs 6 hours.

## 5. Trim the matrix

- A matrix multiplies cost. `node: [22, 24, 26] × os: [ubuntu, windows, macos]` is 9 jobs, with macOS at 10× price.
- On PRs, test **the version you ship on Linux**. Run the full matrix on `push` to main, nightly, or in the merge queue:
  ```yaml
  strategy:
    matrix:
      node: ${{ github.event_name == 'pull_request' && fromJSON('[24]') || fromJSON('[22, 24, 26]') }}
  ```
- Use `include:` for the one extra OS combination instead of a full cross-product, and `exclude:` for the ones that add nothing.
- Limits: 256 jobs per matrix, and `max-parallel` to cap concurrency (useful with rate-limited external services).

## 6. Use the cores you pay for

- **Parallel steps** (2026): `parallel:` runs a group of steps at once inside one job and waits for all of them. `background: true` + `wait` / `wait-all` / `cancel` give fine control, for example a server running while tests execute. There's a limit of 10 concurrent background steps, and none inside composite actions.
  ```yaml
  - run: npm ci
  - parallel:
      - run: npm run lint
      - run: npm run typecheck
      - run: npm test
  - run: npm run build
  ```
  This helps when the steps are I/O-bound or single-threaded (linters, type checkers). CPU-bound steps on a 2-vCPU private runner just share the same two cores. actionlint 1.7.12 does not know this syntax yet and reports `step must run script with "run" section`; that's a false positive.
- Test runners: `-j$(nproc)` / `--workers=auto` / `pytest -n auto` (pytest-xdist) / `go test` (parallel by default) / `cargo nextest`.
- **Sharding** across jobs only for long suites (> ~5 min). Each shard pays the setup cost and minute rounding again:
  ```yaml
  strategy:
    matrix:
      shard: [1, 2, 3, 4]
  steps:
    - run: npx vitest run --shard=${{ matrix.shard }}/4
  ```

## 7. Don't do work twice

- Build once, then pass the output to the following jobs with `upload-artifact`/`download-artifact` instead of rebuilding.
- Skip `setup-*` for tools already on the runner image (git, jq, gh, docker, rustup/cargo, python3, a Node LTS). Check the image readme (`actions/runner-images`) and zizmor `superfluous-actions`. Keep the setup action when you need a **specific** version or its built-in cache.
- Install with the lockfile and no extras: `npm ci --no-audit --no-fund`, `uv sync --locked`, `cargo … --locked`, `go mod download` only if not using setup-go's cache.
- Don't build release binaries on every PR unless you ship them from the PR.
- Artifacts: `retention-days: 1–7` for CI outputs (the default follows the repo setting, often 90), and `compression-level: 0` for already-compressed files (images, tarballs, zips). Artifact storage beyond the plan's quota is billed.

## 8. Report what you measured

When optimizing, report for the before and after: **wall-clock time** (created → completed), **the sum of job durations**, **billable minutes** (the sum of per-job rounded-up minutes, times the runner multiplier), and the step that dominates. Use the commands in `references/review-checklist.md` §2.
