# Action versions and SHA pins

Resolved on **2026-09-23** with `gh api` (release tag → commit SHA). Versions go stale fast: **re-resolve before you write a workflow** if this table is more than a few weeks old.

## Runtime baseline

- Node 24 became the default for JavaScript actions on 2026-06-16, and Node 20 is being removed from the runners (announced for 2026-09-23). An action that declares `runs.using: node20` **does not fail**: the runner forces it onto Node 24 and logs `##[warning]Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24: actions/checkout@v4, actions/setup-python@v5` (observed on 2026-09-23). It usually works, but nobody tested that combination, and `ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION=true` is only a temporary escape hatch. Upgrade to the current majors. Checked with `gh api` on 2026-09-23: `checkout@v4`, `cache@v4`, `setup-node@v4`, `setup-python@v5`, `setup-go@v5` and `upload-artifact@v4` are all `node20`, while `checkout@v5` and `setup-node@v5` are already `node24`. Read `runs.using` in the action.yml at the pinned ref when in doubt.
- Every current JavaScript major needs **runner ≥ 2.327.1**. This matters on self-hosted runners and GHES. `checkout@v6+` needs ≥ 2.329.0 for authenticated git inside Docker container actions, and `uses: $/path` needs ≥ 2.336.0.
- Node 24 does not run on macOS ≤ 13.4 or ARM32 self-hosted runners.

## Current pins

| Action | Version | SHA | Notes |
|---|---|---|---|
| `actions/checkout` | v7.0.1 | `3d3c42e5aac5ba805825da76410c181273ba90b1` | v7 refuses fork-PR checkout under `pull_request_target`/`workflow_run` |
| `actions/cache` (also `/restore`, `/save`) | v6.1.0 | `55cc8345863c7cc4c66a329aec7e433d2d1c52a9` | `save-always` deprecated. Use the sub-actions |
| `actions/setup-node` | v7.0.0 | `820762786026740c76f36085b0efc47a31fe5020` | auto-cache only for npm with `packageManager` |
| `actions/setup-python` | v7.0.0 | `5fda3b95a4ea91299a34e894583c3862153e4b97` | `pip-install` input removed |
| `actions/setup-go` | v7.0.0 | `b7ad1dad31e06c5925ef5d2fc7ad053ef454303e` | cache on by default |
| `actions/setup-java` | v6.0.1 | `de7274f081f381c8f8158605e0321c36c376e2e6` | `cache-read-only` input |
| `actions/upload-artifact` | v7.0.1 | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | `archive: false` for a single unzipped file |
| `actions/download-artifact` | v8.0.1 | `3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c` | fails on digest mismatch by default |
| `actions/github-script` | v9.0.0 | `3a2844b7e9c422d3c10d287c895573f7108da1b3` | `require('@actions/github')` removed; use the injected `getOctokit` |
| `actions/attest-build-provenance` | v4.2.2 | `4d101475d8b20a2381f78447822ac1eab6504dd8` | |
| `astral-sh/setup-uv` | v10.2.0 | `c18668ad3cf93ea998bef934396af7bb5c839dc7` | cache auto-off on release/tag/`pull_request_target`/`workflow_run` |
| `Swatinem/rust-cache` | v2.9.2 | `6323deb102c322ba6fcbdcafc7e3dddab59af2b6` | |
| `pnpm/action-setup` | v6.1.0 | `ea17c68df8912ef543352723c149a84f56e3d413` | inputs use underscores (`run_install`) |
| `oven-sh/setup-bun` | v2.2.0 | `0c5077e51419868618aeaa5fe8019c62421857d6` | cache on by default (`no-cache: false`) |
| `docker/setup-buildx-action` | v4.4.1 | `f87e5991a6d7451dcb8d9637bfbc97413f497069` | |
| `docker/build-push-action` | v7.4.0 | `c3c9e263c25d99ce0380d002d59b67737d91b0dc` | |
| `docker/login-action` | v4.6.0 | `dbcb813823bdd20940b903addbd779551569679f` | |
| `docker/metadata-action` | v6.2.0 | `dc802804100637a589fabce1cb79ff13a1411302` | |
| `docker/setup-qemu-action` | v4.4.0 | `99012661954931238ded8c8b007157a8430204e1` | avoid when you can cross-compile |
| `dorny/paths-filter` | v4.0.3 | `ceb8a2b8f2d89434be7ff52d3de7ec3738c5cc9d` | |
| `step-security/harden-runner` | v2.21.1 | `e14015d583714f6e62063499dc959a02595150a1` | `egress-policy` defaults to `block` in `action.yml`. Always set it |
| `zizmorcore/zizmor-action` | v0.6.4 | `cc914d7f3750a2d13d75c7f184a1060aa0e9d482` | composite action |
| `aws-actions/configure-aws-credentials` | v6.3.0 | `e1253824e5c10ff9df46874f81ed3ec929e19cfd` | |
| `pypa/gh-action-pypi-publish` | v1.14.2 | `dc37677b2e1c63e2034f94d8a5b11f265b73ba33` | trusted publishing |
| `reproducible-containers/buildkit-cache-dance` | v3.4.0 | `5422eac04292c961a382e0f584ea0f03ad9da723` | |

CLI tools: actionlint **1.7.12** (`rhysd/actionlint:1.7.12` image), zizmor **1.30.1** (`ghcr.io/zizmorcore/zizmor:1.30.1`).

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
