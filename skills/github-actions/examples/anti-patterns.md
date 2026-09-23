# Anti-patterns

Never produce these. Each one comes with what it costs and the fix. The "Detected by" column shows which tool catches it, so a review can cite the tool output.

| # | Anti-pattern | Cost | Fix | Detected by |
|---|---|---|---|---|
| 1 | `run: echo "${{ github.event.pull_request.title }}"` | command injection | pass it through `env:`, reference `"$TITLE"` | zizmor `template-injection` |
| 2 | `pull_request_target` + checkout of `github.event.pull_request.head.sha` | repo takeover (secrets, write token) | `pull_request` + `workflow_run` split (`pr-privileged-split.md`) | zizmor `dangerous-triggers`, Scorecard |
| 3 | No `permissions:` block | default token may be read/write on everything | `permissions: {}` + per-job grants | zizmor `excessive-permissions` |
| 4 | `uses: some/action@v2` | mutable tag, supply chain (tj-actions, 2025) | full SHA + `# vX.Y.Z` + Dependabot cooldown | zizmor `unpinned-uses` |
| 5 | Checkout with default `persist-credentials` + `upload-artifact` of the workspace | token leaks in the artifact | `persist-credentials: false`, upload only build outputs | zizmor `artipacked` |
| 6 | `secrets: inherit` / `${{ toJSON(secrets) }}` | every secret exposed to the callee or logs | pass named secrets | zizmor `secrets-inherit`, `overprovisioned-secrets` |
| 7 | `AWS_SECRET_ACCESS_KEY` in repo secrets | long-lived key, broad blast radius | OIDC role + `id-token: write` on one job | manual |
| 8 | Cache restore in a release job | cache poisoning into published artifacts | no cache in release/publish jobs | zizmor `cache-poisoning` |
| 9 | `on: pull_request: paths: [...]` on a **required** check | PRs that don't touch those paths can never merge (check stays pending) | job-level `paths-filter` + always-run aggregate job | manual |
| 10 | `cancel-in-progress: true` with `group: ${{ github.workflow }}` only | a push to any branch cancels the others; main deploys get cancelled | group on `github.ref`; cancel only on `pull_request` | zizmor `concurrency-limits` (partial) |
| 11 | lint / typecheck / test / build as 4 jobs, each re-running checkout + setup + install | 4× setup time and 4 billable minutes for ~1 minute of work | one job; `parallel:` for the independent checks | measure |
| 12 | Test matrix `[22, 24, 26] × [ubuntu, windows, macos]` on every PR | 9 VMs, macOS at 10× price | ship version on Linux for PRs, full matrix on main/nightly | manual |
| 13 | No `timeout-minutes` | a hang burns 6 h | 2–3× the normal duration | manual |
| 14 | `fetch-depth: 0` "just in case" | downloads all history, slow on old repos | default depth; `filter: blob:none` when history is needed | step time |
| 15 | Project in a subdirectory, `setup-go` / `setup-node` without `cache-dependency-path` | cache silently never hits (warning only) | `cache-dependency-path: <dir>/go.sum` | step log |
| 16 | `pip install uv` + `setup-python` in every job | redundant downloads, no cache | `astral-sh/setup-uv` (installs Python, caches) | zizmor `superfluous-actions` (partial) |
| 17 | `actions/cache` saving on every PR | PR-scoped caches nobody can reuse, evicting main's | save only on the default branch | `gh cache list` |
| 18 | `actions/checkout@v4`, `actions/cache@v4`, `setup-node@v4` | Node 20 runtime removed 2026-09-23, so the run fails | current majors (`references/versions.md`) | run log |
| 19 | QEMU (`setup-qemu-action`) for multi-arch when the language cross-compiles | every `RUN` emulated, several times slower | `FROM --platform=$BUILDPLATFORM` + `GOOS/GOARCH`, or native `ubuntu-24.04-arm` | measure (`docker-build-push.md`) |
| 20 | `runs-on: ubuntu-latest` for toolchain-sensitive builds | image changes under you (→ 26.04, Oct–Nov 2026) | `ubuntu-24.04` | manual |
| 21 | `if: github.actor == 'dependabot[bot]'` to grant privileges | spoofable in some flows | check `github.event.pull_request.user.login` and the event | zizmor `bot-conditions` |
| 22 | Self-hosted runner on a public repo | any fork PR runs code on your machine | GitHub-hosted runners; self-hosted only for private repos with ephemeral runners | zizmor `self-hosted-runner` |

## The naive workflow the bench started from

Each of the `*-naive.yml` workflows measured in `examples/*-ci.md` uses #4, #3, #11, #13 and #20 together, and most also have #14 or #15. That's the typical shape of a first CI file, and of what an LLM produces without this skill:

```yaml
name: ci
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with: { fetch-depth: 0 }
      - uses: actions/setup-node@v7
        with: { node-version: 24 }
      - run: npm install
      - run: npm run lint
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node: [22, 24, 26]
    steps:
      - uses: actions/checkout@v7
        with: { fetch-depth: 0 }
      - uses: actions/setup-node@v7
        with: { node-version: "${{ matrix.node }}" }
      - run: npm install
      - run: npm test
```

zizmor 1.30.1 (`--offline`, regular persona) on this file: 9 findings. `unpinned-uses` ×4 (high), `excessive-permissions` ×3 (medium), `artipacked` ×2 (low). The concurrency, timeout, job-count and matrix problems are invisible to linters, so they need a review and a measurement. `on: [push, pull_request]` also runs every PR commit twice for branches in the same repo.
