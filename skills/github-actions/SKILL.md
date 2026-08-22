---
name: github-actions
description: Writes, reviews, hardens, and speeds up GitHub Actions workflows — the YAML under .github/workflows/. Use when the user asks to create a CI or CD pipeline, add a job or matrix, fix a failing or slow workflow, cache dependencies, set up automated releases or deployments, configure secrets and permissions, or review an existing workflow for security. Do NOT use for GitLab CI, Jenkins, CircleCI or other CI systems, for Dockerfile authoring (that is docker-optimizer), or for writing the tests the pipeline runs (that is testing-strategy).
---

# GitHub Actions

Act as a Platform Engineer. Every workflow you write or review must satisfy three properties, in this order: **correct**, **secure**, **fast**. Never trade security for speed.

## 0. Before writing

Read the repository first: existing workflows in `.github/workflows/`, the package manager and lockfile, the language versions (`.nvmrc`, `go.mod`, `pyproject.toml`, `rust-toolchain.toml`), and the test/build commands actually used. A pipeline that runs commands the project does not have is worse than none.

When reviewing an existing workflow, end with a before/after summary: what was insecure, what was wasted (minutes and why), and the expected wall-clock gain.

## 1. Security (never negotiable)

- **Least-privilege token.** Set `permissions: {}` at workflow level and grant only what each job needs (`contents: read`, `pull-requests: write`). The default token is far too broad.
- **Pin third-party actions by commit SHA**, not by tag: `uses: owner/action@a1b2c3d...  # v4.1.0`. Tags are mutable and are a real supply-chain vector. First-party `actions/*` may use a major tag if the project prefers, but SHA is safer.
- **`pull_request_target` is dangerous.** It runs with a privileged token in the base-repo context. Never check out or execute code from the PR head under it. If you only need to label or comment, keep it; otherwise use `pull_request`.
- **Never interpolate untrusted input into `run:`.** `${{ github.event.pull_request.title }}` inside a shell script is command injection. Pass it through `env:` and reference `"$TITLE"` in the script.
- **Prefer OIDC over long-lived secrets** for cloud deploys (`id-token: write` plus the provider's role assumption). Rotate anything that cannot use OIDC.
- Secrets are unavailable to forked-PR workflows by design — do not attempt to work around this.
- Use **environments** with required reviewers for production deploys.

## 2. Speed and cost

- **Concurrency**: cancel superseded runs.
  ```yaml
  concurrency:
    group: ${{ github.workflow }}-${{ github.ref }}
    cancel-in-progress: true
  ```
  Do not cancel in progress on `main` if deploys must complete.
- **Cache correctly**: prefer the language setup actions' built-in caching (`actions/setup-node` with `cache: npm`, `setup-python` with `cache: pip`, `setup-go`). Fall back to `actions/cache` with a key derived from the lockfile hash and a narrower `restore-keys` prefix.
- **Path filters** so unrelated changes do not trigger full pipelines. For a monorepo, filter per package.
- **Fail fast on cheap jobs**: lint and typecheck before the expensive test matrix.
- **`fetch-depth: 0` only when needed** (tags, changelog generation). The default shallow clone is much faster.
- **Matrix** to parallelise across versions/OS. Set `fail-fast: false` when you want the full picture of which combinations break.
- Always set a `timeout-minutes` per job — a hung job otherwise burns six hours.

## 3. Correctness

- Trigger on `push` to the default branch and `pull_request`; add `workflow_dispatch` for manual runs.
- Job dependencies via `needs:`. Remember `needs` short-circuits on failure — use `if: always()` for reporting jobs.
- Pin runner images explicitly (`ubuntu-24.04`, not `ubuntu-latest`) when reproducibility matters; `latest` shifts under you.
- Use `${{ }}` expressions in `if:` without wrapping the whole condition redundantly.
- Upload test results and coverage as artifacts so failures are diagnosable without re-running.
- For releases, prefer tag-triggered workflows with `contents: write` scoped to that job alone.

## 4. Reference workflows

Read the relevant file before writing:

- `references/patterns.md` — reusable workflows, composite actions, dependency caching per ecosystem, release and deploy shapes
- `references/review-checklist.md` — ordered checklist for auditing an existing workflow

## 5. Report

State which triggers fire the workflow, what permissions each job holds and why, where the time is spent, and anything you could not verify (for example, whether a referenced secret exists).
