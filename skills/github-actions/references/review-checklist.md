# Review checklist and measurement

Use this when **reviewing** an existing workflow and to produce before/after numbers. Report 🔴 findings first. They are exploitable or break the pipeline.

Severity: 🔴 security/correctness · 🟠 cost/speed · 🟡 maintainability.

## 1. Checklist

| # | Check | Sev. | Tool |
|---|---|---|---|
| 1 | `${{ github.event.* }}`, `head_ref`, inputs or step outputs from untrusted data expanded inside `run:` / `script:` | 🔴 | zizmor `template-injection`, actionlint |
| 2 | `pull_request_target` / `workflow_run` / `issue_comment` that checks out or runs PR code, or consumes artifacts as code/env | 🔴 | zizmor `dangerous-triggers`, Scorecard `Dangerous-Workflow` |
| 3 | No `permissions:`, `write-all`, or write scopes on jobs that don't use them | 🔴 | zizmor `excessive-permissions`, Scorecard `Token-Permissions` |
| 4 | Third-party `uses:` pinned to a tag/branch, not a SHA; container images without a digest | 🔴 | zizmor `unpinned-uses`, `unpinned-images`; `pinact run --check` |
| 5 | `persist-credentials` left at the default in jobs that don't push, especially if they upload artifacts | 🔴 | zizmor `artipacked` |
| 6 | Long-lived cloud keys or registry tokens where OIDC / trusted publishing works | 🔴 | zizmor `use-trusted-publishing` |
| 7 | `secrets: inherit`, `toJSON(secrets)`, secrets echoed or written to files that get uploaded | 🔴 | zizmor `secrets-inherit`, `overprovisioned-secrets` |
| 8 | Cache restored in a release/publish/privileged job (no `cache-mode: none`), or `cache-mode: write` on a low-trust trigger | 🔴 | zizmor `cache-poisoning` |
| 9 | Actions on the removed Node 20 runtime (`checkout@v4`, `cache@v4`, `setup-node@v4`, `setup-python@v5`, `setup-go@v5`, `upload-artifact@v4`…) | 🔴 | run fails; check `references/versions.md` |
| 10 | Required check comes from a workflow with `on.paths`, so it stays pending when skipped | 🔴 | manual |
| 11 | `if:` pitfalls: `if: \|` block that is always true, `a && b \|\| c` with falsy `b`, `contains()` on a string | 🔴 | zizmor `unsound-condition`, `unsound-ternary`, `unsound-contains` |
| 12 | No `concurrency` on PR workflows, or `cancel-in-progress: true` that also cancels main/deploys | 🟠 | zizmor `concurrency-limits` |
| 13 | No `timeout-minutes` (default 360) | 🟠 | manual |
| 14 | Many short jobs sharing the same setup (each rounds up to 1 billable minute) | 🟠 | measure (§2) |
| 15 | No dependency cache, a cache that silently misses (subdirectory lockfile), or a key without `hashFiles` | 🟠 | step log: `Cache not found`, `Dependencies file is not found` |
| 16 | Caches saved from PR runs (evicts main's cache, useless to other PRs) | 🟠 | `gh cache list --ref refs/pull/…` |
| 17 | Full matrix (versions × OS) on every PR; macOS/Windows cells without need | 🟠 | manual |
| 18 | `fetch-depth: 0` without `filter:`; full checkout for a monorepo package | 🟠 | step time |
| 19 | Setup actions or installs for tools already on the image; `pip install uv` per job | 🟠 | zizmor `superfluous-actions` |
| 20 | Heavy jobs on `ubuntu-latest` (moves to 26.04 in Oct–Nov 2026) or unpinned images | 🟡 | manual |
| 21 | Artifacts with default retention (often 90 days) for CI-only outputs | 🟡 | manual |
| 22 | Permissions without a comment explaining why; jobs/workflows without `name:` | 🟡 | zizmor pedantic |
| 23 | No Dependabot/Renovate for `github-actions` (SHA pins rot) | 🟡 | zizmor `dependabot-cooldown` |

## 2. Commands

```bash
# Lint: correctness (expressions, types, shellcheck on run:, runner labels, action inputs)
docker run --rm -v "$PWD":/repo -w /repo rhysd/actionlint:1.7.12 -color

# Security audit. --offline skips network audits; add --gh-token for impostor-commit,
# known-vulnerable-actions, stale-action-refs. --persona=pedantic for review-level noise.
docker run --rm -v "$PWD":/repo -w /repo ghcr.io/zizmorcore/zizmor:1.30.1 --offline .github/workflows
docker run --rm -e GH_TOKEN="$(gh auth token)" -v "$PWD":/repo -w /repo \
  ghcr.io/zizmorcore/zizmor:1.30.1 --persona=pedantic .github/workflows

# Pins
pinact run --check
```

actionlint 1.7.12 predates three 2026 keys and reports them as errors. These are false positives; GitHub accepted each one on real runs:
- `parallel:` / `background:` steps: `step must run script with "run" section or run action with "uses" section`
- `concurrency.queue`: `unexpected key "queue" for "concurrency" section`
- `cache-mode`: `unexpected key "cache-mode" for "job" section`

Everything else it reports is real.

### Measuring a run

```bash
R=owner/repo
gh run list -R $R -w ci.yml --limit 10 --json databaseId,conclusion,createdAt,updatedAt,event
gh run view <id> -R $R --json jobs --jq '.jobs[] | {name, conclusion, startedAt, completedAt,
  steps: [.steps[] | {name, startedAt, completedAt}]}'
gh cache list -R $R --sort size_in_bytes --limit 20   # what is taking the 10 GB
gh cache list -R $R --ref refs/pull/123/merge         # caches saved by a PR (usually waste)
```

Compute:
- **wall-clock**: `updatedAt − createdAt` of the run (what the developer waits for, including queueing);
- **job time**: Σ(`completedAt − startedAt`) over jobs that ran;
- **billable minutes**: Σ ceil(job seconds / 60) × runner multiplier (Linux 1, Windows ≈ 1.7, macOS ≈ 10, `ubuntu-slim` ⅓, arm64 ≈ 0.83);
- **dominant step**: the longest step per job. That is where the optimization goes.

Measure a **cold** run (after `gh cache delete --all -R $R`), a **warm** run (cache hit, no changes), and a **code-change** run (warm cache, one source file changed). Cold vs. warm shows what the cache is worth. Warm vs. code-change shows whether the cache survives normal commits.

## 3. Report format

1. 🔴 findings, each with the line, the attack or failure it enables, and the fix.
2. Cost/speed: a table with before → after for wall-clock, billable minutes and the dominant step, **measured** when you could run it and marked *estimated* otherwise.
3. The single highest-impact change, if the user only does one thing.
4. What you could not verify (secret names, branch protection settings, required checks, org policies).
