# Python (uv) CI

Measured on GitHub-hosted public runners (`ubuntu-24.04`) on 2026-09-23, using a FastAPI + pydantic + numpy + pandas app with ruff and pytest, locked with `uv.lock`. The naive workflow: separate lint and test-matrix [3.13, 3.14] jobs, each doing `setup-python` → `pip install uv` → `uv sync`, with no cache. actionlint and zizmor: clean.

Format: wall-clock / Σ job time / billable minutes.

| Run | Naive (3 jobs) | This file (1 job) |
|---|---|---|
| Cold | 20 s / 36 s / **3** | 16 s / 13 s / **1** |
| Warm (median of 2) | 19 s / 36 s / **3** | 17 s / 12 s / **1** |
| Code change | 19 s / 37 s / 3 | 13 s / 10 s / 1 |
| Cache stored | — | 33 MB (with `prune-cache`) |

## Why it looks like this

1. **`astral-sh/setup-uv` replaces `setup-python` + `pip install uv`.** It installs a checksummed uv binary. `uv sync` then installs the interpreter from `.python-version` itself, and `cache-python: true` caches it. `setup-python` becomes a superfluous action.
2. **`enable-cache: true` + `prune-cache: true`.** uv's cache is keyed on `uv.lock`. `prune-cache` runs `uv cache prune --ci` before saving: it drops the wheels that were only downloaded (fast to fetch again) and keeps the ones built from source (slow to rebuild). That keeps the cache small, so the restore stays cheap.
3. **`uv sync --locked`** fails if `uv.lock` is out of date with `pyproject.toml`, instead of silently re-resolving in CI.
4. **One job.** Three jobs of 10–15 s bill 3 minutes. One job with the same checks bills 1. On main, add the 3.14 cell with a matrix expression as in `node-ci.md` if you support several versions.
5. On `release`, tag-push, `pull_request_target` and `workflow_run` events, setup-uv v10 **turns its cache off automatically** (cache poisoning). On `merge_group` it restores but doesn't save.

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
    name: ci
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    permissions:
      contents: read # checkout
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: astral-sh/setup-uv@c18668ad3cf93ea998bef934396af7bb5c839dc7 # v10.2.0
        with:
          enable-cache: true
          prune-cache: true
          cache-python: true
      - run: uv sync --locked
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run pytest -q
```

- Subdirectory project: set `working-directory: <dir>` on setup-uv (so it finds `.python-version` and `uv.lock`), `cache-dependency-glob: <dir>/uv.lock`, and `defaults.run.working-directory`. The bench workflow (`python-opt.yml`) is this file with those changes and without the format check.
- Slow test suite: `uv add --dev pytest-xdist` and `pytest -n auto` use every vCPU (4 on public runners, 2 on private). Shard across jobs only when the suite runs for several minutes.
- Poetry or pip projects without uv: `setup-python` with `cache: poetry|pip` and `cache-dependency-path`.
