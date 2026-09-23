# Docker build and push (multi-arch)

This covers the workflow side. The Dockerfile itself (stages, cache mounts, cross-compilation) belongs to the `docker-optimizer` skill.

Measured on GitHub-hosted public runners (`ubuntu-24.04`) on 2026-09-23 with a Go service built for `linux/amd64,linux/arm64`, a multi-stage Dockerfile, and a distroless final image of about 10 MB. The bench built without pushing (`push: false`). The push/login/metadata steps below were linted but not pushed to a registry. Format: wall-clock / Σ job time / billable minutes.

| Variant | Cold | Warm (no change) | Code change |
|---|---|---|---|
| **QEMU**: Dockerfile without `--platform=$BUILDPLATFORM`, no cache | 317 s / 313 s / **6** | — | — |
| Cross-compiling Dockerfile, no cache | 67 s / 62 s / 2 | 62–70 s / 60–66 s / 1–2 | 70 s / 66 s / 2 |
| + `type=gha,mode=max` layer cache (**this file**) | 108 s / 103 s / 2 | **27–29 s / 23–26 s / 1** | 74–88 s / 70–84 s / 2 |
| + `buildkit-cache-dance` for `RUN --mount=type=cache` | 94 s / 91 s / 2 | 38 s / 33 s / 1 | 100 s / 97 s / 2 |

What the numbers say:

1. **Cross-compile instead of emulating: 5× faster, 6 → 2 minutes.** Under QEMU every `RUN` of the arm64 build stage (`go mod download`, `go build`) is emulated. With `FROM --platform=$BUILDPLATFORM` + `GOOS/GOARCH`, both architectures compile natively on the x64 runner. Only the final `COPY` runs per platform. If the language can't cross-compile (native Node/Python extensions), build each architecture on its native runner (`ubuntu-24.04` + `ubuntu-24.04-arm`) and merge them with `docker buildx imagetools create`. Don't use QEMU.
2. **The layer cache pays off from the second build of an unchanged tree, not the first.** Cold, `mode=max` spent about 45 s exporting about 300 MB (every layer of the builder stages, including the `golang` base) to the cache. Warm, the whole build is cache hits: 8 s for the build step. Worth it when the same Dockerfile and dependencies are built often (PRs restore main's cache).
3. **A code change invalidates the compile layer**, and `type=gha` doesn't export `--mount=type=cache` directories, so `go build` starts with an empty build cache. That's why "code change" is close to the uncached time.
4. **`buildkit-cache-dance` did not pay off here.** It shortened the build step (33 s vs 51–63 s), but injecting and extracting the mount cache cost about 30 s. Use it only when the compile is minutes long and the mount cache is small relative to it, and measure. Otherwise the fix is on the Dockerfile side: keep dependency download in its own cacheable layer (as this Dockerfile does), and keep the per-commit compile small.

## Code

```yaml
name: image
on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:

permissions: {}

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

jobs:
  image:
    name: image
    runs-on: ubuntu-24.04
    timeout-minutes: 20
    permissions:
      contents: read       # checkout
      packages: write      # push to ghcr.io
      id-token: write      # sign build provenance
      attestations: write  # store the attestation
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      # No setup-qemu-action: the Dockerfile cross-compiles on $BUILDPLATFORM.
      - uses: docker/setup-buildx-action@f87e5991a6d7451dcb8d9637bfbc97413f497069 # v4.4.1
      - id: meta
        uses: docker/metadata-action@dc802804100637a589fabce1cb79ff13a1411302 # v6.2.0
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=sha
            type=semver,pattern={{version}}
            type=ref,event=branch
      - if: github.event_name != 'pull_request'
        uses: docker/login-action@dbcb813823bdd20940b903addbd779551569679f # v4.6.0
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ github.token }}
      - id: build
        uses: docker/build-push-action@c3c9e263c25d99ce0380d002d59b67737d91b0dc # v7.4.0
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha,scope=app
          # Only main writes the cache; PRs and tags read it.
          cache-to: ${{ github.ref == 'refs/heads/main' && 'type=gha,scope=app,mode=max,ignore-error=true' || '' }}
      - if: github.event_name != 'pull_request'
        uses: actions/attest-build-provenance@4d101475d8b20a2381f78447822ac1eab6504dd8 # v4.2.2
        with:
          subject-name: ghcr.io/${{ github.repository }}
          subject-digest: ${{ steps.build.outputs.digest }}
          push-to-registry: true
```

- **PRs build but don't push or log in.** A fork PR has no `packages: write` anyway. The PR job still proves the image builds; it reads main's cache and writes none.
- `packages: write`, `id-token: write` and `attestations: write` are granted to the one job that needs them. If PRs from forks matter, move the push into a separate job with `if: github.event_name != 'pull_request'`, so the PR job runs with `contents: read` only.
- `scope=app`: give each image its own scope, or two images overwrite each other's cache.
- `ignore-error=true`: a cache-export failure must not fail a good build. Measured: under `cache-mode: read` (or on any read-only trigger), the export **fails the whole build** with `error writing layer blob: failed to reserve cache` unless `ignore-error=true` is set. `actions/cache` only warns in that situation.
- Tags are pushed from the same workflow and read main's cache. Release builds that must not reuse any cache can set `no-cache: true`, at the cost of the full cold time.
- `ghcr.io/${{ github.repository }}` must be lowercase. With an uppercase owner, use `metadata-action` output or lowercase it in a step.
