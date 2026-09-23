# Cache in CI and multi-arch builds

The workflow YAML itself (jobs, permissions, secrets) belongs to the `github-actions` skill. This covers what the **Dockerfile and the `buildx` command** need so that CI reuses cache.

Sources: [Cache storage backends](https://docs.docker.com/build/cache/backends/), [Multi-platform builds](https://docs.docker.com/build/building/multi-platform/).

## 1. The problem

A CI runner starts with an empty builder. Without a remote cache, **every build is cold**, whatever order the Dockerfile uses. There are two separate layers of cache:

| Kind | What it stores | Survives in CI? |
|---|---|---|
| **Layer cache** (result of each instruction) | Result of `RUN`, `COPY`... | Only with `--cache-to`/`--cache-from` |
| **Cache mounts** (`--mount=type=cache`) | Package manager directories | **No**: they are local to the builder and are not exported by `--cache-to`. Requires a workaround (e.g. `reproducible-containers/buildkit-cache-dance` on GitHub Actions) or a persistent runner/builder |

That's why, for CI, the most important thing is a **dependency layer that can be cached as a layer**: `cargo-chef` (Rust), `go mod download` on its own, `npm ci` with the manifests mounted, and so on. On a layer cache hit, the `RUN` doesn't even execute, and the cache mount stops mattering.

## 2. Backends

```bash
# Registry (any CI; recommended). mode=max also caches intermediate stages.
docker buildx build \
  --cache-from type=registry,ref=registry.example.com/app:buildcache \
  --cache-to   type=registry,ref=registry.example.com/app:buildcache,mode=max \
  -t registry.example.com/app:$SHA --push .

# GitHub Actions (native cache API)
  --cache-from type=gha --cache-to type=gha,mode=max

# Local directory (self-hosted runners, persisted between jobs)
  --cache-from type=local,src=/cache/app --cache-to type=local,dest=/cache/app,mode=max
```

- `mode=min` (default) exports only the layers of the final image. **`mode=max`** exports every stage (build, deps). Without it, the build stage is never cached.
- Measured: on the default `docker` driver **with the containerd image store** (Engine 29), `--cache-to type=local` works directly. After `docker buildx prune --all`, a build using only `--cache-from` came out 100% `CACHED`. On the classic store (without containerd) you need `docker buildx create --driver docker-container --use`.
- One cache ref per branch or target (`buildcache-main`, `buildcache-pr-123`), with a fallback to main: `--cache-from` accepts several refs.

## 3. Multi-arch without emulation

QEMU emulation is much slower (every `RUN` instruction on the foreign architecture is interpreted). Whenever the language can cross-compile, build natively for the builder's platform and generate a binary for the target:

```dockerfile
FROM --platform=$BUILDPLATFORM golang:1.27-trixie AS build
ARG TARGETOS TARGETARCH
RUN CGO_ENABLED=0 GOOS=$TARGETOS GOARCH=$TARGETARCH go build -o /out/app .

FROM gcr.io/distroless/static-debian13:nonroot
COPY --from=build /out/app /app
```

Measured (Go, `linux/amd64,linux/arm64`): **12 s** total, no QEMU. Only the final stage's `COPY` runs per platform (no `RUN` in the runtime stage → no emulation).

| Language | Cross-compile |
|---|---|
| Go | `GOOS`/`GOARCH` (native, trivial with `CGO_ENABLED=0`) |
| Rust | `--target` + linker. [`tonistiigi/xx`](https://github.com/tonistiigi/xx) (`xx-cargo`) takes care of it |
| C/cgo | `tonistiigi/xx` (`xx-clang`, `xx-apt-get`) |
| Node/Python/Java | Bytecode is portable. Build dependencies on `$BUILDPLATFORM` only if they have **no** native extensions. Otherwise use native runners per architecture (e.g. `ubuntu-24.04-arm`) and merge the manifests with `docker buildx imagetools create` |

Avoid any `RUN` in the final stage of multi-arch images: each one runs under emulation on the other architecture.

## 4. Other CI speedups

- `.dockerignore` well configured → a smaller context upload, and fewer cache invalidations from irrelevant files (`.git` changes on every commit).
- `--pull` in scheduled/release builds, to get base image security patches.
- `docker build --check` as a cheap job before the build. It exits 1 if any warning fires. `# check=error=true` at the top of the Dockerfile makes even a plain `docker build` fail on warnings, and `# check=skip=RuleA,RuleB` turns off specific rules.
- Build attestations (`--sbom --provenance`) only on release builds if time matters.
