# Runtime performance with minimal resources

The goal is to use the **smallest** CPU and memory limit that holds the load with stable latency. Almost every problem here comes from one thing: **the runtime sees the host (16, 64 cores, hundreds of GB) and not the container limit**. It sizes threads, workers and heap for the wrong machine. The result is CPU throttling (CFS quota exhausted → latency spikes) or an OOM kill.

## 1. Measure before you size

```bash
docker stats --no-stream                        # real CPU% and MEM of each container
docker run --cpus=1 -m 256m --memory-swap 256m ...   # reproduce the production limit locally (no swap)
docker inspect -f '{{.State.OOMKilled}}' <ctr>  # was it an OOM kill?
cat /sys/fs/cgroup/cpu.stat                     # inside the container: nr_throttled / throttled_usec
```

Sizing loop: start at `idle RSS × 2` for memory and `1` CPU. Run a load test (k6, wrk, hey), watch `nr_throttled` and p99 latency, and raise the limit only when the metrics call for it.

- **Memory limit** = hard limit. Going over means an OOM kill (exit 137, `OOMKilled: true`). Leave 20–30% headroom above the peak. On a host with swap, the limit alone also grants the same amount of swap (measured: `-m 256m` → `memory.swap.max` = 256 MB), so the process slows down swapping instead of being killed, and a local test doesn't reproduce a host without swap. Set `--memory-swap` (compose: `memswap_limit`) equal to the memory limit.
- **Memory reservation** = soft limit, used for scheduling and reclaim under host pressure. Set it to the typical usage.
- **CPU (`cpus: 0.5`)** = CFS quota. Going over doesn't kill the process, it **throttles** it. For latency-sensitive workloads, throttling hurts more than it seems: a GC that uses 8 threads burns a 1-CPU quota in 12 ms and freezes the process for the rest of the 100 ms period.
- **`pids_limit`** protects against fork bombs and thread leaks (e.g. 256–512 for a normal service).

## 2. Is each runtime aware of the limit? (measured on Engine 29.7, cgroup v2)

| Runtime | CPU | Memory | Required action |
|---|---|---|---|
| **Go ≥ 1.25** | Yes: `GOMAXPROCS` = CPU limit (**floor of 2**: `--cpus=1` → 2) | No: the GC doesn't know the limit | `GOMEMLIMIT` ≈ 90% of the limit. Below 2 CPUs `GOMAXPROCS` stays at 2 (`--cpus=0.5` → 2): see §3 before forcing 1. Go < 1.25: set `GOMAXPROCS` or use `automaxprocs` |
| **Rust (tokio)** | Yes: `available_parallelism()` = limit (`--cpus=2` → 2) | n/a (no GC) | None. Watch the allocator with musl |
| **Node.js 24** | n/a (1 JS thread; libuv pool = 4) | **Partially**: the default heap is about half the limit, with a floor of ~259 MB and a cap of ~2.2 GB (`-m 256m` and `-m 512m` → 259 MB, `-m 1g` → 560 MB, `-m 8g` → 2240 MB) | `NODE_OPTIONS=--max-old-space-size-percentage=75` (`-m 512m` → 387 MB on 22.23 and 24.22), or `--max-old-space-size=<75% of the limit in MB>` on a release without that flag. `UV_THREADPOOL_SIZE` only if you do a lot of fs/crypto/dns |
| **Python** | **No**: `os.cpu_count()` = host cores (16 with `--cpus=2`) | No | Set `--workers` explicitly. Never compute workers from `cpu_count()` inside the container. For libraries that size their own pools from it, `PYTHON_CPU_COUNT=<limit>` (3.13+) makes `os.cpu_count()` return that value (measured: 16 → 2) |
| **Java ≥ 17** | Yes: `availableProcessors()` follows the CPU limit | Yes, but the default heap is **25%** of the limit | `-XX:MaxRAMPercentage=75`. See §3 |

## 3. Per-language tuning

### Go
```dockerfile
ENV GOMEMLIMIT=460MiB   # for memory: 512M
# GOMAXPROCS is automatic (1.25+), with a floor of 2
```
With a limit below 2 CPUs the runtime still runs 2 threads. `GOMAXPROCS=1` removes that mismatch, but then the GC shares the only thread with the application. Force it only if `nr_throttled` keeps growing under load, and compare p99 before and after.

Static binary + distroless/static: idle RSS measured at 4.8 MiB. Go is the best language for "minimal resources".

### Node.js
```dockerfile
ENV NODE_OPTIONS="--max-old-space-size-percentage=75"   # 75% of the container limit, whatever it is
```
- On a Node release without that flag, use megabytes: `--max-old-space-size=384` for `memory: 512M`.
- 1 process per container, and scale horizontally through replicas. Avoid `cluster`/PM2 inside the container (it duplicates what the orchestrator already does, and the heap limit is per process).
- A handler for `SIGTERM`, or `init: true` (without it `docker stop` waits 10 s and SIGKILLs).

### Python
- Async (FastAPI/uvicorn): `--workers` = CPU limit (1–2). Sync (gunicorn): `--workers N --threads M`, with `N ≈ CPUs` and `M` sized for I/O.
- Memory ≈ `workers × RSS per worker` (35–60 MiB for a small FastAPI app) + 30%.
- `gunicorn --preload` shares code between workers through copy-on-write (less RSS).
- `--max-requests 1000 --max-requests-jitter 100` in gunicorn contains leaks from third-party libraries.
- `PYTHONUNBUFFERED=1`, and bytecode precompiled at build time (`UV_COMPILE_BYTECODE=1` or `python -m compileall`) so read-only containers don't try to write `.pyc`.

### Java
```dockerfile
ENV JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=75 -XX:+ExitOnOutOfMemoryError"
```
- Measured with `-m 512m`: max heap 123 MB by default (25%), **371 MB** with `MaxRAMPercentage=75`. The remaining 25% covers metaspace, thread stacks, code cache and direct buffers. Raise it to 80% only if the app has few threads and little off-heap memory.
- `availableProcessors()` respects `--cpus` (measured: 2). The JVM picks SerialGC by itself with < 2 CPUs or < 1792 MB, which is fine for small containers.
- A jlink custom JRE cuts the image from 130 MB to 86 MB (compressed) compared with `temurin:25-jre`.
- Startup: the AOT cache (Java 25, JEP 483/514/515) took Spring Boot from 1.8 s to 1.3 s. CDS/AppCDS on older versions. GraalVM native-image for scale-to-zero. See `examples/java.md`.

### Rust
Nothing is needed for CPU. For musl builds, use `mimalloc` (or `jemalloc`): musl's default allocator degrades under many threads.

## 4. Image size also affects resources

- **Pull/startup time**: a 57 MB compressed image starts on a new node in seconds, one of 429 MB takes a lot longer. That matters for autoscaling and rollouts.
- **Disk and registry**: every version is stored. Smaller images = cheaper registry, faster cache.
- **Attack surface and CVEs**: fewer packages = fewer patches and restarts.

## 5. Startup time

- Precompiled bytecode (Python), AOT cache / CDS (Java), no work in `ENTRYPOINT` (no `npm install` or migrations on startup, which belong in a separate job).
- `HEALTHCHECK --start-period` sized for the real startup, so a slow boot isn't marked unhealthy.
- A small image + dependency layers shared between services (same base, same digest) → nodes reuse the layers they already have.
