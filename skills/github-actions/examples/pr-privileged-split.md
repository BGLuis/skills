# PR feedback that needs a write token: split the workflow in two

Use this when a PR workflow has to **comment, label, upload a preview or report coverage** for PRs from forks. A fork PR's `pull_request` run gets a read-only token and no secrets, and `pull_request_target` running PR code is a repo takeover. The safe shape splits the work in two:

1. `pull_request` (unprivileged): builds and tests the untrusted code and uploads **data** as an artifact.
2. `workflow_run` (privileged): runs the **default-branch** version of its own file, never checks out PR code, downloads the artifact, validates it as data and does the write.

Validated: zizmor 1.32.0 reports nothing, and actionlint 1.7.12 flags only the newer `cache-mode` key (a false positive, see `references/review-checklist.md`). The head-commit check and the concurrency group were added later and only linted. `workflow_run` is always flagged by zizmor `dangerous-triggers`; it is silenced with an inline `# zizmor: ignore[...]` **that states why**, which is the reviewable way to accept a finding.

## 1. Unprivileged: `.github/workflows/pr-test.yml`

```yaml
name: pr-test
on:
  pull_request:

permissions: {}

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    name: test
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    permissions:
      contents: read # checkout
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0
        with:
          node-version-file: .nvmrc
          cache: npm
      - run: npm ci --ignore-scripts --no-audit --no-fund
      - run: npx vitest run --coverage --coverage.reporter=json-summary
      - name: Write the report as plain data
        env:
          PR_NUMBER: ${{ github.event.pull_request.number }}
        run: |
          mkdir -p report
          jq --argjson pr "$PR_NUMBER" '{pr: $pr, lines: .total.lines.pct}' \
            coverage/coverage-summary.json > report/report.json
      - uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
        with:
          name: pr-report
          path: report/report.json
          retention-days: 1
          if-no-files-found: error
```

## 2. Privileged: `.github/workflows/pr-comment.yml`

```yaml
name: pr-comment
on: # zizmor: ignore[dangerous-triggers] never checks out or executes PR content
  workflow_run:
    workflows: [pr-test]
    types: [completed]

permissions: {}

concurrency:
  # Repository + branch: two forks that both use `patch-1` must not cancel each other.
  group: ${{ github.workflow }}-${{ github.event.workflow_run.head_repository.full_name }}-${{ github.event.workflow_run.head_branch }}
  cancel-in-progress: true

jobs:
  comment:
    name: comment
    if: github.event.workflow_run.event == 'pull_request' && github.event.workflow_run.conclusion == 'success'
    runs-on: ubuntu-slim
    timeout-minutes: 5
    cache-mode: none # privileged trigger: never restore a cache
    permissions:
      actions: read        # download the artifact from the triggering run
      pull-requests: write # post the comment
    steps:
      # No checkout: nothing from the PR is ever executed here.
      - uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
        with:
          name: pr-report
          path: ${{ runner.temp }}/pr-report
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ github.token }}
      - name: Validate and comment
        env:
          GH_TOKEN: ${{ github.token }}
          GH_REPO: ${{ github.repository }}
          REPORT: ${{ runner.temp }}/pr-report/report.json
          HEAD_SHA: ${{ github.event.workflow_run.head_sha }}
        run: |
          pr=$(jq -r '.pr' "$REPORT")
          lines=$(jq -r '.lines' "$REPORT")
          # The artifact is attacker-controlled: accept only the exact shapes we expect.
          [[ "$pr" =~ ^[0-9]+$ ]] || { echo "bad pr number"; exit 1; }
          [[ "$lines" =~ ^[0-9]+(\.[0-9]+)?$ ]] || { echo "bad coverage value"; exit 1; }
          # A well-formed number can still be someone else's PR. Comment only on the PR whose head this run tested.
          head=$(gh pr view "$pr" --json headRefOid --jq .headRefOid)
          [[ "$head" == "$HEAD_SHA" ]] || { echo "::notice::PR #$pr is not at $HEAD_SHA, not commenting"; exit 0; }
          gh pr comment "$pr" --body "Line coverage: ${lines}%"
```

## Why each line is there

- **No checkout in the privileged job.** Even though checkout v7 refuses fork code under `workflow_run`, the safest privileged job has nothing to execute.
- **Artifact into `$RUNNER_TEMP`, never the workspace.** A crafted artifact can't then overwrite scripts or config that a later step runs.
- **Validate with strict regexes before use**, then check ownership. The PR number from the artifact decides *where* the comment goes, and a regex only proves it is a number: a fork could name any other PR. The job compares that PR's head commit with `workflow_run.head_sha` (which comes from GitHub, not from the artifact) and stays silent when they differ, which also covers a run made stale by a newer push. Don't trust `workflow_run.pull_requests[]` instead; it is empty for fork PRs.
- **The concurrency group includes the head repository.** `head_branch` alone is chosen by the contributor, and two forks with the same branch name would cancel each other's comment.
- **Values reach the shell through `env:` and `jq`**, never through `${{ }}` in `run:`.
- **`ubuntu-slim`**: the job is an API call, so the 1-vCPU runner costs ⅓ of the standard one.
- **`retention-days: 1`**: the artifact only needs to live until the second workflow consumes it.
- **`cache-mode: none`**: `workflow_run` defaults to `cache-mode: read`, so any cache action added later would restore main's cache into a job with a write token. `none` closes that at the token level.
- Only `actions: read` and `pull-requests: write`. No `contents: write`, no secrets.
