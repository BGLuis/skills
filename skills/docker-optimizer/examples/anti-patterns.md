# Anti-patterns — never produce these

This file is real. It was run through `docker build --check` and hadolint (Engine 29.7). The comments say which tool catches each problem. **"Nobody"** means neither tool detects it, so it is up to you.

```dockerfile
FROM node:latest as build                 # hadolint DL3007 (latest) · build-check FromAsCasing
MAINTAINER someone@example.com            # build-check MaintainerDeprecated · hadolint DL4000
WORKDIR app                               # build-check WorkdirRelativePath · hadolint DL3000
ARG PASSWORD=hunter2                      # build-check SecretsUsedInArgOrEnv · hadolint DL3064
ENV API_KEY=supersecretvalue123           # build-check SecretsUsedInArgOrEnv · hadolint DL3064
ENV NODE_ENV production                   # build-check LegacyKeyValueFormat
COPY . .                                  # Nobody: invalidates the cache of npm install on any change
RUN apt-get update && apt-get install -y curl git   # hadolint DL3015 (recommends); no cache/cleanup
RUN npm install                           # Nobody: should be npm ci, with a cache mount, --omit=dev
                                          # Nobody: no USER → runs as root
                                          # Nobody: single stage → git, curl, devDependencies in prod
CMD npm start                             # build-check JSONArgsRecommended · hadolint DL3025
                                          # Nobody: npm as PID 1 (signals, exit code 1 on stop)
                                          # Nobody: no .dockerignore → .git, .env, node_modules in the context
```

Measured consequences for the equivalent naive image (`node:24`, `npm install`, `npm start`):
- 429 MB compressed / 1.72 GB on disk, against 57 MB / 236 MB for the corrected version (`examples/node.md`).
- **483 HIGH/CRITICAL CVEs** (trivy) against **0** in the distroless version.
- Secrets from `ARG`/`ENV` readable in `docker history` and in the image's tar.

## Anti-pattern → fix

| Anti-pattern | Why it's bad | Fix |
|---|---|---|
| `FROM x:latest` / no tag | Non-reproducible build, surprise major versions | `x:24-trixie-slim@sha256:...` + Dependabot/Renovate |
| Full base in the runtime | Hundreds of MB and CVEs | Multi-stage. Runtime slim/distroless/DHI |
| `COPY . .` before installing dependencies | Every code change reinstalls everything | Bind-mount the manifests, install, then `COPY` the source |
| `npm install` / `pip install` without a lockfile | Non-deterministic | `npm ci`, `uv sync --locked`, `pip install -r requirements.txt` with pinned hashes |
| devDependencies in the image | Size, attack surface | `npm ci --omit=dev` in a separate stage, `uv sync --no-dev` |
| No `USER` | Root inside the container | `USER 10001:10001` / `nonroot` |
| `ARG`/`ENV` with secrets | Leaks in `history` and the tar | `RUN --mount=type=secret` |
| `CMD npm start` / shell form | PID 1 doesn't receive `SIGTERM` → 10 s + SIGKILL | `CMD ["node", "dist/index.js"]` + a `SIGTERM` handler or `init: true` |
| `apt-get install` without `--no-install-recommends`, `update` on its own | Stale cache, extra packages | A single `RUN`, `--no-install-recommends`, a cache mount or `rm -rf /var/lib/apt/lists/*` |
| `pip install --no-cache-dir` **together with** a cache mount | Cancels out the mount | Pick one: a cache mount (BuildKit) or `--no-cache-dir` (legacy) |
| `HEALTHCHECK CMD curl ...` on distroless | curl doesn't exist → always unhealthy | A `healthcheck` subcommand in the binary, or a probe using the runtime |
| `supervisord`/PM2 running several processes | Hides failures, breaks per-process limits | One process per container, separate services in compose |
| `restart: on-failure:3` on a service | Gives up and stays down | `restart: unless-stopped` + healthcheck |
| No limits in compose | A leak brings down the host. Runtimes size themselves for the host | `deploy.resources.limits` + runtime tuning (`references/runtime-performance.md`) |
| Logs with no rotation | Fills the disk | `logging.options.max-size`/`max-file` |
| Global `ARG` used inside `RUN` without re-declaring it | Expands to empty, fails silently | `ARG NAME` again after the stage's `FROM` |
| `GOARCH=amd64` hardcoded | Breaks multi-arch | `FROM --platform=$BUILDPLATFORM` + `TARGETARCH` |
