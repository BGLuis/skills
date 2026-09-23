# Node.js (TypeScript) CI

Measured on GitHub-hosted public runners (`ubuntu-24.04`, 4 vCPU) on 2026-09-23, using a Fastify + zod app with eslint, tsc and vitest (106 MB `node_modules`). The naive workflow is the usual first CI file: lint / typecheck / test matrix [22, 24, 26] / build as separate jobs, `npm install`, `ubuntu-latest`, `fetch-depth: 0`, no cache, no permissions, no timeout. actionlint and zizmor: clean (see the parallel-steps note).

Format: wall-clock / Σ job time / billable minutes.

| Run | Naive (6 jobs) | This file (1 job) |
|---|---|---|
| Cold (no cache) | 35 s / 77 s / **6** | 20 s / 16 s / **1** |
| Warm (median of 2) | 32 s / 66 s / **6** | 19 s / 15 s / **1** |
| Code change, warm cache | 36 s / 69 s / 6 | 51 s / 48 s / 1 ⚠ |

⚠ Runner noise: the steps of that run add up to 15 s. The rest was the job waiting on the host before the first step. Identical runs varied from 10 s to 48 s, so compare medians of ≥ 3 runs.

On other runners (same job, 2 runs each): `ubuntu-24.04-arm` 11–16 s of job time at 83% of the x64 price. `ubuntu-slim` 55–109 s, at ⅓ of the price per minute, but 5–7× slower. On a private repo it is still cheaper per run (1–2 min × $0.002 vs 1 min × $0.006), but the developer waits up to a minute longer. Use slim for gatekeeping jobs, not builds.

## Why it looks like this

1. **One job instead of six.** Every job rounds up to a billable minute and repeats checkout, Node install and `npm install` (2–5 s each, per job). Six jobs doing 1 minute of total work bill 6 minutes, and one job doing the same work bills 1.
2. **`parallel:` for the independent checks.** lint, typecheck and test are single-threaded and don't depend on each other, so they share the 4 vCPUs (2 on private repos). Measured: the group finished in 2 s, while its three steps add up to about 5 s.
3. **The matrix runs only on main**, via an expression. PRs test the version you ship (24), which removes 2 of the 3 test VMs on every PR push. Keep the PR value in sync with `.nvmrc`. The bench measured the single-version job; each extra matrix cell on main adds one job like it.
4. **`cache: npm` + `cache-dependency-path`**: caches `~/.npm` keyed on the lockfile. On this small dependency set, warm `npm ci` took 2–5 s either way. The cache matters more as `node_modules` grows, and it keeps working when the registry is slow. Automatic caching only kicks in when the **root** `package.json` has `packageManager: npm@…`, so set `cache:` explicitly.
5. **`npm ci --ignore-scripts --no-audit --no-fund`**: lockfile-exact, no install scripts from dependencies (supply chain), and no network round-trips for audit and fund messages.
6. **Artifacts**: `retention-days: 3` instead of the repo default (often 90). `if-no-files-found: error` catches a build that silently produced nothing.

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
  ci:
    name: ci (node ${{ matrix.node }})
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    permissions:
      contents: read # checkout
    strategy:
      matrix:
        # PRs: the version you ship. main: the whole supported range.
        node: ${{ github.event_name == 'pull_request' && fromJSON('["24"]') || fromJSON('["22", "24", "26"]') }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0
        with:
          node-version: ${{ matrix.node }}
          cache: npm
      - run: npm ci --ignore-scripts --no-audit --no-fund
      - parallel:
          - run: npm run lint
          - run: npm run typecheck
          - run: npm test
      - run: npm run build
      - if: matrix.node == '24'
        uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
        with:
          name: dist
          path: dist/
          retention-days: 3
          if-no-files-found: error
```

- actionlint 1.7.12 flags `parallel:` as `step must run script with "run" section…`. That's a false positive, because the syntax is newer than the linter. GitHub accepted and ran it. To support linters that predate it, replace the group with three sequential steps; that costs about 3 s on this project.
- For a project in a subdirectory, add `defaults.run.working-directory: <dir>`, `cache-dependency-path: <dir>/package-lock.json`, the `.nvmrc` path, and `working-directory` on each step inside `parallel:`. The bench workflow (`node-opt.yml`) is this file with those changes and no matrix.
- pnpm: add `pnpm/action-setup` (with `cache: true`) **before** setup-node and drop `cache: npm` from setup-node. Caching in both wastes a save. Bun: `oven-sh/setup-bun` caches by default.
