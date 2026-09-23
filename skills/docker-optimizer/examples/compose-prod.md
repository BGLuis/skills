# Docker Compose — production (single host)

Validated with Engine 29.8 / Compose 5.5. With plain `docker compose up -d` (**no Swarm**), every field below showed up in `docker inspect` and all three services (Go distroless, Node distroless, Python slim) reached `healthy` with `read_only` + `cap_drop: [ALL]` + non-root.

## Code

```yaml
name: app

x-hardening: &hardening
  read_only: true
  tmpfs:
    - /tmp
  cap_drop: [ALL]
  security_opt:
    - "no-new-privileges:true"
  init: true
  restart: unless-stopped
  logging:
    driver: json-file
    options:
      max-size: "10m"
      max-file: "3"

services:
  api:
    <<: *hardening
    image: registry.example.com/api@sha256:<digest>   # the same digest that passed staging
    user: "65532:65532"
    ports:
      - "127.0.0.1:8080:8080"   # the reverse proxy on the host is the only one exposed
    environment:
      GOMEMLIMIT: 115MiB        # ~90% of the limit
    stop_grace_period: 10s
    # distroless without a shell: the image's HEALTHCHECK calls `/server healthcheck`
    deploy:
      resources:
        limits: { cpus: "0.50", memory: 128M, pids: 100 }
        reservations: { memory: 64M }
    depends_on:
      db:
        condition: service_healthy

  web:
    <<: *hardening
    image: registry.example.com/web@sha256:<digest>
    user: "65532:65532"
    ports:
      - "127.0.0.1:3000:3000"
    environment:
      NODE_OPTIONS: "--max-old-space-size=192"   # ~75% of 256M (the V8 default would be 259 MB)
    healthcheck:
      test: ["CMD", "/nodejs/bin/node", "-e", "fetch('http://127.0.0.1:3000/healthz').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"]
      interval: 10s
      timeout: 3s
      start_period: 10s
      retries: 3
    deploy:
      resources:
        limits: { cpus: "0.50", memory: 256M, pids: 100 }
        reservations: { memory: 96M }
    depends_on:
      api:
        condition: service_healthy

  db:
    image: postgres:18-trixie
    # Postgres needs to write data and run its entrypoint as root before dropping to `postgres`:
    # no read_only / cap_drop ALL here. Keep only the options that don't break it.
    security_opt:
      - "no-new-privileges:true"
    restart: unless-stopped
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets: [db_password]
    volumes:
      - db-data:/var/lib/postgresql
    shm_size: 128m
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 10
    logging:
      driver: json-file
      options: { max-size: "10m", max-file: "3" }
    deploy:
      resources:
        limits: { cpus: "1", memory: 512M }

secrets:
  db_password:
    file: ./secrets/db_password.txt

volumes:
  db-data:
```

Bring it up with `docker compose up -d --wait`. The command blocks until everything is `healthy`, and fails fast (exit 1, `container <name> is unhealthy`) if a service goes unhealthy. That makes it good for deploy scripts.

## Validated evidence

| Field | Observed in `docker inspect` |
|---|---|
| `deploy.resources.limits` cpus/memory/pids | `NanoCpus=500000000`, `Memory=134217728`, `PidsLimit=100` |
| `reservations.memory` | `MemoryReservation=67108864` |
| `read_only` + `tmpfs` | `ReadonlyRootfs=true`, `/tmp` tmpfs `rw,nosuid,nodev,noexec`. Writing to `/` → `Read-only file system` |
| `cap_drop`, `security_opt`, `init` | `CapDrop=[ALL]`, `SecurityOpt=[no-new-privileges:true]`, `Init=true` |
| `logging` | `LogConfig={Type:json-file, max-size:10m, max-file:3}` (the daemon default has **no** rotation) |
| `restart: unless-stopped` | `RestartPolicy={Name:unless-stopped}` |
| `depends_on: service_healthy` | the dependent service waits for `Healthy` from the dependency, including when the healthcheck comes from the image's `HEALTHCHECK` |
| ports `127.0.0.1:` | `HostIp=127.0.0.1`, not reachable from outside |

## Decisions and why

- **`deploy.resources` vs `mem_limit`/`cpus`/`pids_limit`**: both work outside Swarm. Pick **one**. Setting both with different values is a hard error: `can't set distinct values on 'cpus' and 'deploy.resources.limits.cpus'`.
- **`restart: unless-stopped`** for services. `on-failure:3` gives up after 3 failures and leaves the service down. Use it only for jobs, or when an external supervisor exists.
- **Log rotation is mandatory**. The daemon's default `json-file` grows without limit and fills the disk. Alternatively, configure `"log-opts"` in `/etc/docker/daemon.json` for the whole host, or use the `local` driver (compressed, rotated by default).
- **`read_only` + `tmpfs`**: an attacker can't persist files, and the app can't create state by accident. If the app writes cache or uploads, mount a specific volume or tmpfs (`/app/cache`), and never turn off `read_only` for the whole container.
- **Secrets through `secrets:` (files in `/run/secrets/`)**, never plain text in `environment:`. Environment variables show up in `docker inspect` and leak into child processes.
- **No `version:`**. The field is obsolete and Compose warns about it.
- **Images by digest** (`image@sha256:`), promoted from staging. Don't `build:` on the production server.
- **One process per container.** Don't put supervisord/PM2 inside the container. Use separate services and `depends_on`.
