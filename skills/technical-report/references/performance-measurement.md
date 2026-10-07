# Performance measurement — protocol for any number

Applies to every time, memory, CPU, byte, or cost number that goes into a report: mode B
evidence, the mode C before/after table, and the mode A validation plan. A number without a
declared protocol is not evidence — it is `[modeled]`.

It does not apply to the **Effort** and **Coverage** metadata: those are estimates of human work,
governed by the typography in `conventions.md` (`5–7 dev-days`, `~35% (3 of 8 tasks)`).

## Contents

- 1. Bottleneck first
- 2. What to declare in every measurement
- 3. Minimum statistics
- 4. Explain the number — active benchmarking
- 5. Efficiency per unit of work
- 6. One change at a time
- 7. The seven questions before publishing a number
- 8. Anti-methods
- 9. Tools per stack
- Sources

## 1. Bottleneck first

Before proposing an optimization, name the resource that limits. For each resource (CPU, memory,
disk, network, connection pool, locks), check **Utilization, Saturation, and Errors** — the USE
method. For request-driven services, measure **Rate, Errors, and Duration** together — the RED
method; latency without an error rate misleads, because fast errors lower the average.

Optimizing what is not the bottleneck does not change the result (Amdahl's law): if the network
is 80% of the time, halving the CPU gains at most 10%.

## 2. What to declare in every measurement

In a table column or in the paragraph right below it:

- **Environment** — machine or runner type, OS, runtime version, production build or not,
  throttling applied (e.g. CPU 4×, 4G network).
- **Tool and exact command** — reproducible by someone else.
- **n** — number of runs per configuration. Minimum **10**; below that, state n and treat the
  difference as indicative.
- **Warm-up** — how many runs were discarded and why (JIT, disk cache, CPU frequency ramping up).
- **State** — hot or cold (cache cleared, first load, freshly started container).
- **Noise** — what was controlled (CPU governor, turbo boost, other processes, container
  neighbors) and what was **not**. Uncontrolled noise is declared too.

## 3. Minimum statistics

- Latency the user feels: **median and p95** (p99 when n is large enough). Throughput and CPU:
  mean ± standard deviation.
- A difference between before and after is only claimed with dispersion or a confidence
  interval, or with the tool's statistical verdict (`benchstat` p-value, `criterion` change).
- **Do not repeat the measurement until it "turns significant"**: rerunning until the result is
  pleasing is multiple testing and invalidates the p-value. Set n beforehand, run once.
- Outliers: exclude only by a declared rule (e.g. IQR fences) and say how many were removed.
- A change smaller than the noise measured between two runs of the **same** code is "no change".

## 4. Explain the number — active benchmarking

Every relevant number comes with the answer to **"why is it this value and not double?"**: which
resource hit its limit during the measurement. That requires observing the system *while* the
measurement runs (per-core CPU usage, GC, syscalls, I/O, long tasks), not just reading the final
result.

A claim about **why** something is slow requires a profiling artifact — flame graph, `perf`,
`pprof`, browser trace — and points to the specific frame or span, not the whole chart:
*"`JSON.parse` in `parseChapter` takes 41% of CPU samples (trace `scroll-5s.json`)"*.

## 5. Efficiency per unit of work

The gain that matters is the one **per unit of work delivered**, not the absolute one — the
absolute mixes scale with efficiency. Include at least one normalized row in the table:

| Resource | Normalized unit |
|---|---|
| CPU | requests/s per core · CPU ms per request |
| Memory | MB per request or per connection · peak heap per open document |
| Network/bundle | kB transferred per navigation · kB of JS per route |
| CI | runner minutes per build · cost per pipeline run |
| Cloud | cost per thousand requests · cost per active user |

A recommendation that reduces a resource without worsening the user metric is a gain even with no
time gain: record it as such.

## 6. One change at a time

Measure → identify the bottleneck → change **one** thing → measure again with the same protocol.
Two changes in the same measurement make the gain unattributable: the report cannot say which of
the two worked, and one of them may be making things worse. In the backlog, coupled fixes are a
single unit and are measured together — and the text says so.

## 7. The seven questions before publishing a number

1. Why not double? — which resource is limiting (§4).
2. Was it configured as in production? — build, flags, data size.
3. Did it cross any limit? — exhausted memory, swap, a full queue distort everything.
4. Were there errors? — count them along with the time.
5. Does it reproduce? — another independent run gives the same result within the dispersion.
6. Does it matter? — the measured load represents real use, not the synthetic best case.
7. Did it actually happen? — the claimed code path was exercised (no cache short-circuiting, no
   code eliminated by the compiler).

## 8. Anti-methods

- **Streetlight** — measuring what is easy to measure, not what limits.
- **Blame someone else** — attributing the cost to a component without USE/RED pointing to it.
- **Random change** — tweaking settings until the number improves, with no hypothesis.
- **Passive benchmarking** — publishing the tool's number without observing the system during
  the run.

## 9. Tools per stack

| Stack | Tool | Minimum correct use |
|---|---|---|
| Any command | `hyperfine` | `--warmup 3 --runs 10 --export-json out.json`; `--prepare` for a cold state |
| Go | `go test -bench` + `benchstat` | `-count=10` on before and after; `benchstat old.txt new.txt` gives the p-value |
| Rust | `criterion` | change report with a confidence interval; noise below the threshold = no change |
| Python | `pyperf` | `python -m pyperf system tune` first; `pyperf compare_to` for the verdict |
| C++ | `google/benchmark` | `--benchmark_repetitions=10 --benchmark_report_aggregates_only=true`; mind the CPU scaling warning |
| Browser | DevTools trace / Lighthouse | profile with declared throttling; long tasks > 50 ms; median of ≥ 5 Lighthouse runs |
| System | `perf`, `pprof`, flame graphs | attach the file and cite the frame |

Attach the raw output (JSON, benchmark `.txt`, trace file) or the path where it is. A summary
table without the raw output is not reproducible.

## Sources

- Brendan Gregg — The USE Method: https://www.brendangregg.com/usemethod.html
- Brendan Gregg — Active Benchmarking: https://www.brendangregg.com/activebenchmarking.html
- Brendan Gregg — Benchmarking Checklist: https://www.brendangregg.com/blog/2018-06-30/benchmarking-checklist.html
- Tom Wilkie — The RED Method: https://grafana.com/blog/the-red-method-how-to-instrument-your-services/
- hyperfine: https://github.com/sharkdp/hyperfine
- benchstat: https://pkg.go.dev/golang.org/x/perf/cmd/benchstat
- criterion.rs — analysis: https://bheisler.github.io/criterion.rs/book/analysis.html
- pyperf — system tuning: https://pyperf.readthedocs.io/en/latest/system.html
- google/benchmark — reducing variance: https://github.com/google/benchmark/blob/main/docs/reducing_variance.md
- Green Software Foundation — SCI (cost per functional unit): https://github.com/Green-Software-Foundation/sci
