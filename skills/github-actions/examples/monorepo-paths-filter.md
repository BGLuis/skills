# Monorepo: run only what changed, keep one required check

The problem: with `on.pull_request.paths`, a PR that doesn't touch those paths never starts the workflow, its required check stays **Pending** forever, and the PR can't merge. (A *job* skipped by `if:` is different: it reports Success.) The fix is to always start the workflow, decide per job, and make **one aggregate job** the only required status check.

Ran on the bench repo (packages `node/`, `python/`, `go/`, `rust/`) on 2026-09-23, on push events. actionlint and zizmor: clean.

| Commit touched | Jobs that ran (job time) | Wall-clock |
|---|---|---|
| `node/` only | changes 9 s → node 7 s → ci-ok 8 s; **go skipped** | 71 s |
| `node/` and `go/` | changes 9 s → node 13 s + go 18 s → ci-ok 4 s | 61 s |

- `ci-ok` was green in both cases, so a skipped job counts as passing.
- **The gate costs wall-clock time**: each `needs:` hop waits for a new runner (about 10–20 s here). Three hops turned 24 s of work into 71 s wall-clock. It pays off when the skipped jobs are expensive (minutes of build/test per package). For two cheap packages, run everything in one job instead.
- `changes` and `ci-ok` run on `ubuntu-slim` (⅓ price). Both are API calls and a shell loop.

## Code

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

jobs:
  changes:
    name: changes
    runs-on: ubuntu-slim
    timeout-minutes: 5
    permissions:
      contents: read      # checkout on push events
      pull-requests: read # paths-filter lists PR files through the API
    outputs:
      packages: ${{ steps.filter.outputs.changes }}
    steps:
      # On pull_request, paths-filter uses the API and needs no checkout.
      - if: github.event_name == 'push'
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
          fetch-depth: 2
      - id: filter
        uses: dorny/paths-filter@ceb8a2b8f2d89434be7ff52d3de7ec3738c5cc9d # v4.0.3
        with:
          filters: |
            api:
              - 'packages/api/**'
              - 'packages/shared/**'
            web:
              - 'packages/web/**'
              - 'packages/shared/**'

  api:
    name: api
    needs: changes
    if: contains(fromJSON(needs.changes.outputs.packages), 'api')
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    permissions:
      contents: read # checkout
    defaults:
      run:
        working-directory: packages/api
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
          sparse-checkout: |
            packages/api
            packages/shared
      - uses: actions/setup-go@b7ad1dad31e06c5925ef5d2fc7ad053ef454303e # v7.0.0
        with:
          go-version-file: packages/api/go.mod
          cache-dependency-path: packages/api/go.sum
      - run: go test ./...

  web:
    name: web
    needs: changes
    if: contains(fromJSON(needs.changes.outputs.packages), 'web')
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    permissions:
      contents: read # checkout
    defaults:
      run:
        working-directory: packages/web
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
          sparse-checkout: |
            packages/web
            packages/shared
      - uses: actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0
        with:
          node-version-file: packages/web/.nvmrc
          cache: npm
          cache-dependency-path: packages/web/package-lock.json
      - run: npm ci --ignore-scripts --no-audit --no-fund
      - run: npm test

  # The ONLY required status check. always(): a failed dependency must not turn it into a (passing) skip.
  ci-ok:
    name: ci-ok
    if: always()
    needs: [changes, api, web]
    runs-on: ubuntu-slim
    timeout-minutes: 2
    permissions: {}
    steps:
      - env:
          RESULTS: ${{ join(needs.*.result, ' ') }}
        run: |
          echo "results: $RESULTS"
          for r in $RESULTS; do
            case "$r" in success|skipped) ;; *) exit 1 ;; esac
          done
```

## Why each piece is there

- **`if: always()` on `ci-ok`**: without it, a failed `api` job makes `ci-ok` **skipped**, and a skipped job reports **Success** to branch protection ([docs](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-jobs-with-conditions)). A broken PR would merge. With `always()` it runs every time. The shell loop fails on `failure` and `cancelled`, and passes on `success` and `skipped`.
- **`contains(fromJSON(...), 'api')`**, not `contains(needs.changes.outputs.packages, 'api')`. The output is a JSON string, and `contains()` on a string does a substring match (`'api'` matches `"rapid"`). zizmor `unsound-contains` flags that.
- **Shared code in both filters** (`packages/shared/**`), so a change there tests every consumer.
- **`sparse-checkout`** writes only the package and its shared code to disk. On a large monorepo this is the checkout speedup (see `references/checkout-and-git.md`). On a tiny repo it's neutral.
- **`fetch-depth: 2` on push**: paths-filter diffs against the previous commit. On `pull_request` it calls the API instead, so there's no checkout at all.
- A merge queue (`merge_group`) needs `merge_group:` added to `on:`, and the filter needs a base (`base: ${{ github.event.merge_group.base_ref }}`), because there's no PR API to ask.
