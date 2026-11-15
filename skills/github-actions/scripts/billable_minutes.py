#!/usr/bin/env python3
"""Measures workflow runs the way references/review-checklist.md §2 defines it.

For each run id it prints wall-clock time, the sum of job durations, billable minutes
(every job rounded up to a whole minute) and the same in Linux-equivalent minutes, plus
the slowest step of every job. With three or more runs it adds the medians, which is
what to compare: hosted runners vary by up to about 2x between identical runs.

Usage: python3 billable_minutes.py OWNER/REPO RUN_ID [RUN_ID ...] [--gh PATH]
Needs an authenticated `gh` that can read the repository's Actions runs.

The price per minute is taken from the runner label of each job. Jobs on larger or
self-hosted runners have no known rate: they count as billable minutes but are left out
of the Linux-equivalent figure, and the output says how many.
"""

import argparse
import json
import math
import statistics
import subprocess
import sys
from datetime import datetime

# USD per minute for standard GitHub-hosted runners on private repositories, from
# https://docs.github.com/en/billing/reference/actions-minute-multipliers (read 2026-11-15).
RATES = {
    "linux-slim": 0.002,
    "linux": 0.006,
    "linux-arm": 0.005,
    "windows": 0.010,
    "macos": 0.062,
}

STANDARD_LABEL = {
    "ubuntu-latest", "ubuntu-22.04", "ubuntu-24.04", "ubuntu-26.04",
    "ubuntu-22.04-arm", "ubuntu-24.04-arm", "ubuntu-26.04-arm",
    "windows-latest", "windows-2022", "windows-2025", "windows-2025-vs2026",
    "windows-11-arm", "windows-11-vs2026-arm",
    "macos-latest", "macos-15", "macos-26", "macos-15-intel", "macos-26-intel",
}  # fmt: skip


def runner_kind(labels: list[str]) -> str | None:
    """Maps a job's `runs-on` labels to a key of RATES, or None when the rate is unknown."""
    if len(labels) != 1:
        return None
    label = labels[0].lower()
    if label == "ubuntu-slim":
        return "linux-slim"
    if label not in STANDARD_LABEL:
        return None
    if label.startswith("windows"):
        return "windows"
    if label.startswith("macos"):
        return "macos"
    return "linux-arm" if label.endswith("-arm") else "linux"


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def seconds_between(start: str | None, end: str | None) -> float | None:
    if not start or not end:
        return None
    return (parse_time(end) - parse_time(start)).total_seconds()


def dominant_step(job: dict) -> tuple[str, float] | None:
    timed = [
        (step["name"], seconds)
        for step in job.get("steps") or []
        if (seconds := seconds_between(step.get("started_at"), step.get("completed_at"))) is not None
    ]
    return max(timed, key=lambda item: item[1]) if timed else None


def summarize(run: dict, jobs: list[dict]) -> dict:
    """A skipped job never got a runner, so it is neither timed nor billed."""
    rows = []
    skipped = 0
    for job in jobs:
        seconds = seconds_between(job.get("started_at"), job.get("completed_at"))
        if job.get("conclusion") == "skipped" or seconds is None:
            skipped += 1
            continue
        minutes = max(1, math.ceil(seconds / 60))
        kind = runner_kind(job.get("labels") or [])
        rows.append(
            {
                "name": job["name"],
                "labels": ",".join(job.get("labels") or []),
                "seconds": seconds,
                "minutes": minutes,
                "linux_equivalent": None if kind is None else minutes * RATES[kind] / RATES["linux"],
                "dominant": dominant_step(job),
            }
        )
    return {
        "id": run["id"],
        "event": run.get("event"),
        "conclusion": run.get("conclusion"),
        # run_started_at is the start of the latest attempt; created_at stays at the first one.
        "wall_clock": seconds_between(run.get("run_started_at") or run.get("created_at"), run.get("updated_at")),
        "job_seconds": sum(row["seconds"] for row in rows),
        "minutes": sum(row["minutes"] for row in rows),
        "linux_equivalent": sum(row["linux_equivalent"] or 0 for row in rows),
        "unknown_rate_jobs": sum(1 for row in rows if row["linux_equivalent"] is None),
        "skipped": skipped,
        "jobs": rows,
    }


def gh(gh_path: str, *args: str) -> str:
    result = subprocess.run([gh_path, "api", *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"gh api {' '.join(args)} failed")
    return result.stdout


def fetch(gh_path: str, repo: str, run_id: str) -> tuple[dict, list[dict]]:
    run = json.loads(gh(gh_path, f"repos/{repo}/actions/runs/{run_id}"))
    lines = gh(gh_path, f"repos/{repo}/actions/runs/{run_id}/jobs", "--paginate", "--jq", ".jobs[] | @json")
    return run, [json.loads(line) for line in lines.splitlines() if line.strip()]


def print_summary(summary: dict) -> None:
    print(f"run {summary['id']} ({summary['event']}, {summary['conclusion']})")
    print(f"  wall-clock  {summary['wall_clock']:.0f} s")
    print(f"  job time    {summary['job_seconds']:.0f} s over {len(summary['jobs'])} job(s), {summary['skipped']} skipped")
    unknown = summary["unknown_rate_jobs"]
    note = f" ({unknown} job(s) with an unknown rate left out)" if unknown else ""
    print(f"  billable    {summary['minutes']} min = {summary['linux_equivalent']:.1f} Linux-equivalent min{note}")
    for row in summary["jobs"]:
        dominant = f"slowest step: {row['dominant'][0]} ({row['dominant'][1]:.0f} s)" if row["dominant"] else ""
        print(f"    {row['name']:<40} {row['labels']:<18} {row['seconds']:>5.0f} s -> {row['minutes']} min  {dominant}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("repo", help="OWNER/REPO")
    parser.add_argument("run_ids", nargs="+")
    parser.add_argument("--gh", default="gh")
    args = parser.parse_args()

    summaries = []
    for run_id in args.run_ids:
        try:
            summaries.append(summarize(*fetch(args.gh, args.repo, run_id)))
        except (RuntimeError, KeyError, ValueError) as exc:
            print(f"run {run_id}: {exc}", file=sys.stderr)
            return 1
        print_summary(summaries[-1])

    if len(summaries) >= 3:
        print(f"median of {len(summaries)} runs")
        print(f"  wall-clock  {statistics.median(s['wall_clock'] for s in summaries):.0f} s")
        print(f"  job time    {statistics.median(s['job_seconds'] for s in summaries):.0f} s")
        print(f"  billable    {statistics.median(s['minutes'] for s in summaries):g} min")
    elif len(summaries) > 1:
        print("fewer than 3 runs: no median printed, the spread between identical runs is too large")
    return 0


if __name__ == "__main__":
    sys.exit(main())
