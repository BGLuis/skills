# Python (uv) — production Dockerfile

Validated with Docker Engine 29.7 (`docker build --check`: no warnings). Test app: FastAPI + uvicorn, with pytest/ruff/mypy as the dev group.

| | Naive (`FROM python`, `COPY . .`, `uv sync`) | This file |
|---|---|---|
| Compressed image | 524 MB | **49 MB** |
| On disk | 2.01 GB | 200 MB |
| Idle RSS | — | 37 MiB |
| `docker stop` | — | 593 ms, exit 0 |
| User | root | 10001 |

Based on [`astral-sh/uv-docker-example`](https://github.com/astral-sh/uv-docker-example) and the uv Docker guide.

## Why it looks like this

1. **Two-step `uv sync`**. The first runs with `--no-install-project`, so only the dependencies are installed, from `uv.lock` + `pyproject.toml` bind mounts. Then the source is copied and the project is installed. Code changes don't reinstall the dependencies.
2. **`--locked`** fails the build if `uv.lock` is out of sync with `pyproject.toml` (reproducible). **`--no-dev`** leaves the dev group out.
3. **`UV_COMPILE_BYTECODE=1`** writes the `.pyc` files at build time, so a `read_only: true` container doesn't try to write them at runtime. **`UV_LINK_MODE=copy`** is needed because the cache is a separate mount (hardlinks are impossible). **`UV_PYTHON_DOWNLOADS=never`** makes uv use the image's interpreter.
4. **Only the `.venv` goes to runtime**. uv, the cache and the source outside the venv stay in the build stage. `--no-editable` installs the project itself into the venv, so the source tree is not needed at runtime.
5. **Same interpreter in both stages** (`python:X-slim-trixie`). A venv holds absolute paths to the Python it was built with.
6. **Static UID/GID (10001)** created with `--no-log-init` (avoids huge sparse lastlog files with high UIDs).

## Why not `gcr.io/distroless/python3`

That image ships **Debian's Python** (3.13 on debian13), not the one from `python:3.14`. A venv built against another interpreter breaks. For distroless, use a Python managed by uv: `uv python install` in the build stage, copy the interpreter together with the venv, and use runtime `gcr.io/distroless/cc-debian13:nonroot`. This saves roughly 30–40 MB more, but you lose a shell for debugging. Keep slim as the default.

## Runtime and resources

- **`os.cpu_count()` ignores the container CPU limit**. Measured with `--cpus=2` on a 16-core host: `os.cpu_count()` = 16, `os.process_cpu_count()` = 16. Formulas like `workers = 2*cpu+1` spawn about 33 workers into a 2-CPU container. **Always set the worker count explicitly** from the configured limit (`--workers 2`, `WEB_CONCURRENCY=2`, `GUNICORN_CMD_ARGS="--workers 2"`).
- Each uvicorn/gunicorn worker is a full process (about 35–60 MiB for a small FastAPI app). Memory limit ≈ `workers × RSS per worker + ~30%`.
- For async (FastAPI/uvicorn), 1 worker per CPU is usually enough. For sync (Django/Flask + gunicorn), use `--workers N --threads M` instead of many processes.
- `PYTHONUNBUFFERED=1` makes logs show up immediately in `docker logs`.

## Code

```dockerfile
# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.14

FROM python:${PYTHON_VERSION}-slim-trixie AS build
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app
# Dependencies first: this layer survives source-code changes.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

FROM python:${PYTHON_VERSION}-slim-trixie AS runtime
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --no-log-init app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status == 200 else 1)"]
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

`.dockerignore`:

```
.git
.venv
**/__pycache__
**/*.pyc
.pytest_cache
.mypy_cache
.ruff_cache
.env*
Dockerfile*
.dockerignore
```

## pip instead of uv

If the project only has `requirements.txt`:

```dockerfile
RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    pip install -r requirements.txt
```

With a cache mount, **don't** use `--no-cache-dir`: the two cancel each other out. The cache doesn't go into the image, it lives in the mount. `--no-cache-dir` only makes sense without BuildKit.

If a dependency compiles C extensions, install `build-essential` **only in the build stage** (apt with cache mounts, see `references/dockerfile-rules.md`). The runtime stage gets only the shared libraries (`libpq5`, not `libpq-dev`).
