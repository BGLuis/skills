# Docker Compose — development

Validated with Compose 5.5 (`docker compose config -q` with no warnings). Editing `src/index.ts` changed the HTTP response in about 6 s, with no rebuild.

## Why it looks like this

1. **`dev` stage in the same Dockerfile** (`target: dev`). It has a shell, devDependencies and a watcher. The production stage stays untouched. One Dockerfile, two targets.
2. **`develop.watch` instead of a bind mount of the whole tree**:
   - `sync`: copies the changed file into the running container. The in-process watcher (`node --watch`, `uvicorn --reload`, `air`) reloads it.
   - `sync+restart`: syncs and restarts the container. Use it for config files that the process only reads at boot.
   - `rebuild`: rebuilds the image and recreates the container. Use it for the lockfile and manifests (new dependencies).
   Unlike a bind mount, `node_modules`/`.venv` inside the container are never overwritten by the host (different OS, native binaries), and on Docker Desktop you skip slow host↔VM I/O.
3. **The process watcher has to recompile or reinterpret the source**. `sync` of `.ts` with `CMD ["node", "dist/index.js"]` **does nothing useful**, because `dist/` isn't rebuilt. Use a watcher that runs the source directly: `node --watch src/index.ts` (Node 24 runs TypeScript natively by stripping the types), `tsx watch`, or `nodemon`.
4. **Limits in dev too**: they catch memory leaks before production, and they stop a runaway process from freezing the laptop.
5. **Ports on `127.0.0.1`**: the dev server isn't exposed to the café's network.

## Code

`Dockerfile` (dev stage, next to the production stages from `examples/node.md`):

```dockerfile
FROM base AS dev
ENV NODE_ENV=development
RUN --mount=type=cache,target=/root/.npm \
    --mount=type=bind,source=package.json,target=package.json \
    --mount=type=bind,source=package-lock.json,target=package-lock.json \
    npm ci
COPY . .
USER node
CMD ["node", "--watch", "src/index.ts"]
```

`compose.yaml`:

```yaml
services:
  api:
    build:
      context: .
      target: dev
    ports:
      - "127.0.0.1:3000:3000"
    init: true
    environment:
      DEBUG: "app:*"
    develop:
      watch:
        - action: sync
          path: ./src
          target: /app/src
        - action: rebuild
          path: package-lock.json
    deploy:
      resources:
        limits:
          cpus: "1"
          memory: 1G
```

Run it with `docker compose up --watch` (or `docker compose watch`).

## Equivalents in other languages

| Language | Dev `CMD` | `sync` | `rebuild` |
|---|---|---|---|
| Python (uv) | `["uv", "run", "fastapi", "dev", "--host", "0.0.0.0"]` or `uvicorn --reload` | `./src` → `/app/src` | `uv.lock`, `pyproject.toml` |
| Go | `["air"]` (install `github.com/air-verse/air` in the dev stage) | `.` → `/src` | `go.mod`, `go.sum` |
| Java (Spring) | `["./mvnw", "spring-boot:run"]` with devtools | `./src` → `/src/src` | `pom.xml` |
| Rust | `["cargo", "watch", "-x", "run"]` | `./src` → `/app/src` | `Cargo.toml`, `Cargo.lock` |

In dev, running a package manager as PID 1 (`uv run`, `mvnw`) is acceptable. In production it is not.

## Docker Desktop (macOS/Windows)

If you really do need a bind mount (for example tooling that expects the files on the host), turn on **VirtioFS** / *synchronized file shares* in Docker Desktop's settings. That is a Desktop setting, not a compose field. On Linux, bind mounts are native and fast.
