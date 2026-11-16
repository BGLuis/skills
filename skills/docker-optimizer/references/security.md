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
| Read-only rootfs | `read_only: true` + `tmpfs: ["/tmp:size=64m"]` | `--read-only --tmpfs /tmp:size=64m` |
| Process limit | `deploy.resources.limits.pids` | `--pids-limit` |
| Ports on localhost only | `"127.0.0.1:8080:8080"` | `-p 127.0.0.1:8080:8080` |

Never: `privileged: true`, `/var/run/docker.sock` mounted (equivalent to root on the host), `network_mode: host` without need, disabling seccomp/AppArmor (`seccomp:unconfined`).

## 4. Supply chain

- **Pin by digest** + automated updates (Dependabot `package-ecosystem: docker`, Renovate). `FROM name:tag@sha256:...` works with `--pull` (measured).
- **Minimal base** = fewer CVEs. Measured with trivy (HIGH+CRITICAL): `node:24` naive → **483** CVEs in OS packages + 4 in npm packages. The distroless version of the same app → **0**.
- **Docker Hardened Images** (`dhi.io`): free and Apache 2.0 since Dec/2025. Near-zero CVEs, SBOM, SLSA Build Level 3 provenance, VEX, fixes within 7 days. A good default when the organization accepts it. Pulling requires a Docker Hub login.
- **SBOM and provenance**: `docker buildx build --sbom=true --provenance=mode=max`. Measured: it works with `--load` on the default `docker` driver when the daemon uses the containerd image store. Inspect it after pushing to a registry: `docker buildx imagetools inspect <ref> --format '{{json .SBOM}}'` (`.Provenance` for SLSA). `imagetools` only reads from a registry, not from the local store.
- **Signing**: `cosign sign <ref>@<digest>` (keyless via OIDC in CI) and verification at deploy time.
- **The tools are part of the supply chain too.** `aquasec/trivy` on Docker Hub served malware under `latest` and `0.69.4`–`0.69.6` between 19 and 23 March 2026 ([Docker's advisory](https://www.docker.com/blog/trivy-supply-chain-compromise-what-docker-hub-users-should-know/)). Pin scanners and linters by version and digest like any base image, and don't hand them the Docker socket (§5).
- `ADD --checksum=sha256:... <url>` when downloading artifacts in the build.
- `npm ci --ignore-scripts` / `pip install --only-binary=:all:` reduce execution of third-party code during the build.

## 5. Scanning

```bash
# Trivy (no install needed). Pinned by version + digest, reading a tar instead of the Docker socket.
docker save app:tag -o app.tar
docker run --rm -v "$PWD/app.tar:/app.tar:ro" \
  aquasec/trivy:0.76.2@sha256:8f6bb947dbc528902e11f2f5be52f7b519f6a39d5d148f41166f2040499768fb \
  image --input /app.tar --severity HIGH,CRITICAL --ignore-unfixed
rm app.tar

# Docker Scout (CLI plugin; comes with Docker Desktop, install it separately on Engine)
docker scout quickview app:tag
docker scout recommendations app:tag   # suggests a smaller or more up-to-date base image

# hadolint (lint beyond build checks: DL3007 latest, DL3008 apt pin, DL3015 recommends, DL3025 JSON CMD)
docker run --rm -i \
  hadolint/hadolint:v2.15.1@sha256:32dac94127fd60b7b7e3fbfc65e1383b9b5e25c9bfd7b8536de7a539fe68a12d < Dockerfile
```

The versions above were checked in 2026-11. Take a newer one from the project's releases and its digest from `docker buildx imagetools inspect <image>:<version>`.

In CI: fail on fixable CRITICAL (`--exit-code 1 --ignore-unfixed`), and re-scan published images daily (new CVEs show up in images that don't change).
