# Image and container security

Sources: [OWASP Docker Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html), [hexops/dockerfile](https://github.com/hexops-graveyard/dockerfile), [Docker Hardened Images](https://github.com/docker-hardened-images). Everything marked "measured" was validated on Engine 29.7.

## 1. User

- **Never root in the final stage.** Neither `docker build --check` nor hadolint flags a **missing** `USER`. hadolint DL3002 only fires on an explicit `USER root`. The skill has to check this itself.
- **Static UID/GID**, numeric in `USER` (`USER 10001:10001`). Kubernetes `runAsNonRoot` only validates a numeric UID. hexops recommends ≥ 10000 so the UID can't collide with a real host user if the container is escaped.
- Distroless/DHI `nonroot` = 65532. `node:*` has `node` = 1000.
- `useradd --no-log-init` (without it, a high UID generates a sparse `lastlog` file of GBs).
- `COPY --link --chown=<name>` on distroless **fails** (measured: `invalid user index: -1`), because `--link` doesn't read the target's `/etc/passwd`. Use the numeric form `--chown=65532:65532`. Better still, don't chown: root-owned files that the process can't write are safer.

## 2. Secrets

- **`RUN --mount=type=secret`**, never `ARG`/`ENV`:
  ```dockerfile
  RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci
  # docker build --secret id=npmrc,src=$HOME/.npmrc .
  RUN --mount=type=secret,id=gh_token,env=GH_TOKEN ./fetch-private.sh
  # docker build --secret id=gh_token,env=GH_TOKEN .
  ```
  Measured: with `ARG TOKEN` + `ENV TOKEN=$TOKEN`, the token shows up **3 times** in `docker history` and inside the `docker save` tar. With `--mount=type=secret`, 0 times.
- The secret's content **is not part of the cache key**. Rotating the token does not re-run the `RUN`. Use `--no-cache-filter <stage>` if you need to force it.
- `docker build --check` catches `SecretsUsedInArgOrEnv` from the variable **name** (`PASSWORD`, `API_KEY`, `TOKEN`...). It doesn't see secrets in `COPY .env`, so that's what `.dockerignore` is for.
- At runtime: compose `secrets:` (files in `/run/secrets/`) instead of `environment:` (visible in `docker inspect`).

## 3. Container privileges (runtime)

| Control | compose | `docker run` |
|---|---|---|
| Drop all capabilities | `cap_drop: [ALL]` (+ `cap_add: [NET_BIND_SERVICE]` only if it binds < 1024) | `--cap-drop ALL` |
| No escalation through setuid | `security_opt: ["no-new-privileges:true"]` | `--security-opt no-new-privileges` |
| Read-only rootfs | `read_only: true` + `tmpfs: [/tmp]` | `--read-only --tmpfs /tmp` |
| Process limit | `deploy.resources.limits.pids` | `--pids-limit` |
| Ports on localhost only | `"127.0.0.1:8080:8080"` | `-p 127.0.0.1:8080:8080` |

Never: `privileged: true`, `/var/run/docker.sock` mounted (equivalent to root on the host), `network_mode: host` without need, disabling seccomp/AppArmor (`seccomp:unconfined`).

## 4. Supply chain

- **Pin by digest** + automated updates (Dependabot `package-ecosystem: docker`, Renovate). `FROM name:tag@sha256:...` works with `--pull` (measured).
- **Minimal base** = fewer CVEs. Measured with trivy (HIGH+CRITICAL): `node:24` naive → **483** CVEs in OS packages + 4 in npm packages. The distroless version of the same app → **0**.
- **Docker Hardened Images** (`dhi.io`): free and Apache 2.0 since Dec/2025. Near-zero CVEs, SBOM, SLSA Build Level 3 provenance, VEX, fixes within 7 days. A good default when the organization accepts it. Pulling requires a Docker Hub login.
- **SBOM and provenance**: `docker buildx build --sbom=true --provenance=mode=max`. Measured: it works with `--load` on the default `docker` driver when the daemon uses the containerd image store. Inspect it after pushing to a registry: `docker buildx imagetools inspect <ref> --format '{{json .SBOM}}'` (`.Provenance` for SLSA). `imagetools` only reads from a registry, not from the local store.
- **Signing**: `cosign sign <ref>@<digest>` (keyless via OIDC in CI) and verification at deploy time.
- `ADD --checksum=sha256:... <url>` when downloading artifacts in the build.
- `npm ci --ignore-scripts` / `pip install --only-binary=:all:` reduce execution of third-party code during the build.

## 5. Scanning

```bash
# Trivy (no install needed)
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest \
  image --severity HIGH,CRITICAL --ignore-unfixed app:tag

# Docker Scout (CLI plugin; comes with Docker Desktop, install it separately on Engine)
docker scout quickview app:tag
docker scout recommendations app:tag   # suggests a smaller or more up-to-date base image

# hadolint (lint beyond build checks: DL3007 latest, DL3008 apt pin, DL3015 recommends, DL3025 JSON CMD)
docker run --rm -i hadolint/hadolint < Dockerfile
```

In CI: fail on fixable CRITICAL (`--exit-code 1 --ignore-unfixed`), and re-scan published images daily (new CVEs show up in images that don't change).
