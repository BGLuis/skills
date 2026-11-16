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
| 9 | Actions targeting the deprecated Node 20 runtime (`checkout@v4`, `cache@v4`, `setup-node@v4`, `setup-python@v5`, `setup-go@v5`, `upload-artifact@v4`…), forced onto Node 24 | 🟠 | run log: `being forced to run on Node.js 24`; `references/versions.md` |
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
| 20 | Heavy jobs on `ubuntu-latest` (it became 26.04 in the 2026-10-19 → 2026-11-19 rollout) or unpinned images | 🟡 | manual |
| 21 | Artifacts with default retention (often 90 days) for CI-only outputs | 🟡 | manual |
| 22 | Permissions without a comment explaining why; jobs/workflows without `name:` | 🟡 | zizmor pedantic |
| 23 | No Dependabot/Renovate for `github-actions` (SHA pins rot) | 🟡 | zizmor `dependabot-cooldown` |
| 24 | Release-profile builds, signing, packaging, publishing or macOS/Windows cells on `pull_request`, or on every push/`workflow_run` of a branch when nobody consumes a build per commit | 🟠 | trigger × job table (`references/triggers.md` §5) |
| 25 | `on: [push, pull_request]` (or `push` without `branches:`): every same-repo PR commit runs twice | 🟠 | manual |
| 26 | No workflow lockfile where the repo could adopt one: the actions called *inside* third-party actions stay on mutable tags | 🟡 | `.github/workflows/actions.lock` missing; `gh actions-lock` |
| 27 | Build and signing in the same job: third-party build code runs with `id-token: write` | 🟠 | manual (`examples/release-oidc.md`) |
| 28 | Logic or `${{ }}` inside `parallel:` steps, which actionlint does not lint | 🟡 | manual (§2) |

## 2. Commands

```bash
# Lint: correctness (expressions, types, shellcheck on run:, runner labels, action inputs)
docker run --rm -v "$PWD":/repo -w /repo rhysd/actionlint:1.7.12 -color

# Security audit. The target is the repository root: `.github/workflows` alone leaves out
# composite actions (action.yml) and .github/dependabot.yml, so dependabot-cooldown never fires.
# --offline skips the network audits. With a token it also runs impostor-commit,
# known-vulnerable-actions, stale-action-refs, ref-confusion and ref-version-mismatch.
# --persona=pedantic for review-level noise.
docker run --rm -v "$PWD":/repo -w /repo ghcr.io/zizmorcore/zizmor:1.32.0 --offline .
docker run --rm -e GH_TOKEN="$(gh auth token)" -v "$PWD":/repo -w /repo \
  ghcr.io/zizmorcore/zizmor:1.32.0 --persona=pedantic .

# Pins
pinact run --check
```

actionlint 1.7.12 predates three 2026 keys and reports them as errors. These are false positives; GitHub accepted each one on real runs:
- `parallel:` / `background:` steps: `step must run script with "run" section or run action with "uses" section`
- `concurrency.queue`: `unexpected key "queue" for "concurrency" section`
- `cache-mode`: `unexpected key "cache-mode" for "job" section`

Everything else it reports is real. What it does **not** report matters too: it stops at the `parallel:` key, so the steps inside the group get no expression check, no shellcheck and no untrusted-input warning (tested: a `${{ github.event.pull_request.title }}` in a `run:` inside `parallel:` passes). zizmor 1.32.0 does audit those steps and warns that its support for them is experimental. Review them by hand.

### Measuring a run

```bash
R=owner/repo
gh run list -R $R -w ci.yml --limit 10 --json databaseId,conclusion,createdAt,updatedAt,event
python3 scripts/billable_minutes.py $R <id> <id> <id>   # the four figures below, and medians from 3 runs
gh cache list -R $R --sort size_in_bytes --limit 20   # what is taking the 10 GB
gh cache list -R $R --ref refs/pull/123/merge         # caches saved by a PR (usually waste)
```

`scripts/billable_minutes.py` reads the runs through the API and computes (do not do this arithmetic by hand):
- **wall-clock**: `updatedAt − createdAt` of the run (what the developer waits for, including queueing);
- **job time**: Σ(`completedAt − startedAt`) over jobs that ran;
- **billable minutes**: Σ ceil(job seconds / 60) × runner multiplier (Linux 1, Windows ≈ 1.7, macOS ≈ 10, `ubuntu-slim` ⅓, arm64 ≈ 0.83). Jobs on larger or self-hosted runners have no rate in the script and are reported apart;
- **dominant step**: the longest step per job. That is where the optimization goes.

Measure a **cold** run (after `gh cache delete --all -R $R`), a **warm** run (cache hit, no changes), and a **code-change** run (warm cache, one source file changed). Cold vs. warm shows what the cache is worth. Warm vs. code-change shows whether the cache survives normal commits.

## 3. Report format

1. 🔴 findings, each with the line, the attack or failure it enables, and the fix.
2. For projects that build binaries or packages, or with several triggers: the trigger × job table from `references/triggers.md` §5 (runs/month × billable minutes × multiplier), and the row with the most minutes per month.
3. Cost/speed: a table with before → after for wall-clock, billable minutes and the dominant step, **measured** when you could run it and marked *estimated* otherwise.
4. The single highest-impact change, if the user only does one thing.
5. What you could not verify (secret names, branch protection settings, required checks, org policies).
