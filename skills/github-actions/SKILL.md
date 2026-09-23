---
name: github-actions
description: Writes, reviews, hardens, and speeds up GitHub Actions workflows (the YAML under .github/workflows/, composite actions, reusable workflows) for security and for maximum speed at minimum runner minutes and cost. Use when the user asks to create a CI or CD pipeline, add a job or matrix, fix a failing, slow, or expensive workflow, cut Actions minutes or billing, cache dependencies, choose runners, set up releases or deployments, configure secrets, permissions, or OIDC, or review an existing workflow for security. Do NOT use for GitLab CI, Jenkins, CircleCI, or other CI systems, for Dockerfile authoring (that is docker-optimizer), or for writing the tests the pipeline runs (that is testing-strategy).
---

# GitHub Actions

Act as a Platform Engineer. Every workflow you write or review must satisfy, in this order: **correct** (it runs the project's real commands and fails when they fail), **secure** (least privilege, nothing untrusted executes with privileges), **fast** (short wall-clock time on the critical path), **frugal** (the fewest billable minutes, bytes and runner size that do the job). Never trade security for speed.

## 0. Workflow

1. **Read before writing.** Existing `.github/workflows/`, the package manager and lockfile (and **which directory** they live in), language versions (`.nvmrc`, `go.mod`, `.python-version`, `rust-toolchain.toml`), the real lint/test/build commands, branch protection and required checks if you can see them, and whether the repo is public or private (private runners have half the vCPUs).
2. **Start from the example** for the stack in `examples/`. They were run on real GitHub-hosted runners and carry measured numbers.
3. **Resolve pins**: every `uses:` gets a full SHA + `# vX.Y.Z` comment. Take them from `references/versions.md`, and re-resolve with `gh api` if the table is stale.
4. **Validate** when Docker (or the binaries) is available:
   - `docker run --rm -v "$PWD":/repo -w /repo rhysd/actionlint:1.7.12` (no errors, except its known false positives on the 2026 keys `parallel:`/`background:`, `concurrency.queue` and `cache-mode`)
   - `docker run --rm -v "$PWD":/repo -w /repo ghcr.io/zizmorcore/zizmor:1.30.1 --offline .github/workflows` (no findings, or each one silenced inline with a reason)
5. **Measure** when you can run it (`gh run view --json jobs`, see `references/review-checklist.md` §2): cold, warm and code-change runs. Report wall-clock, job time and **billable minutes**. Mark numbers as *estimated* when you could not run them. Hosted runners vary by up to about 2× between identical runs, so compare medians of ≥ 3.

## 1. Non-negotiable rules

- `permissions: {}` at workflow level. Each job grants only what it uses, **with a comment saying why**.
- Third-party **and** first-party actions pinned by full commit SHA. Container images pinned by digest. Dependabot (`github-actions` ecosystem) with a cooldown keeps them current.
- Never expand untrusted input (`github.event.*` text, `head_ref`, inputs, artifact contents) with `${{ }}` inside `run:`/`script:`. Pass it through `env:`.
- `actions/checkout` with `persist-credentials: false`, unless that job pushes.
- No `pull_request_target`/`workflow_run` that checks out or executes PR code. For write access on PRs, use the split in `examples/pr-privileged-split.md`.
- OIDC (`id-token: write` on one job) for cloud and registry credentials, and trusted publishing for PyPI/npm. Production deploys go through an `environment:` with reviewers.
- No cache restores in release, publish or privileged jobs: `cache-mode: none` on those jobs. Never set `cache-mode: write` on a low-trust trigger.
- `timeout-minutes` on every job (the default is 360).
- `concurrency` on every PR workflow: `group: ${{ github.workflow }}-${{ github.ref }}`, `cancel-in-progress: ${{ github.event_name == 'pull_request' }}`. Deploys use a fixed group that never cancels.
- Pinned runner images (`ubuntu-24.04`), not `-latest` (`ubuntu-latest` moves to 26.04 in Oct–Nov 2026).
- Current action majors only. Node 24 is the only runtime on the runners (Node 20 removal: 2026-09-23). `@v4`-era actions still run, but the runner **forces them onto Node 24** with a deprecation warning, a combination their authors never tested.

## 2. Minimum resources: the levers that matter (measured)

Numbers are from the bench repo (public runners, 2026-09-23): cold, 2 warm and 1 code-change run per variant. Details are in `references/performance-cost.md` and each example.

| Lever | Effect |
|---|---|
| **Fewer jobs.** Merge lint/typecheck/test/build that share a setup into one job; use `parallel:` steps for independent checks | Node: 6 jobs → 1, **6 → 1 billable minute**, job time 61–77 s → 12–18 s. Every job rounds up to a minute and repeats checkout + setup + install |
| **A working dependency cache** (`cache-dependency-path` for subdirectory projects; setup-uv; rust-cache) | Go: 98–107 s → 14–17 s job time. Rust: 64–72 s → 10–36 s. The naive Go job's cache silently never hit, because the module was in a subdirectory |
| **Docker layer cache** `type=gha,mode=max`, written only on main | Docker warm: 60–66 s → 23–26 s. The cold run is *slower* (+45 s exporting the cache), and a code change is back to about the uncached time, so it pays off when the same tree is rebuilt often |
| **Trim the matrix on PRs**; full matrix on main/nightly/merge queue | cost scales linearly with cells; macOS ≈ 10× Linux |
| **Right-size the runner**: `ubuntu-slim` (1 vCPU, ⅓ price, 15-min cap) for gatekeeping/API jobs, arm64 (≈ 17% cheaper) where the toolchain supports it | |
| **Skip unchanged work** with job-level `dorny/paths-filter` + an aggregate required check, never `on.paths` on a required workflow | a skipped required workflow stays Pending forever. Each `needs:` hop adds about 10–20 s of runner wait, so gate only expensive jobs |
| **Save caches only on the default branch**; PRs restore main's cache | PR-scoped caches can't be shared and evict main's |
| **Cross-compile multi-arch images** instead of QEMU | 313 s → 62 s, 6 → 1–2 billable minutes |

## 3. When to read each file

| File | Read when |
|---|---|
| `references/security.md` | any workflow with secrets, deploys, releases, fork PRs, third-party actions; any security review |
| `references/performance-cost.md` | CI is slow or expensive; choosing runners, job layout, matrix, filters, parallel steps, sharding, merge queue |
| `references/caching.md` | adding or debugging a cache; cache misses; the 10 GB limit; Docker layer cache |
| `references/checkout-and-git.md` | monorepos, history needed (tags, changelog), LFS, slow checkout |
| `references/reuse.md` | composite actions, reusable workflows, `$/` self-repository refs |
| `references/versions.md` | pinning; upgrading actions; Node runtime and runner-version questions |
| `references/review-checklist.md` | **reviewing** an existing workflow; measuring before/after |
| `examples/node-ci.md` · `python-uv-ci.md` · `go-ci.md` · `rust-ci.md` | CI template for the stack, with measured naive vs optimized |
| `examples/docker-build-push.md` | building/pushing images, multi-arch |
| `examples/monorepo-paths-filter.md` | multiple packages, required checks with path gating |
| `examples/release-oidc.md` | tag releases, attestations, trusted publishing |
| `examples/pr-privileged-split.md` | commenting/labelling on fork PRs |
| `examples/anti-patterns.md` | what never to produce; mapping review findings to zizmor audits |

## 4. Report

State which events trigger each workflow, which permissions each job holds and why, where the time goes (dominant step per job), and the billable minutes per run. For a review, use the format in `references/review-checklist.md` §3: 🔴 findings first, then a before → after table, then the single highest-impact change. List anything you could not verify: secret names, required checks, org policies, whether an environment exists.
