# Dockerfile rules — cache, BuildKit and base image

Sources: [Docker build best practices](https://docs.docker.com/build/building/best-practices/), [Optimize cache usage](https://docs.docker.com/build/cache/optimize/), [hexops/dockerfile](https://github.com/hexops-graveyard/dockerfile).

## 1. Layer order and cache

A layer is invalidated when its instruction changes or when any file it read changes. **Everything after it rebuilds.**

Order: base → system packages → dependency manifests → install dependencies → source → build.

```dockerfile
# Wrong: any .ts change reinstalls every dependency
COPY . .
RUN npm ci

# Right: the npm ci layer depends only on the manifests
RUN --mount=type=bind,source=package.json,target=package.json \
    --mount=type=bind,source=package-lock.json,target=package-lock.json \
    npm ci
COPY . .
```

## 2. BuildKit mounts (`RUN --mount`)

Always start the file with `# syntax=docker/dockerfile:1`. It pulls the latest stable frontend 1.x, so there's no need to pin `1.4`.

| Mount | Use it for | Notes |
|---|---|---|
| `type=cache,target=<dir>` | Package manager cache (npm, pip, uv, go, cargo, maven, apt) | Persists across builds **on the same builder**. Not exported by `--cache-to` (CI: see `ci-cache.md`). Never put build output you need in the image inside it. |
| `type=bind,source=X,target=X` | Manifests (`package.json`, `uv.lock`, `go.mod`) or the whole context (`target=.`) during compilation | Doesn't create a layer. Read-only by default. Output has to be written **outside** the mount. |
| `type=secret,id=X[,env=VAR]` | Tokens (`.npmrc`, `pip.conf`, GitHub token) | Never in `ARG` or `ENV`: those end up in `docker history` and in the image config. |
| `type=ssh` | `git clone` of private repos | `docker build --ssh default .` |

Cache paths per ecosystem:

| Tool | `target=` |
|---|---|
| npm | `/root/.npm` |
| pnpm | `/root/.local/share/pnpm/store` |
| yarn (berry) | `/root/.yarn/berry/cache` |
| pip | `/root/.cache/pip` |
| uv | `/root/.cache/uv` (+ `UV_LINK_MODE=copy`) |
| poetry | `/root/.cache/pypoetry` |
| go | `/go/pkg/mod` and `/root/.cache/go-build` |
| cargo | `/usr/local/cargo/registry` and `/usr/local/cargo/git` |
| maven | `/root/.m2` |
| gradle | `/root/.gradle` |
| apt | `/var/cache/apt` and `/var/lib/apt` with `sharing=locked` |

When the build runs as a non-root user, the target is that user's `$HOME`. Add `uid=<UID>` to the mount.

### apt with a cache mount (the official pattern)

Debian/Ubuntu images have `/etc/apt/apt.conf.d/docker-clean`, which deletes the cache after every install. Remove it, otherwise the cache mount stays empty:

```dockerfile
RUN rm -f /etc/apt/apt.conf.d/docker-clean
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      libpq-dev
```

Without cache mounts (for example old CI), use the classic form in a **single** `RUN`: `apt-get update && apt-get install -y --no-install-recommends ... && rm -rf /var/lib/apt/lists/*`.

- `--no-install-recommends` always: it often cuts 30–60% of the installed packages.
- **Don't pin versions of apt packages** (`pkg=1.2.3-1`). Debian removes old versions from its mirrors and the build breaks within weeks. Pin the **base image by digest** for reproducibility (hadolint DL3008 can be ignored with this justification).
- Sort packages alphabetically, one per line (clean diffs).

## 3. Multi-stage

- Every compiled or transpiled project: at least `build` → `runtime`. Compilers, headers, devDependencies and source code never reach the runtime.
- Name the stages (`AS build`). BuildKit only builds the stages the target depends on, and **runs independent stages in parallel**. Split `deps` (prod) and `build` (full) to take advantage of that.
- `--target dev` for a development stage with a shell and hot reload (see `examples/compose-dev.md`).
- `COPY --from=<image>` to grab a binary from another image without a stage (for example `COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /usr/local/bin/uv`).

## 4. Other instructions

- **`COPY`**, not `ADD`. Use `ADD` only to extract a local tar, or for `ADD --checksum=sha256:... https://...` (a remote download with verification).
- **`COPY --link`** makes the copy independent of the layers below it. Changing the base image doesn't invalidate or re-copy it (a rebase). Use it for `COPY --from` into the final stage. It is incompatible with anything that depends on existing files at the destination (symlinks in the target path).
- **Heredocs** for long scripts, instead of chains of `&& \`:
  ```dockerfile
  RUN <<EOT
      set -eu
      step one
      step two
  EOT
  ```
- **Exec form** (`["bin", "arg"]`) in `CMD`/`ENTRYPOINT`. Shell form wraps the process in `/bin/sh -c`, which does not forward `SIGTERM`. If you need an entrypoint script, end it with `exec "$@"`.
- **`ENTRYPOINT` = the binary, `CMD` = default arguments**. Then `docker run image --help` works.
- **`WORKDIR` with absolute paths**. Never `RUN cd ...`.
- **`ENV` for build-time variables only when the runtime needs them**. Otherwise use `ARG`. Never use either for secrets.
- **`LABEL org.opencontainers.image.source=...`** (plus `version`, `revision`) for traceability.
- `set -o pipefail` (or `SHELL ["/bin/bash", "-o", "pipefail", "-c"]`) when a `RUN` uses pipes.

## 5. `.dockerignore`

Always present. It shrinks the context (upload to the builder), prevents cache invalidation caused by irrelevant files, and keeps secrets out. Minimum:

```
.git
.env*
*.log
Dockerfile*
.dockerignore
# per language: node_modules, dist, target, .venv, __pycache__, coverage ...
```

To whitelist instead, start with `*` and re-include with `!src/`, `!package*.json`.

## 6. Base image selection

| Base | Compressed size (amd64, measured 2026-09) | Shell | libc | When |
|---|---|---|---|---|
| `scratch` | 0 | no | — | Static binary + you copy the CA certs and passwd yourself |
| `gcr.io/distroless/static-debian13:nonroot` | 0.9 MB | no | none | **Go / Rust musl default** (includes CA, tzdata, nonroot) |
| `gcr.io/distroless/cc-debian13:nonroot` | 10.7 MB | no | glibc | Rust (glibc), C/C++ |
| `gcr.io/distroless/nodejs24-debian13:nonroot` / `java25-debian13` | 55 / 73 MB | no | glibc | Node/Java production when nothing needs a shell |
| Docker Hardened Images (`dhi.io/...`) | variable | depends on the variant | glibc/musl | Near-zero CVEs, SBOM, SLSA L3 provenance, free (Apache 2.0) since Dec/2025. Great hardened alternative to distroless |
| `*-slim-trixie` (Debian 13) | python 43.5 / node 82.5 MB | yes | glibc | **Interpreted default** (Python, Node) and whenever you need `apt` in the runtime |
| `alpine` | 3.8 MB | yes | musl | CLI tools, proxies. Avoid for Python (wheels are often glibc-only → slow compiles) and when the app is sensitive to allocator/DNS behavior |
| full images (`node:24`, `python:3.14`, `golang:1.27`) | 300–600 MB | yes | glibc | **Only in the build stage** |

Rules:
- Pin a specific **tag** (`node:24.9-trixie-slim`, at least `major.minor`) and, in production, the **digest**: `FROM node:24-trixie-slim@sha256:...`. Get it with `docker buildx imagetools inspect <image> --format '{{json .Manifest.Digest}}'`. Automate updates (Dependabot `package-ecosystem: docker` or Renovate), or the image stops receiving patches.
- Build with `--pull` in CI so you always start from the most recent patch of the tag.
- The Debian codename (`trixie`, `bookworm`) should be the same between build and runtime (glibc compatibility).
