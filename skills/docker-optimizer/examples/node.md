# Node.js (TypeScript) — production Dockerfile

Validated with Docker Engine 29.7 (`docker build --check`: no warnings). Test app: Fastify with TypeScript, eslint and @types/node as devDependencies.

| | Naive (`FROM node`, `npm install`, `npm start`) | This file |
|---|---|---|
| Compressed image | 429 MB | **57 MB** |
| On disk | 1.72 GB | 236 MB |
| `node_modules` shipped | 58 MB (with devDependencies) | 12.4 MB (`--omit=dev`) |
| `docker stop` | exit code 1 (npm in the middle) | 216 ms, exit 0 |
| User | root | 65532 (`nonroot`) |

## Why it looks like this

1. **Three stages**. `deps` installs **production dependencies only** (`npm ci --omit=dev`). `build` installs everything and compiles. `runtime` copies `node_modules` from `deps` and `dist` from `build`. Copying `node_modules` from the compile stage ships TypeScript, eslint and the rest into production.
2. **`package.json` and the lockfile are bind-mounted**, not copied. The `npm ci` layer only changes when they change, and they don't become stray layers.
3. **`--mount=type=cache,target=/root/.npm`**: rebuilds reuse downloaded tarballs.
4. **`--ignore-scripts`** blocks postinstall scripts from dependencies (supply chain). Remove it only if a dependency really needs a native build step (such as `sharp` or `bcrypt`). In that case build in `deps` with `node:*-slim` (glibc) and copy the result.
5. **Distroless nodejs**: its entrypoint is already `node`, so `CMD` holds only the script. No shell, no npm, and `nonroot` by default. Files stay owned by root and read-only for the process. Don't use `--chown` unless the app writes to that directory.
6. **Never `CMD ["npm", "start"]`**. npm adds an extra process in the signal path. Measured: exit code 1 on `docker stop`, while `node` directly exits with 0.

## PID 1 and signals (measured)

When Node runs as PID 1 **without a `SIGTERM` handler**, it ignores the signal. `docker stop` waits the full 10 s and SIGKILLs it (exit 137). With `--init` (or `init: true` in compose), it stops in 231 ms. Either handle `SIGTERM` in code (below) or run the container with `init`.

```js
const close = async () => { await app.close(); process.exit(0); };
process.on("SIGTERM", close);
process.on("SIGINT", close);
```

## Memory (measured on Node 24)

V8 sizes the heap from the cgroup limit, but it does not leave headroom. With `-m 256m`, the heap limit came out as **259 MB**, bigger than the container itself, so the kernel kills the process before the GC reacts. With `-m 1g` it came out as 560 MB. **Always** set `NODE_OPTIONS=--max-old-space-size=<~75% of the limit in MB>`. With 256 MB → `192`, measured heap limit 195 MB.

## Code

```dockerfile
# syntax=docker/dockerfile:1

ARG NODE_VERSION=24

FROM node:${NODE_VERSION}-trixie-slim AS base
WORKDIR /app

# Production dependencies only: this is what ships.
FROM base AS deps
RUN --mount=type=cache,target=/root/.npm \
    --mount=type=bind,source=package.json,target=package.json \
    --mount=type=bind,source=package-lock.json,target=package-lock.json \
    npm ci --omit=dev --ignore-scripts

# Full install (incl. devDependencies) + compile.
FROM base AS build
RUN --mount=type=cache,target=/root/.npm \
    --mount=type=bind,source=package.json,target=package.json \
    --mount=type=bind,source=package-lock.json,target=package-lock.json \
    npm ci --ignore-scripts
COPY . .
RUN npm run build

FROM gcr.io/distroless/nodejs${NODE_VERSION}-debian13:nonroot AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY package.json ./
EXPOSE 3000
# The distroless entrypoint is already `node`; CMD holds only the script.
CMD ["dist/index.js"]
```

`.dockerignore`:

```
.git
node_modules
dist
coverage
*.log
.env*
Dockerfile*
.dockerignore
```

## Variants

- **pnpm**: `RUN corepack enable` in `base`. Cache mount `target=/root/.local/share/pnpm/store`. Use `pnpm install --frozen-lockfile --prod` in `deps`. Plain JavaScript (no build step): drop the `build` stage and copy `src/` from the context.
- **Plain JavaScript, no build**: `deps` + runtime only. `COPY src ./src`.
- **Need a shell in production** (entrypoint scripts): use `node:24-trixie-slim` as runtime with `USER node` (UID 1000). It is bigger than distroless, but still has no devDependencies.
- **Healthcheck**: distroless has no `curl`. Use `HEALTHCHECK CMD ["/nodejs/bin/node", "-e", "fetch('http://127.0.0.1:3000/healthz').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"]`, or leave the health check to the orchestrator.
