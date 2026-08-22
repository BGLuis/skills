---
name: docker-optimizer
description: Generates and reviews Dockerfiles and docker-compose.yml configurations for build performance, image size, multi-stage builds, and container security. Use whenever the user asks to write, review, harden, or optimize a Dockerfile, docker-compose file, or container image, or asks why a Docker build is slow or an image is too large. Do NOT use for Kubernetes manifests/orchestration, CI/CD pipeline YAML, or general application code unrelated to containerization.
---

# Docker Optimizer

Act as a Senior Infrastructure Engineer when generating or reviewing Dockerfiles and docker-compose configurations. Do not produce standard, unoptimized configurations — always apply the rules below.

## 0. Workflow: analysis and comparison report

- **Existing analysis**: Before modifying anything, read the existing `Dockerfile` or `docker-compose.yml` (if present). Understand the current base image, dependencies, layer structure, and likely bottlenecks.
- **Before/after report**: Whenever you optimize an existing configuration, end your response with a comparison summary:
  - Estimated or actual reduction in final image size (e.g., "reduced from 1.2GB to 150MB").
  - Expected improvements in build time (from cache mounts) and startup time.
  - A bulleted list of the main architectural changes and why they matter.

## 1. General Dockerfile rules

- **Layer caching**: Order instructions from least frequently changed (OS dependencies) to most frequently changed (application code).
- **`.dockerignore`**: Always include a strict `.dockerignore` (excluding `node_modules`, `.git`, local build artifacts, etc.).
- **`COPY` vs `ADD`**: Always use `COPY`. Only use `ADD` to natively extract a local `.tar` file.
- **Rootless**: Never run the final application as root. Use a predefined non-root user (like `node`) or create one.
- **Pin versions**: Never use `latest`. Pin base images to specific versions or SHA-256 digests (e.g., `FROM node@sha256:...`).
- **Signal handling**: Ensure PID 1 forwards signals. Use the exec form of `CMD`/`ENTRYPOINT`; add `--init` or `tini` only when the process genuinely spawns children.
- **Healthchecks**: Define a `HEALTHCHECK` (or a compose-level `healthcheck`) for long-running services so orchestrators can detect a hung process.
- **Linting compliance**: Adhere to `hadolint` rules (group `RUN` commands with `&&`, pin `apt`/`apk` package versions, clear package caches).

## 2. Base image selection

- **Debian slim**: Default for interpreted languages (Python, Node.js) to avoid `musl` libc compatibility issues.
- **Distroless**: Default for production runtime (Java, Node.js, Python) for maximum security (no shell, minimal attack surface).
- **Scratch**: Use only for static, self-contained binaries (Go, Rust compiled with `x86_64-unknown-linux-musl`).
- **Alpine**: Avoid for Node/Python if C extensions are required. Fine for pure tools or networking utilities.

## 3. Advanced build architecture (BuildKit)

- **Multi-stage builds**: Always use multi-stage builds (`builder` and `runner` stages) to keep the final image minimal.
- **Syntax**: Include `# syntax=docker/dockerfile:1.4` (or newer) at the top of the file.
- **Cache mounts**: Use `--mount=type=cache` for package managers (apt, npm, pip, cargo) to speed up rebuilds.
- **Secret mounts**: Use `--mount=type=secret` for credentials. Never use `ARG` or `ENV` for secrets.

## 4. Language-specific heuristics

If the target application uses Node.js, Python, Rust, Go, or Java, read `references/language-heuristics.md` before proceeding with the optimization.

## 5. Reference examples (few-shot)

If in doubt about the ideal structure of a file, read the relevant file under `examples/` — gold-standard configurations and anti-patterns to avoid:

- `examples/node-multistage.md` — production Node.js Dockerfile
- `examples/go-scratch.md` — production Go Dockerfile
- `examples/compose-dev.md` — development docker-compose.yml
- `examples/bad-dockerfile.md` — anti-patterns to never reproduce

## 6. Development vs. production environments

- **Local development**:
  - Do NOT use Distroless or Scratch. Use images with a shell (e.g., `-slim` or standard variants) so the developer can `docker exec` and debug.
  - Use `docker compose watch` for live code syncing (hot-reloading) instead of rebuilding the image on every change.
  - Bind mounts are acceptable and expected; on Mac/Windows, advise the user on VirtioFS for better I/O performance.
- **Production**:
  - Apply the strict rules above: Distroless, no bind mounts of source code, multi-stage builds, locked/pinned configurations.

## 7. Docker Compose optimizations

- **Resource limits**: Always define `deploy.resources.limits` (CPU and memory) to prevent OOM crashes that affect the host.
- **VirtioFS**: Recommend or configure VirtioFS for volume mounts (instead of gRPC-FUSE) to improve I/O performance on macOS and Windows (WSL2).
- **Resilience**: Include `restart: on-failure:3`.
- **Startup order**: Use `depends_on` with `condition: service_healthy` rather than assuming boot order.
- **Single-process paradigm**: If a container truly needs multiple processes, prefer `supervisord` over a complex sidecar network when the isolation overhead of separate containers isn't worth it.
