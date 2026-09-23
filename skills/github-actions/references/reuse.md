# Reuse: reusable workflows and composite actions

Source: [Reusing workflow configurations](https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations).

## Which one

| You are factoring out | Use | Runs as |
|---|---|---|
| Steps inside one job (setup + install + cache) | **composite action** (`action.yml` with `runs.using: composite`) | steps inside the caller's job, on the caller's runner, with the caller's token |
| Whole jobs (a standard CI or deploy pipeline shared across repos) | **reusable workflow** (`on: workflow_call`) | separate jobs, each with its own runner and permissions |

A composite action adds **no** runner time. A reusable workflow adds at least one job, so it pays the per-job minute rounding and setup cost again (`references/performance-cost.md` §1).

## Composite action in the same repo

```yaml
# .github/actions/setup-node-deps/action.yml
name: Setup Node deps
description: Node from .nvmrc, npm cache, clean install
runs:
  using: composite
  steps:
    - uses: actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0
      with:
        node-version-file: .nvmrc
        cache: npm
    - run: npm ci --ignore-scripts --no-audit --no-fund
      shell: bash
```

```yaml
steps:
  - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
    with:
      persist-credentials: false
  - uses: ./.github/actions/setup-node-deps
```

- Every `run:` in a composite action needs an explicit `shell:`.
- `./path` needs the repo checked out first. **`uses: $/.github/actions/setup-node-deps`** (2026-07, runner ≥ 2.336.0) resolves the action at the exact commit that is running, **without a checkout**, and satisfies an org "require SHA pinning" policy. Plain `./` counts as unpinned under that policy. zizmor `self-repository` suggests the `$/` form.
- Composite actions can't use `parallel:` or `background:` steps internally, but a composite action can itself run as a background step.

## Reusable workflow

```yaml
# .github/workflows/ci-node.yml (callee)
name: ci-node
on:
  workflow_call:
    inputs:
      node-version-file: { type: string, default: .nvmrc }
    secrets:
      NPM_TOKEN: { required: false }

permissions: {}

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
      - uses: actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0
        with:
          node-version-file: ${{ inputs.node-version-file }}
          cache: npm
      - run: npm ci --ignore-scripts --no-audit --no-fund
      - run: npm test
```

```yaml
# caller
jobs:
  ci:
    permissions:
      contents: read # passed down; the callee can only reduce it
    uses: my-org/workflows/.github/workflows/ci-node.yml@<sha> # v3.2.0
    secrets:
      NPM_TOKEN: ${{ secrets.NPM_TOKEN }} # explicit, never `secrets: inherit`
```

- **Pin cross-repo reusable workflows by SHA**, like actions.
- Declare the contract: typed `inputs`, the `secrets` the callee needs, and `outputs`. `env` is **not** passed in either direction.
- The caller's `permissions` are the ceiling. The callee can only reduce them.
- `secrets: inherit` hands over every secret (zizmor `secrets-inherit`). Pass them by name.
- Limits: 10 levels of nesting, and 50 unique reusable workflows per workflow file.
- Inside a callee, `job.workflow_ref`, `job.workflow_sha`, `job.workflow_repository` and `job.workflow_file_path` (2026-09) identify the callee itself. `github.workflow_ref` identifies the caller.
