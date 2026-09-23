# Docker Compose — rules

Templates: `examples/compose-dev.md` and `examples/compose-prod.md`. Both were validated end to end (Compose 5.5): `config -q` with no warnings, `up --wait` with every service `healthy`.

## Structure

- File name: `compose.yaml`. **No `version:` key** (obsolete).
- Split dev/prod with `compose.yaml` (base) + `compose.override.yaml` (dev, applied automatically) or `-f compose.prod.yaml`. Alternatively, use separate files when the two differ a lot.
- Reuse repeated blocks with extension fields + YAML anchors (`x-hardening: &hardening` → `<<: *hardening`).
- Interpolate with `${VAR:?error}` for mandatory variables. The `.env` file next to the compose file only fills in interpolation, it does not reach the containers (that is `env_file:`).

## Resources (validated outside Swarm)

```yaml
deploy:
  resources:
    limits: { cpus: "0.50", memory: 256M, pids: 100 }
    reservations: { memory: 128M }
```

- Honored by plain `docker compose up` (`NanoCpus`, `Memory`, `PidsLimit`, `MemoryReservation` in `docker inspect`).
- The top-level form (`cpus`, `mem_limit`, `pids_limit`) is equivalent. **Don't mix the two** with different values: `can't set distinct values on 'cpus' and 'deploy.resources.limits.cpus'`.
- The limit alone isn't enough. Tune the runtime for it (Node heap, Python workers, JVM, GOMEMLIMIT). See `runtime-performance.md`.
- `deploy.replicas` works in Compose for stateless services without a fixed host port.

## Hardening (validated)

`read_only: true` + `tmpfs`, `cap_drop: [ALL]`, `security_opt: ["no-new-privileges:true"]`, `user: "UID:GID"`, `init: true`. Go, Node and Python apps reached healthy with all of them together. Exceptions: images whose entrypoint needs root to prepare the environment (Postgres, nginx upstream on port 80). For those, keep `no-new-privileges` and limits, and relax the rest, or use unprivileged variants (`nginxinc/nginx-unprivileged`).

## Health, order and deploy

- `healthcheck` in compose overrides the image's `HEALTHCHECK`. Without it, the image's one is used, and it works for `depends_on: condition: service_healthy`.
- Distroless: `test: ["CMD", "<binary>", ...]` (exec form). `CMD-SHELL` needs `/bin/sh`.
- `depends_on.<svc>.condition`: `service_healthy` (wait until healthy), `service_completed_successfully` (migration/seed jobs), `service_started`.
- `docker compose up -d --wait [--wait-timeout N]` blocks until everything is healthy and fails fast (exit 1) on the first unhealthy service. Use it in deploy scripts.
- `restart: unless-stopped` for services, `"no"` for one-shot jobs.
- `stop_grace_period` ≥ the real graceful shutdown time (default 10 s).

## Logs

The daemon default (`json-file`) **has no rotation**. On each service (or globally in `/etc/docker/daemon.json`):

```yaml
logging:
  driver: json-file        # or "local": compressed, rotated by default
  options: { max-size: "10m", max-file: "3" }
```

## Network and ports

- Publish only what faces the outside world. Internal services (db, cache) don't get `ports:` and talk over the project network by service name.
- `"127.0.0.1:8080:8080"` when a reverse proxy runs on the host. A bare `"8080:8080"` listens on `0.0.0.0` and **bypasses UFW/firewalld** (Docker writes its own iptables rules).
- `networks:` with `internal: true` for backends with no internet egress.

## Development

- `build.target: dev` + `develop.watch` (`sync`, `sync+restart`, `rebuild`). See `examples/compose-dev.md`.
- `sync` only helps if the process inside reloads the source (`node --watch src/index.ts`, `uvicorn --reload`, `air`). If the `CMD` runs compiled artifacts, the sync has no effect.
- `docker compose watch` tears down the watched containers when it gets `SIGTERM`.
- Slow bind mounts on macOS/Windows: a Docker Desktop setting (VirtioFS / synchronized file shares), not a compose field.
