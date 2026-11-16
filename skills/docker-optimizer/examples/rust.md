# Rust — production Dockerfile

Validated with Docker Engine 29.7 (`docker build --check`: no warnings). Test app: axum + tokio with graceful shutdown.

| | Naive (`FROM rust`, `COPY . .`, `cargo build`) | This file |
|---|---|---|
| Compressed image | 644 MB | **11 MB** |
| On disk | 2.53 GB | 44.6 MB |
| Rebuild after changing only `src/` | 22 s (recompiles every crate) | **8 s** (dependencies CACHED) |
| Idle RSS | — | 0.7 MiB |
| `docker stop` | — | 294 ms, exit 0 |

## Why it looks like this

1. **[`cargo-chef`](https://github.com/LukeMathWalker/cargo-chef)**. `prepare` turns `Cargo.toml` and `Cargo.lock` into a `recipe.json` of the dependencies. `cook` compiles only those dependencies in a separate layer. That layer stays cached until the dependencies change, **including in CI with a remote cache** (see `references/ci-cache.md`). A cache mount on `target/` does not survive a remote cache.
2. **Cache mounts on the cargo registry and git** with `sharing=locked`: rebuilds don't download crates again, and parallel builds don't corrupt the index.
3. **Release profile** tuned for size and speed: `lto = "thin"`, `codegen-units = 1`, `strip = true`. `panic = "abort"` shrinks the binary a little more (the numbers above include it), but then a panic in one request handler kills the whole server instead of only that task. Add it only when that is acceptable.
4. **`distroless/cc:nonroot`**: glibc + libgcc, no shell, UID 65532. Use it for dynamic glibc binaries (the Rust default). For `scratch` or `distroless/static`, build with `--target x86_64-unknown-linux-musl`. musl's allocator is slower under concurrency, so pair it with `mimalloc` or `jemalloc` if performance matters.
5. `std::thread::available_parallelism()` **respects the cgroup CPU limit**. Measured: `--cpus=2` → 2, so tokio sizes its worker pool correctly with no tuning.

## Code

```toml
# Cargo.toml
[profile.release]
lto = "thin"
codegen-units = 1
strip = true
```

```dockerfile
# syntax=docker/dockerfile:1

FROM lukemathwalker/cargo-chef:0.1.78-rust-1.100-slim-trixie AS chef
WORKDIR /app

# Compute a dependency-only "recipe" from Cargo.toml/Cargo.lock.
FROM chef AS planner
COPY . .
RUN cargo chef prepare --recipe-path recipe.json

FROM chef AS build
COPY --from=planner /app/recipe.json recipe.json
# Dependencies only: cached until Cargo.toml/Cargo.lock change.
RUN --mount=type=cache,target=/usr/local/cargo/registry,sharing=locked \
    --mount=type=cache,target=/usr/local/cargo/git,sharing=locked \
    cargo chef cook --release --locked --recipe-path recipe.json
COPY . .
RUN --mount=type=cache,target=/usr/local/cargo/registry,sharing=locked \
    --mount=type=cache,target=/usr/local/cargo/git,sharing=locked \
    cargo build --release --locked --bin api

# glibc + libgcc, no shell, UID 65532.
FROM gcr.io/distroless/cc-debian13:nonroot AS runtime
COPY --from=build /app/target/release/api /usr/local/bin/api
EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/api"]
```

`.dockerignore`:

```
.git
.env*
target
Dockerfile*
.dockerignore
```

`.env*` matters here more than elsewhere: `COPY . .` puts the whole context into build-stage layers, and `--cache-to ...,mode=max` pushes those layers to the registry.

Graceful shutdown (without it, `docker stop` waits 10 s and SIGKILLs):

```rust
axum::serve(listener, app)
    .with_graceful_shutdown(async {
        let mut term = tokio::signal::unix::signal(SignalKind::terminate()).unwrap();
        tokio::select! { _ = tokio::signal::ctrl_c() => {}, _ = term.recv() => {} }
    })
    .await?;
```

The `cargo-chef` tag carries both versions (`<cargo-chef>-rust-<rust>-slim-trixie`). Take the Rust version from the project's `rust-toolchain.toml`, pick the current `cargo-chef` release, and add the digest in real projects. The `latest-*` tags exist, but they change both versions under you.
