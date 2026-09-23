# Caching

A cache is worth what it saves minus what it costs to restore and save. Restores run at roughly 100–150 MB/s ([Depot](https://depot.dev/blog/github-actions-cache); [RunsOn](https://runs-on.com/benchmarks/github-actions-cache-performance/) measured 78–91 s to save and restore 4 GB). A multi-GB cache can be slower than downloading the packages again. **Measure the restore step and the post-save step, not just the job total.**

Sources: [Dependency caching reference](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching), [actions/cache](https://github.com/actions/cache), [Actions limits](https://docs.github.com/en/actions/reference/limits).

## 1. Rules of the platform

| Rule | Consequence |
|---|---|
| 10 GB per repo by default (paid plans can raise it, $0.07/GB-month above 10 GB); LRU eviction, runs hourly | Too many keys (per-PR, per-matrix-cell) evict main's useful cache |
| Unused for 7 days → deleted | Weekly-only workflows start cold |
| A run can restore caches from **its own branch, the default branch, and (for PRs) the base branch**; never from sibling or child branches | PRs benefit from main's cache for free. Main never sees PR caches |
| PR caches are scoped to `refs/pull/N/merge` | Saving on PRs makes one private copy per PR that nobody else can use. **Save on the default branch only** |
| Only `push`, `schedule`, `workflow_dispatch`, `repository_dispatch` (and a few others) can write default-branch caches | `merge_group` and PR runs can't feed main |
| Keys are immutable: an existing key is never overwritten | Include the lockfile hash in the key. A static key freezes forever |
| 200 uploads/min per repo | Wide matrices that all save can hit it |
| Key ≤ 512 characters | |

### `cache-mode`: least privilege for the cache (2026)

The cache has its own permission, set at workflow or job level and enforced with scoped cache tokens:

| `cache-mode` | Restore | Save |
|---|---|---|
| `write` | ✓ | ✓ |
| `read` | ✓ | ✗ |
| `write-only` | ✗ | ✓ |
| `none` | ✗ | ✗ |

- Default when omitted: `write` for trusted triggers (`push`, `schedule`, `workflow_dispatch`, `repository_dispatch`, …), and **`read`** for low-trust ones (`pull_request_target`, `issue_comment`, `workflow_run`, …). `pull_request` caches are PR-scoped anyway.
- **Never declare `write`/`write-only` on a low-trust trigger.** It re-opens cache poisoning.
- `cache-mode: none` on release/publish jobs guarantees no cache is restored, whatever the actions do.
- `cache-mode: read` on the job that calls a reusable workflow caps what the callee can request. A callee asking for more fails validation.
- Measured on a job with `cache-mode: read` (the log shows `Cache mode: read` under *Set up job*):
  - `actions/cache/save` logs `Failed to save: … cache write denied: token has no writable scopes` as a **warning**, and the job continues.
  - `docker/build-push-action` with `cache-to: type=gha` **fails the build** (`error writing layer blob: failed to reserve cache`) unless `ignore-error=true` is set.
  - `$ACTIONS_CACHE_MODE` was empty inside `run:` steps. Don't branch on it in scripts.
- actionlint 1.7.12 doesn't know `cache-mode` yet (the same kind of false positive as `parallel:`).

## 2. Prefer the setup action's built-in cache

Built-in caches key on the lockfile and cache the **download cache**, not `node_modules`/`.venv`, which is what you want. They are portable across dependency changes.

| Stack | Action and input | Default | Key |
|---|---|---|---|
| npm | `setup-node` `cache: npm` | **auto-on only** when `package.json` at the root has `packageManager: npm@…`. Otherwise off | `package-lock.json` |
| pnpm | `pnpm/action-setup` `cache: true`, **or** `setup-node` `cache: pnpm` (not both) | off | `pnpm-lock.yaml` |
| yarn | `setup-node` `cache: yarn` | off | `yarn.lock` |
| bun | `oven-sh/setup-bun` | **on** (`no-cache: false`) | `bun.lock` |
| uv | `astral-sh/setup-uv` `enable-cache: true` + `prune-cache: true` | `auto`: on for hosted runners, **off** on release/tag/`pull_request_target`/`workflow_run` | `uv.lock`, `pyproject.toml`, requirements files |
| pip / poetry / pipenv | `setup-python` `cache: pip` | off | requirements / `poetry.lock` |
| Go | `setup-go` | **on** | `go.mod`/`go.sum` **at the repo root** |
| Java | `setup-java` `cache: maven\|gradle\|sbt` + `cache-read-only` | off | build files |
| Rust | `Swatinem/rust-cache` after the toolchain | on (saves `~/.cargo` + `target`) | `Cargo.lock`, toolchain, job |
| Docker | `docker/build-push-action` `cache-from/to: type=gha,scope=<image>` | off | layer graph |

### Pitfalls measured on the bench repo

- **Subdirectory projects silently lose the cache.** `setup-go` looks for its dependency file at the repo root. With the module in `go/` it logs `Restore cache failed: Dependencies file is not found … Supported file pattern: go.mod` as a *warning*, the job stays green, and nothing is ever cached. setup-node's auto-cache reads the root `package.json`. Always set `cache-dependency-path: go/go.sum` (or `node/package-lock.json`), and set `working-directory` for setup-uv.
- **`pip install uv` in every job** is a tool download the setup action caches for you. `astral-sh/setup-uv` also installs Python (`cache-python: true`), so `setup-python` is superfluous (zizmor `superfluous-actions`).
- `uv` caches the wheels it builds and re-downloads the rest. `prune-cache: true` runs `uv cache prune --ci` before saving, which keeps the cache small. Measured: see `examples/python-uv-ci.md`.

## 3. Save only on the default branch

With built-in caches, gate saving where the action supports it:

```yaml
- uses: Swatinem/rust-cache@6323deb102c322ba6fcbdcafc7e3dddab59af2b6 # v2.9.2
  with:
    save-if: ${{ github.ref == 'refs/heads/main' }}

- uses: actions/setup-java@de7274f081f381c8f8158605e0321c36c376e2e6 # v6.0.1
  with:
    distribution: temurin
    java-version: '25'
    cache: gradle
    cache-read-only: ${{ github.ref != 'refs/heads/main' }}
```

For anything else, split `actions/cache` into restore and save. The combined action saves on every successful run, including PRs. The split also saves after a failed test run, so the next attempt starts warm (`save-always` is deprecated and broken):

```yaml
- id: cache
  uses: actions/cache/restore@55cc8345863c7cc4c66a329aec7e433d2d1c52a9 # v6.1.0
  with:
    path: ~/.cache/tool
    key: tool-${{ runner.os }}-${{ runner.arch }}-${{ hashFiles('**/tool.lock') }}
    restore-keys: tool-${{ runner.os }}-${{ runner.arch }}-

- run: make test

- if: always() && steps.cache.outputs.cache-hit != 'true' && github.ref == 'refs/heads/main'
  uses: actions/cache/save@55cc8345863c7cc4c66a329aec7e433d2d1c52a9 # v6.1.0
  with:
    path: ~/.cache/tool
    key: ${{ steps.cache.outputs.cache-primary-key }}
```

- Put `runner.os` **and `runner.arch`** in the key. x64 and arm64 caches are not interchangeable.
- `restore-keys` gives a partial hit after a lockfile change. The package manager then only fetches the delta.
- `lookup-only: true` checks whether a key exists without downloading it. Use it to skip a whole "warm the cache" job.
- `fail-on-cache-miss: true` is for jobs that must consume what an earlier job produced.

## 4. When not to cache

- **Release, publish and privileged jobs** (`pull_request_target`, `workflow_run`): cache poisoning. Set `cache-mode: none` on those jobs. See `references/security.md` §3.
- **Tiny dependency sets** (< ~50 MB): the round trip to the cache service costs about as much as the registry download. Measure it.
- **`node_modules` or `.venv` directly**: they are bound to the exact runtime version and OS. Cache the package manager's store and let `npm ci` / `uv sync` link from it.
- **Build outputs between jobs of the same run**: those are artifacts (`upload-artifact`/`download-artifact`), not caches.

## 5. Docker layer cache

Covered in detail by the `docker-optimizer` skill (`references/ci-cache.md`). The workflow side is:

```yaml
- uses: docker/setup-buildx-action@f87e5991a6d7451dcb8d9637bfbc97413f497069 # v4.4.1
- uses: docker/build-push-action@c3c9e263c25d99ce0380d002d59b67737d91b0dc # v7.4.0
  with:
    context: .
    cache-from: type=gha,scope=api
    cache-to: ${{ github.ref == 'refs/heads/main' && 'type=gha,scope=api,mode=max,ignore-error=true' || '' }}
```

- One `scope` per image. Two images sharing the default scope overwrite each other.
- `mode=max` also exports intermediate stages. **That includes the builder base image layers.** Measured on the Go bench image: about 300 MB in the cache for a 10 MB final image. That's still a good trade when builds are slow, but it eats into the 10 GB budget. Use `mode=min` when only the final stage matters.
- `RUN --mount=type=cache` directories are **not** exported by `type=gha`. Persist them with `reproducible-containers/buildkit-cache-dance`, or better, make the dependency layer cacheable as a layer.
