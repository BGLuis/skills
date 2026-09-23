---
name: docker-optimizer
description: Generates, reviews, and tunes Dockerfiles, .dockerignore, and docker-compose.yml for small images, fast cached builds, hardened containers, and maximum performance under tight CPU/memory limits. Use whenever the user asks to write, review, harden, or optimize a Dockerfile, compose file, or container image, asks why a Docker build is slow or an image is too large, or asks how to size container resources (memory/CPU limits, workers, heap, GOMAXPROCS). Do NOT use for Kubernetes manifests/Helm, CI/CD pipeline YAML (that is github-actions), or application code unrelated to containerization.
---

# Docker Optimizer

Act as a Senior Infrastructure Engineer. Every image you write or review must satisfy, in this order: **correct** (it builds and runs), **secure** (least privilege), **small and fast** (build, pull, startup), **frugal at runtime** (the smallest CPU/memory limit that holds the load). Never produce a generic Dockerfile: apply the rules below and justify each decision.

## 0. Workflow

1. **Read before writing.** Existing `Dockerfile`, `.dockerignore`, `compose.yaml`, the lockfile and package manager, the language version (`.nvmrc`, `go.mod`, `pyproject.toml`, `rust-toolchain.toml`, `pom.xml`), the real start command, and whether the app writes to disk, spawns child processes, or needs native libraries.
2. **Choose the base and the stages** (`references/dockerfile-rules.md` §6). Use the example for the language in `examples/` as the template.
3. **Validate** when a docker CLI is available:
   - `docker build --check .` (no warnings)
   - build, then `docker image ls` / `docker image inspect -f '{{.Size}}'`
   - `docker run` with the production limits (`--cpus`, `-m`)
   - `docker stop` exits 0 fast
   - `docker inspect -f '{{.Config.User}}'` is not root

   Commands are in `references/review-checklist.md`.
4. **Before/after report** whenever you optimize something that exists. Report compressed size, on-disk size, rebuild time after a code-only change, the user, and `docker stop` time, with **real numbers** when you could measure and marked as estimates when you could not. Then list the changes and why each one matters.

## 1. Non-negotiable rules (Dockerfile)

- `# syntax=docker/dockerfile:1` on the first line.
- **Multi-stage** for anything compiled or transpiled. Compilers, devDependencies, headers and source code never reach the final stage.
- **Cache order**: manifests + dependency install before `COPY` of the source. Mount the manifests with `--mount=type=bind` instead of copying them.
- **`--mount=type=cache`** on the package manager. **`--mount=type=secret`** for credentials. Never put secrets in `ARG`/`ENV`.
- **Strict `.dockerignore`**, always (`.git`, `.env*`, `node_modules`, `target`, `.venv`, `Dockerfile*`...).
- **Non-root with a static UID/GID** (`USER 10001:10001` or the image's `nonroot` 65532). Files copied into the runtime stay owned by root (read-only for the process). Use `--chown` only where the app writes.
- **Pin the base**: at least `major.minor` for the tag, plus a `@sha256:` digest in production with automated updates. Never `latest`. Don't pin apt/apk package versions.
- **Exec form** in `CMD`/`ENTRYPOINT`, **never a package manager as PID 1** (`npm start`, `uv run`, `poetry run`). The process must handle `SIGTERM`, or the container runs with `init: true` / `--init`.
- **`COPY`, not `ADD`**. `apt-get install --no-install-recommends`.
- **HEALTHCHECK** only with something that exists in the image. Distroless has no `curl`: use a `healthcheck` subcommand in the binary itself, the runtime (`node -e fetch(...)`, `python -c urllib...`), or leave it to the orchestrator.

## 2. Base image (summary — full table in `references/dockerfile-rules.md` §6)

| Case | Runtime |
|---|---|
| Go, Rust with musl | `gcr.io/distroless/static-debian13:nonroot` (`scratch` only if you copy CA and passwd yourself) |
| Rust/C++ glibc | `gcr.io/distroless/cc-debian13:nonroot` |
| Node | `gcr.io/distroless/nodejs24-debian13:nonroot`, or `node:24-trixie-slim` if you need a shell |
| Python | `python:3.x-slim-trixie` (same interpreter in build and runtime; distroless/python ships a different Python version) |
| Java | jlink custom JRE on `debian:trixie-slim`, or `eclipse-temurin:25-jre` |
| Hardened alternative | Docker Hardened Images (`dhi.io`, free, near-zero CVEs) |
| Build stage | full image of the language, never shipped |

Avoid `alpine` for Python and for native Node dependencies (musl: wheels and prebuilt binaries are often missing → slow builds, subtle bugs).

## 3. Runtime performance under limits

Most runtimes size threads, workers and heap from the **host**, not from the container. Before you set limits, read `references/runtime-performance.md`. In short (measured on Engine 29.7):

- **Node**: the heap follows the limit without headroom (256 MB → heap 259 MB → OOM kill). Always set `--max-old-space-size` ≈ 75% of the limit.
- **Python**: `os.cpu_count()` returns the host's cores. Set `--workers` explicitly.
- **Go ≥ 1.25**: `GOMAXPROCS` follows the CPU limit (floor of 2). Set `GOMEMLIMIT` ≈ 90% of the memory limit.
- **Java**: the default heap is 25% of the limit. Use `-XX:MaxRAMPercentage=75`.
- **Rust**: respects the CPU limit by itself.

## 4. Compose

Details and validated fields in `references/compose.md`. Production:

- `deploy.resources.limits` (cpus, memory, pids) + `reservations.memory`
- `read_only: true` + `tmpfs`, `cap_drop: [ALL]`, `security_opt: [no-new-privileges:true]`, `init: true`
- log rotation (`max-size`/`max-file`)
- `healthcheck` + `depends_on: condition: service_healthy`
- `restart: unless-stopped`
- ports on `127.0.0.1` when there's a proxy in front

Development: a `dev` stage with a shell, `develop.watch` (sync/rebuild) instead of rebuilding by hand.

## 5. When to read each file

| File | Read when |
|---|---|
| `references/dockerfile-rules.md` | writing any Dockerfile (cache, mounts, apt, multi-stage, base-image table) |
| `references/runtime-performance.md` | setting CPU/memory limits, workers, heap, or the user wants "more performance with fewer resources" |
| `references/compose.md` | any compose file (dev or prod) |
| `references/security.md` | hardening, secrets, scanning, SBOM/provenance, supply chain |
| `references/ci-cache.md` | a slow build in CI, remote cache, multi-arch |
| `references/review-checklist.md` | **reviewing** an existing Dockerfile/compose, or measuring before/after |
| `examples/node.md` · `python-uv.md` · `go.md` · `rust.md` · `java.md` | production template for the language (each has measured numbers) |
| `examples/compose-dev.md` · `compose-prod.md` | compose templates |
| `examples/anti-patterns.md` | what never to produce, and how each anti-pattern is fixed |

## 6. Development vs production

- **Dev**: images with a shell (`-slim`), a `dev` stage, bind mounts / `develop.watch`, devDependencies installed. Distroless and scratch are fine for production, but painful for debugging. To debug distroless without adding a shell to the image, attach a tools container to its namespaces: `docker run --rm -it --pid=container:<ctr> --network=container:<ctr> busybox sh` (tested: sees the process and the port). `docker debug` exists only in Docker Desktop.
- **Prod**: everything in §1, no source bind mounts, immutable images promoted between environments (the same digest in staging and prod, configuration through env vars/secrets).
- On Docker Desktop (macOS/Windows), slow bind-mount I/O is solved in the Desktop settings (VirtioFS / synchronized file shares), not in the compose file. Recommend `develop.watch` for large trees.
