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

Compose: limits (cpus/memory/pids), hardening (`read_only`, `cap_drop`, `no-new-privileges`), log rotation, `depends_on` with `service_healthy`, `restart`, ports exposed on `0.0.0.0` without need, `docker.sock` mounted, `privileged: true`, secrets in `environment:` in plain text.

## 2. Measurement commands

```bash
# Automatic lint (Docker's official build checks)
docker build --check .

# Size: compressed (pull) vs on disk (unpacked)
docker image inspect -f '{{.Size}}' app:tag   # bytes; with the containerd store = compressed content
docker image ls app                            # on-disk usage
docker image ls --tree app                     # per platform, for multi-arch images

# Which layers weigh the most, and which instruction created them
docker history --format '{{.Size}}\t{{.CreatedBy}}' app:tag | sort -rh | head

# Rebuild time after changing only source code (should hit CACHED on dependencies)
touch src/<file> && time docker build -t app:tag . 2>&1 | grep -E 'CACHED|DONE'

# User and entrypoint
docker inspect -f 'user={{.Config.User}} entry={{json .Config.Entrypoint}} cmd={{json .Config.Cmd}}' app:tag

# Runtime under the production limit
docker run -d --name t --cpus=1 -m 256m app:tag
docker stats --no-stream t
docker inspect -f '{{.State.Health.Status}} oom={{.State.OOMKilled}}' t

# Graceful stop time (should be < 1 s, exit 0 or 143, never 137)
s=$(date +%s%N); docker stop t; echo "$(( ($(date +%s%N)-s)/1000000 )) ms"; docker inspect -f '{{.State.ExitCode}}' t
```

### Extra tools

```bash
# Wasted bytes per layer (files overwritten/removed in later layers)
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock wagoodman/dive:latest app:tag --ci

# HIGH/CRITICAL CVEs
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest \
  image --severity HIGH,CRITICAL --quiet app:tag

# Lint beyond build checks
docker run --rm -i hadolint/hadolint < Dockerfile
```

Reference values measured (Node app): naive → trivy 483 HIGH/CRIT, dive 8.5 MB wasted. Distroless multi-stage → 0 CVEs, 630 bytes wasted.

**What no tool catches** (verified with build-check + hadolint): missing `USER`, missing `.dockerignore`, a package manager as PID 1 in exec form (`["npm","start"]`), `COPY . .` before installing dependencies, devDependencies in the final image, a single stage with a compiler. Review these by hand, always.

**Size in `docker image ls` vs `inspect`**: with the containerd image store, `image ls` shows the unpacked disk usage and `inspect .Size` shows the compressed content (what gets pulled). Compare apples with apples. In before/after reports, use the compressed size as the main number.

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
