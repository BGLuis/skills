#!/usr/bin/env python3
"""Checks the pin table of references/versions.md against GitHub.

For every row (action, version, SHA) it asks the API which commit the version tag points
to and which release is the latest, and prints one status per action:

- MISMATCH: the SHA in the table is not the commit of that tag. Never use that row.
- UPDATE:   a newer release exists and is older than the cooldown. The line carries the
            new tag and its SHA, ready to paste into the table.
- COOLDOWN: a newer release exists but was published less than --cooldown-days ago.
            Keep the current pin until it ages (references/security.md §4).
- OK:       the table has the latest release.

Usage: python3 check_pins.py [VERSIONS_MD] [--cooldown-days N] [--gh PATH]
VERSIONS_MD defaults to ../references/versions.md. Needs an authenticated `gh`.
Exit code 1 on any MISMATCH or API error, 0 otherwise (UPDATE rows are advice).
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROW = re.compile(
    r"^\|\s*`(?P<repo>[\w.-]+/[\w.-]+)`[^|]*\|\s*(?P<version>v[\w.-]+)\s*\|\s*`(?P<sha>[0-9a-f]{40})`\s*\|"
)


@dataclass(frozen=True)
class Pin:
    repo: str
    version: str
    sha: str


def parse_table(text: str) -> list[Pin]:
    return [Pin(**m.groupdict()) for line in text.splitlines() if (m := ROW.match(line))]


def classify(
    pin: Pin,
    tag_sha: str,
    latest_tag: str,
    latest_published: datetime,
    now: datetime,
    cooldown_days: int,
) -> str:
    if tag_sha != pin.sha:
        return "MISMATCH"
    if latest_tag == pin.version:
        return "OK"
    if now - latest_published < timedelta(days=cooldown_days):
        return "COOLDOWN"
    return "UPDATE"


def gh_api(gh: str, path: str) -> dict:
    result = subprocess.run([gh, "api", path], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"gh api {path} failed")
    return json.loads(result.stdout)


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main() -> int:
    default_table = Path(__file__).resolve().parent.parent / "references" / "versions.md"
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("versions_md", nargs="?", type=Path, default=default_table)
    parser.add_argument("--cooldown-days", type=int, default=7)
    parser.add_argument("--gh", default="gh")
    args = parser.parse_args()

    pins = parse_table(args.versions_md.read_text(encoding="utf-8"))
    if not pins:
        print(f"no pin rows found in {args.versions_md}", file=sys.stderr)
        return 1

    now = datetime.now(timezone.utc)
    failed = False
    for pin in pins:
        try:
            tag_sha = gh_api(args.gh, f"repos/{pin.repo}/commits/{pin.version}")["sha"]
            latest = gh_api(args.gh, f"repos/{pin.repo}/releases/latest")
            status = classify(
                pin,
                tag_sha,
                latest["tag_name"],
                parse_time(latest["published_at"]),
                now,
                args.cooldown_days,
            )
            detail = ""
            if status == "MISMATCH":
                detail = f"{pin.version} is {tag_sha}, the table says {pin.sha}"
            elif status == "UPDATE":
                new_sha = gh_api(args.gh, f"repos/{pin.repo}/commits/{latest['tag_name']}")["sha"]
                detail = f"{latest['tag_name']} {new_sha} (published {latest['published_at'][:10]})"
            elif status == "COOLDOWN":
                detail = f"{latest['tag_name']} published {latest['published_at'][:10]}"
        except (RuntimeError, KeyError, ValueError) as exc:
            status, detail = "ERROR", str(exc)
        failed = failed or status in ("MISMATCH", "ERROR")
        print(f"{status:<9}{pin.repo:<46}{pin.version:<10}{detail}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
