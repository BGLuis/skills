# Checkout and git

`actions/checkout` runs in every job. On large repos it is often the single largest fixed cost, and a pure waste when the job reads three directories.

Sources: [actions/checkout README](https://github.com/actions/checkout), [Depot: why checkout is slow](https://depot.dev/blog/why-organizations-have-slow-actions-checkout).

## Defaults (v7)

| Input | Default | Meaning |
|---|---|---|
| `fetch-depth` | `1` | shallow: only the triggering commit |
| `fetch-tags` | `false` | |
| `filter` | none | partial clone (`blob:none`, `tree:0`). **Overrides `sparse-checkout`** |
| `sparse-checkout` | none | only these paths in the working tree (cone mode) |
| `lfs` / `submodules` | `false` | |
| `persist-credentials` | **`true`** | set it to `false`, see `references/security.md` §5 |

## Choosing the clone shape

| Job needs | Use | Why |
|---|---|---|
| Build/test the current commit | defaults + `persist-credentials: false` | 1 commit, full tree |
| One package in a monorepo | `sparse-checkout: packages/api` (plus shared config files) | files outside the cone are never written. Depot measured 60 s → 2 s on a large monorepo with sparse + partial clone |
| Git history but not old file contents (changelog, `git log`, semantic-release, version from tags) | `fetch-depth: 0` + `filter: blob:none` | all commits and trees, no historic blobs |
| Only commit metadata (`git describe`, commit counts) | `fetch-depth: 0` + `filter: tree:0` | smallest full-history clone |
| A diff against the base branch | `fetch-depth: 0` + `filter: blob:none`, or on PRs skip the checkout and use the API (`dorny/paths-filter` does this) | |
| Push back to the repo | `persist-credentials: true` in **that job only**, with `contents: write` | |

- `fetch-depth: 0` **without** a filter downloads every version of every file ever committed. On a repo of any age that's the slow path. Never use it by default.
- A job that only calls an API, posts a comment or deploys an artifact doesn't need checkout at all.
- `lfs: true` downloads the LFS objects of the checked-out commit on every run, with no cache. Prefer `lfs: false` plus `git lfs pull --include=<only what the job needs>`, or cache `.git/lfs` with a key computed in a previous step from `git lfs ls-files -l`.
- On a tiny repo (the bench repo's checkout took 1–4 s) none of this matters. Optimize checkout only when the step's time in the run shows it matters.
