# Review checklist and measurement

Use it when **reviewing** an existing Dockerfile/compose, and to produce the before/after numbers.

## 1. Checklist (Dockerfile)

Severity: 🔴 security/correctness · 🟠 size/performance · 🟡 maintainability.

| # | Check | Sev. |
|---|---|---|
| 1 | Runs as root (no `USER`, or `USER root` at the end) | 🔴 |
| 2 | Secrets in `ARG`/`ENV`/`COPY .env` (visible in `docker history`) | 🔴 |
| 3 | `latest` or no tag, no digest in production | 🔴 |
| 4 | `.dockerignore` missing or weak (`.git`, `.env`, `node_modules` go into the context) | 🔴 |
| 5 | Shell-form `CMD`/`ENTRYPOINT`, or a package manager as PID 1 (`npm start`, `uv run`) | 🔴 |
| 6 | No `SIGTERM` handling and no `init` → `docker stop` takes 10 s + SIGKILL | 🟠 |
| 7 | Single stage with a compiler / devDependencies / source in the final image | 🟠 |
| 8 | `COPY . .` before installing dependencies | 🟠 |
| 9 | No cache mounts for the package manager | 🟠 |
| 10 | `apt-get` without `--no-install-recommends`, or `update` in a separate `RUN` from `install` | 🟠 |
| 11 | Full base (`node:24`, `python:3.14`) in the runtime | 🟠 |
| 12 | `HEALTHCHECK` using a binary that doesn't exist in the image (curl in distroless) | 🟠 |
| 13 | Runtime not tuned for the limit (Node heap, Python workers, JVM heap, GOMEMLIMIT) | 🟠 |
| 14 | `ADD` where `COPY` is enough; relative `WORKDIR`; `RUN cd` | 🟡 |
| 15 | Missing `# syntax=docker/dockerfile:1`; legacy `ENV key value`; `MAINTAINER` | 🟡 |
| 16 | No OCI labels (`org.opencontainers.image.source`/`revision`) | 🟡 |

Compose: limits (cpus/memory/pids, `memswap_limit`), hardening (`read_only`, `cap_drop`, `no-new-privileges`), log rotation, `depends_on` with `service_healthy`, `restart`, ports exposed on `0.0.0.0` without need, `docker.sock` mounted, `privileged: true`, secrets in `environment:` in plain text.

## 2. Measurement commands

```bash
# Automatic lint (Docker's official build checks)
docker build --check .

# Size: compressed (pull) vs on disk (unpacked)
docker image ls app:tag                        # CONTENT SIZE = compressed, DISK USAGE = unpacked (containerd store)
docker save app:tag | wc -c                    # compressed size in bytes, for scripts (containerd store)
docker image ls --tree app                     # per platform, for multi-arch images

# Which layers weigh the most, and which instruction created them
docker history --format '{{.Size}}\t{{.CreatedBy}}' app:tag | sort -rh | head

# Rebuild time after changing only source code (should hit CACHED on dependencies).
# The content has to change: BuildKit keys the cache on file content, so `touch` leaves everything CACHED.
printf '\n' >> src/<file> && time docker build -t app:tag . 2>&1 | grep -E 'CACHED|DONE'
git checkout -- src/<file>

# User and entrypoint
docker inspect -f 'user={{.Config.User}} entry={{json .Config.Entrypoint}} cmd={{json .Config.Cmd}}' app:tag

# Runtime under the production limit. --memory-swap equal to -m: without it the container gets that much swap on top.
docker run -d --name app-test --cpus=1 -m 256m --memory-swap 256m app:tag
docker stats --no-stream app-test
docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}} oom={{.State.OOMKilled}}' app-test

# Graceful stop time (should be < 1 s, exit 0 or 143, never 137)
s=$(date +%s%N); docker stop app-test; echo "$(( ($(date +%s%N)-s)/1000000 )) ms"; docker inspect -f '{{.State.ExitCode}}' app-test
docker rm app-test
```

### Extra tools

Pin each tool by version and digest, and give it a tar of the image instead of `/var/run/docker.sock` (root on the host). `aquasec/trivy:latest` served malware in March 2026. The versions below were checked in 2026-11: take a newer one from the project's releases and its digest from `docker buildx imagetools inspect`.

```bash
docker save app:tag -o app.tar

# Wasted bytes per layer (files overwritten/removed in later layers)
docker run --rm -v "$PWD/app.tar:/app.tar:ro" \
  wagoodman/dive:v0.13.1@sha256:f1886e6c32c094fc41a623c1989f5cb3e48aa766da5f0be233f911fc1d85ce10 \
  --source docker-archive /app.tar --ci

# HIGH/CRITICAL CVEs
docker run --rm -v "$PWD/app.tar:/app.tar:ro" \
  aquasec/trivy:0.76.2@sha256:8f6bb947dbc528902e11f2f5be52f7b519f6a39d5d148f41166f2040499768fb \
  image --input /app.tar --severity HIGH,CRITICAL --quiet

# Lint beyond build checks
docker run --rm -i \
  hadolint/hadolint:v2.15.1@sha256:32dac94127fd60b7b7e3fbfc65e1383b9b5e25c9bfd7b8536de7a539fe68a12d < Dockerfile

rm app.tar
```

Reference values measured (Node app): naive → trivy 483 HIGH/CRIT, dive 8.5 MB wasted. Distroless multi-stage → 0 CVEs, 630 bytes wasted.

**What no tool catches** (verified with build-check + hadolint): missing `USER`, missing `.dockerignore`, a package manager as PID 1 in exec form (`["npm","start"]`), `COPY . .` before installing dependencies, devDependencies in the final image, a single stage with a compiler. Review these by hand, always.

**Compressed vs on disk**: with the containerd image store, `docker image ls` shows both: CONTENT SIZE is the compressed content (what gets pulled) and DISK USAGE adds the unpacked layers. `docker image inspect -f '{{.Size}}'` is close to the disk usage, not to the compressed size (measured on Engine 29.9 for `alpine:3.20`: 13.07 MB in `inspect`, 3.71 MB of content). On the classic store only the unpacked size is available locally. Compare apples with apples. In before/after reports, use the compressed size as the main number.

## 3. Report format

```markdown
| Metric | Before | After |
|---|---|---|
| Compressed image | 429 MB | 57 MB |
| On disk | 1.72 GB | 236 MB |
| Rebuild (code only) | 22 s | 8 s |
| User | root | 65532 |
| `docker stop` | 10.3 s (SIGKILL) | 0.2 s |

Main changes:
- ...: why it matters
```

Measured numbers are presented as measured. Estimates are presented as estimates, never mixed.
