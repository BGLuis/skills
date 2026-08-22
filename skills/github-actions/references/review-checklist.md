# Workflow Review Checklist

Work through in order. Stop and report anything in section 1 immediately — those are exploitable.

## 1. Security
- [ ] `permissions:` declared? Workflow-level default should be `{}` or `contents: read`.
- [ ] Any job holding `write` scopes it does not use?
- [ ] Third-party actions pinned to a SHA? (tag-pinned = mutable = supply-chain risk)
- [ ] `pull_request_target` present? If so, does it check out or run PR-head code? That is a repo takeover path.
- [ ] Any `${{ github.event.* }}` interpolated directly into a `run:` block? (command injection)
- [ ] Secrets echoed, passed to third-party actions, or exposed in artifacts/logs?
- [ ] Long-lived cloud credentials that OIDC could replace?
- [ ] `script` steps from `actions/github-script` handling untrusted input?

## 2. Correctness
- [ ] Triggers match intent; no accidental double-runs (`push` + `pull_request` on the same branch).
- [ ] `needs:` graph correct; reporting jobs use `if: always()`.
- [ ] Runner and language versions pinned where reproducibility matters.
- [ ] Does the workflow actually run the project's real test/build commands?
- [ ] Artifacts uploaded for post-mortem on failure.

## 3. Speed and cost
- [ ] `concurrency` with `cancel-in-progress` on PR workflows.
- [ ] Dependency cache present and keyed on the lockfile hash.
- [ ] `timeout-minutes` on every job.
- [ ] Cheap checks (lint, typecheck) gate the expensive matrix.
- [ ] `fetch-depth: 0` only where history is genuinely required.
- [ ] Path filters on monorepos.
- [ ] Redundant matrix combinations that test nothing new.

## Reporting
Quantify: "the test job re-downloads 400MB of dependencies on every run — no cache key", "9 of 12 jobs hold `contents: write` but only the release job pushes". Close with the single highest-impact fix.
