# Release on tag: build once, attest, publish without stored tokens

A Python package built with uv. The layout generalizes to anything that produces files:

1. `build`: `contents: read` only, **no cache** (cache poisoning), builds the distribution once, uploads it as an artifact.
2. `attest` inside `build`: signs SLSA build provenance with the job's OIDC identity.
3. `pypi`: downloads the exact bytes that were built and publishes through **trusted publishing** (OIDC, no `PYPI_TOKEN`), gated by the `pypi` environment.
4. `github-release`: the only job with `contents: write`.

Validated on the bench repo with tags v0.1.0–v0.1.3:
- `build` + `github-release` succeeded, and the log shows `Cache mode: none` on `build`.
- `gh attestation verify` passed on the downloaded wheel (signer `release.yml@refs/tags/v0.1.0`).
- A tag without a version bump failed in `build`, so nothing was published.
- `concurrency.queue` was accepted.

zizmor 1.30.1 reports nothing. actionlint 1.7.12 flags only the newer `queue` and `cache-mode` keys (false positives, see `references/review-checklist.md`). The `pypi` job needs a PyPI trusted publisher, so it was linted but not run.

```yaml
name: release
on:
  push:
    tags: ['v*.*.*']

permissions: {}

# Never cancel a release half-way; queue them in order.
concurrency:
  group: release
  cancel-in-progress: false
  queue: max

jobs:
  build:
    name: build
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    cache-mode: none # release: never restore or save a cache
    permissions:
      contents: read     # checkout
      id-token: write    # sign the provenance attestation
      attestations: write # store the attestation
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: astral-sh/setup-uv@c18668ad3cf93ea998bef934396af7bb5c839dc7 # v10.2.0
        with:
          enable-cache: false # release: never restore a cache someone else wrote
      - name: Tag must match the package version
        env:
          TAG: ${{ github.ref_name }}
        run: test "v$(uv version --short)" = "$TAG"
      - run: uv build
      - uses: actions/attest-build-provenance@4d101475d8b20a2381f78447822ac1eab6504dd8 # v4.2.2
        with:
          subject-path: dist/*
      - uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
        with:
          name: dist
          path: dist/
          retention-days: 7
          if-no-files-found: error

  pypi:
    name: pypi
    needs: build
    runs-on: ubuntu-24.04
    timeout-minutes: 5
    environment:
      name: pypi
      url: https://pypi.org/p/my-package
    permissions:
      id-token: write # trusted publishing to PyPI
    steps:
      - uses: actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c # v8.0.1
        with:
          name: dist
          path: dist/
      - uses: pypa/gh-action-pypi-publish@dc37677b2e1c63e2034f94d8a5b11f265b73ba33 # v1.14.2

  github-release:
    name: github-release
    needs: build
    runs-on: ubuntu-slim
    timeout-minutes: 5
    permissions:
      contents: write # create the release and upload assets
    steps:
      - uses: actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c # v8.0.1
        with:
          name: dist
          path: dist/
      - env:
          GH_TOKEN: ${{ github.token }}
          GH_REPO: ${{ github.repository }}
          TAG: ${{ github.ref_name }}
        run: gh release create "$TAG" dist/* --verify-tag --generate-notes
```

## Why it looks like this

- **Build once, publish the same bytes.** Every consumer downloads the artifact. Nothing rebuilds, so what was attested is what ships. `download-artifact@v8` fails if the digest doesn't match.
- **No cache in release workflows.** A cache is written by a less trusted run (any push to main) and restored into the job that holds publishing rights. `cache-mode: none` enforces that at the token level, and `enable-cache: false` makes the intent visible in the action (setup-uv v10 already skips caching on tag pushes).
- **Permissions per job.** `build` can sign but not write the repo. `pypi` can only mint an OIDC token. `github-release` can write contents but has no OIDC. A compromised build step can't create a release.
- **The `pypi` environment** holds the protection rules (required reviewers, tag pattern `v*`). On PyPI, configure the trusted publisher with repo + workflow `release.yml` + environment `pypi`, so a token minted anywhere else is rejected.
- **`concurrency: release`, `cancel-in-progress: false`, `queue: max`**: tags pushed close together all complete, one after the other. Without `queue: max`, only one run can be pending, so a third tag would cancel the second one while it waits.
- **`ubuntu-slim` for `github-release`**: it is one API call, so it runs on the ⅓-price runner.
- Turn on **immutable releases** in the repository settings, so the published tag and assets can't be replaced afterwards.
- `--verify-tag` makes `gh release create` fail instead of silently creating a tag that doesn't exist.
- **The tag must match the package version.** On the bench, pushing `v0.1.1` without bumping `pyproject.toml` happily published `bench_py-0.1.0-*.whl` under release v0.1.1. The first step now fails that case in about a second, before anything is built or signed.

## Verifying the attestation (consumer side)

```bash
gh release download v0.1.0 -R owner/repo -p '*.whl'
gh attestation verify bench_py-0.1.0-py3-none-any.whl -R owner/repo
```
