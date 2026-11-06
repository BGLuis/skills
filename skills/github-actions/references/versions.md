# Action versions and SHA pins

Resolved on **2026-11-06** with `gh api` (release tag → commit SHA). Versions go stale fast: **re-resolve before you write a workflow** if this table is more than a few weeks old.

## Runtime baseline

- Node 24 became the default for JavaScript actions on 2026-06-16, and since 2026-09-23 the runners no longer run Node 20. An action that declares `runs.using: node20` **does not fail**: the runner forces it onto Node 24 and logs `##[warning]Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24: actions/checkout@v4, actions/setup-python@v5` (observed on 2026-09-23). It usually works, but nobody tested that combination, and `ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION=true` is only a temporary escape hatch. Upgrade to the current majors. Checked with `gh api` on 2026-09-23: `checkout@v4`, `cache@v4`, `setup-node@v4`, `setup-python@v5`, `setup-go@v5` and `upload-artifact@v4` are all `node20`, while `checkout@v5` and `setup-node@v5` are already `node24`. Read `runs.using` in the action.yml at the pinned ref when in doubt.
- Every current JavaScript major needs **runner ≥ 2.327.1**. This matters on self-hosted runners and GHES. `checkout@v6+` needs ≥ 2.329.0 for authenticated git inside Docker container actions, and `uses: $/path` needs ≥ 2.336.0.
- Node 24 does not run on macOS ≤ 13.4 or ARM32 self-hosted runners.

## Current pins

| Action | Version | SHA | Notes |
|---|---|---|---|
| `actions/checkout` | v7.0.1 | `3d3c42e5aac5ba805825da76410c181273ba90b1` | v7 refuses fork-PR checkout under `pull_request_target`/`workflow_run` |
| `actions/cache` (also `/restore`, `/save`) | v6.1.0 | `55cc8345863c7cc4c66a329aec7e433d2d1c52a9` | `save-always` deprecated. Use the sub-actions |
| `actions/setup-node` | v7.1.0 | `949feb2413d6458794dcd2491c4babbbce0c15c1` | auto-cache only for npm with `packageManager` |
| `actions/setup-python` | v7.1.0 | `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` | `pip-install` input removed |
| `actions/setup-go` | v7.0.0 | `b7ad1dad31e06c5925ef5d2fc7ad053ef454303e` | cache on by default |
| `actions/setup-java` | v6.2.0 | `77dd5b2ce225ea11469928ac317850245a74ae78` | `cache-read-only` input |
| `actions/upload-artifact` | v7.0.2 | `cf430e030ddbb5b0abf93d22962f4752f3646cd9` | `archive: false` for a single unzipped file |
| `actions/download-artifact` | v8.0.2 | `9000827ccba6bdab643e8b6fd33ac0654aef8333` | fails on digest mismatch by default |
| `actions/github-script` | v9.0.0 | `3a2844b7e9c422d3c10d287c895573f7108da1b3` | `require('@actions/github')` removed; use the injected `getOctokit` |
| `actions/attest-build-provenance` | v4.2.2 | `4d101475d8b20a2381f78447822ac1eab6504dd8` | |
| `astral-sh/setup-uv` | v10.3.3 | `68559e99cc807c1eb7e9238fd43a15bba460eec2` | cache auto-off on release/tag/`pull_request_target`/`workflow_run` |
| `Swatinem/rust-cache` | v2.9.3 | `d1527c8f67ef9af357290475d4af4b0fab8f12e0` | |
| `pnpm/action-setup` | v6.1.1 | `73e46992e05b19abd31f2f3c20e0e7370d762115` | inputs use underscores (`run_install`) |
| `oven-sh/setup-bun` | v2.2.0 | `0c5077e51419868618aeaa5fe8019c62421857d6` | cache on by default (`no-cache: false`) |
| `docker/setup-buildx-action` | v4.4.1 | `f87e5991a6d7451dcb8d9637bfbc97413f497069` | |
| `docker/build-push-action` | v7.4.0 | `c3c9e263c25d99ce0380d002d59b67737d91b0dc` | |
| `docker/login-action` | v4.8.0 | `8aa5831fb8d48d8f76594c7ddde61ae58019f550` | |
| `docker/metadata-action` | v6.2.0 | `dc802804100637a589fabce1cb79ff13a1411302` | |
| `docker/setup-qemu-action` | v4.4.0 | `99012661954931238ded8c8b007157a8430204e1` | avoid when you can cross-compile |
| `dorny/paths-filter` | v4.0.3 | `ceb8a2b8f2d89434be7ff52d3de7ec3738c5cc9d` | |
| `step-security/harden-runner` | v2.22.3 | `46b06cea07f9e64621fdf066ba77ac6915163d43` | `egress-policy` defaults to `block` in `action.yml`. Always set it |
| `zizmorcore/zizmor-action` | v0.8.1 | `45d7276c9ca790aabd705e31ca99c6185c3e76dd` | composite action |
| `aws-actions/configure-aws-credentials` | v6.3.0 | `e1253824e5c10ff9df46874f81ed3ec929e19cfd` | |
| `pypa/gh-action-pypi-publish` | v1.14.3 | `7245906fb61fa33a13554f9d5fb856fe61758086` | trusted publishing. v1.14.3 fixes GHSA-5xjx-3w67-w9x9: do not stay below it |
| `reproducible-containers/buildkit-cache-dance` | v3.4.0 | `5422eac04292c961a382e0f584ea0f03ad9da723` | |

CLI tools: actionlint **1.7.12** (`rhysd/actionlint:1.7.12` image), zizmor **1.32.0** (`ghcr.io/zizmorcore/zizmor:1.32.0`).

## Pin format

```yaml
- uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
```

- Always pin the **full 40-character SHA** and add a `# vX.Y.Z` comment. Dependabot and Renovate update both. zizmor `ref-version-mismatch` flags a comment that does not match the SHA.
- Resolve a tag the same way the table above was built. `commits/<tag>` dereferences annotated tags to the commit:
  ```bash
  tag=$(gh api repos/actions/checkout/releases/latest --jq .tag_name)
  gh api repos/actions/checkout/commits/$tag --jq .sha
  ```
- Or let a tool do it: `pinact run` (suzuki-shunsuke/pinact) or `ratchet pin` (sethvargo/ratchet). In CI, use `pinact run --check` to fail when anything is unpinned.
- Pin container images (`container:`, `services:`, `docker://`) by `@sha256:` digest (zizmor `unpinned-images`).
