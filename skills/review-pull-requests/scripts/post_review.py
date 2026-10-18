#!/usr/bin/env python3
"""Checks a drafted pull request review against the live diff, then posts it in one call.

The draft is a JSON file:

    {"repo": "owner/name", "pr": 120, "commit_id": "<head SHA the review was written on>",
     "event": "COMMENT" | "REQUEST_CHANGES" | "APPROVE",
     "body": "summary",
     "comments": [{"path": "src/a.rs", "line": 31, "side": "RIGHT",
                   "start_line": 28, "body": "…"}]}

Before posting it checks, and refuses on any failure: the event and its body; that the
pull request is still open and its head is still `commit_id` (a new push moves the lines
the comments point to); that the author is not the viewer when the event approves or
requests changes (GitHub refuses both on your own pull request); and that every comment
lands on a line of the diff — the right side for added or unchanged lines, the left for
removed ones, a multi-line range inside one hunk. After posting, the review's id and URL
are written back to the draft, and a second run refuses to post it again.

Usage: python3 post_review.py DRAFT.json [--dry-run] [--gh PATH]
Exit code 1 on any check that fails or a post that fails.
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

EVENTS = ("COMMENT", "REQUEST_CHANGES", "APPROVE")
HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


class GhError(Exception):
    pass


def gh(exe, *args):
    out = subprocess.run([exe, *args], capture_output=True, text=True, timeout=120, check=False)
    if out.returncode != 0:
        raise GhError(f"`gh {' '.join(args[:3])} …` failed: "
                      f"{out.stderr.strip() or out.stdout.strip()}")
    return json.loads(out.stdout)


def diff_lines(patch):
    """{side: {line: hunk index}} for every line a review comment can point to."""
    sides = {"LEFT": {}, "RIGHT": {}}
    old = new = hunk = None
    for raw in (patch or "").split("\n"):
        m = HUNK_RE.match(raw)
        if m:
            old, new = int(m.group(1)), int(m.group(3))
            hunk = 0 if hunk is None else hunk + 1
            continue
        if hunk is None or raw.startswith("\\"):
            continue
        if raw.startswith("+"):
            sides["RIGHT"][new] = hunk
            new += 1
        elif raw.startswith("-"):
            sides["LEFT"][old] = hunk
            old += 1
        else:
            sides["RIGHT"][new] = hunk
            sides["LEFT"][old] = hunk
            old += 1
            new += 1
    return sides


def check_draft(draft, pr, files, viewer):
    errors = []
    event = draft.get("event")
    if event not in EVENTS:
        errors.append(f"`event` must be one of {', '.join(EVENTS)}")
    if event in ("COMMENT", "REQUEST_CHANGES") and not (draft.get("body") or "").strip():
        errors.append(f"a {event} review needs a `body`")
    if pr.get("state") != "open":
        errors.append(f"the pull request is {pr.get('state')}")
    head = pr["head"]["sha"]
    if not draft.get("commit_id") or not head.startswith(draft["commit_id"]):
        errors.append(f"the head is now `{head[:9]}`, not the `{(draft.get('commit_id') or '')[:9]}`"
                      " the review was written on: read the new commits and re-check every line")
    if event in ("APPROVE", "REQUEST_CHANGES") and viewer == pr["user"]["login"]:
        errors.append(f"you are the author: GitHub refuses {event} on your own pull request; "
                      "use COMMENT")
    patches = {f["filename"]: diff_lines(f.get("patch")) for f in files}
    for i, c in enumerate(draft.get("comments") or [], 1):
        where = f"comment {i} (`{c.get('path')}:{c.get('line')}`)"
        if not (c.get("body") or "").strip():
            errors.append(f"{where} has no body")
        if c.get("path") not in patches:
            errors.append(f"{where}: the file is not in this pull request's diff")
            continue
        side = c.get("side", "RIGHT")
        lines = patches[c["path"]].get(side)
        if lines is None:
            errors.append(f"{where}: `side` must be LEFT or RIGHT")
            continue
        if c.get("line") not in lines:
            errors.append(f"{where}: line {c.get('line')} is not on the {side} side of the diff; "
                          "GitHub only takes comments on lines a hunk shows")
            continue
        start = c.get("start_line")
        if start is not None:
            start_side = c.get("start_side", side)
            first = patches[c["path"]].get(start_side, {})
            if start not in first or start > c["line"] and start_side == side:
                errors.append(f"{where}: start_line {start} is not a line of the diff before "
                              "`line`")
            elif first[start] != lines[c["line"]]:
                errors.append(f"{where}: lines {start}–{c['line']} span two hunks")
    return errors


def payload(draft):
    body = {"commit_id": draft["commit_id"], "event": draft["event"],
            "body": draft.get("body") or "", "comments": []}
    for c in draft.get("comments") or []:
        item = {"path": c["path"], "line": c["line"], "side": c.get("side", "RIGHT"),
                "body": c["body"]}
        if c.get("start_line") is not None:
            item["start_line"] = c["start_line"]
            item["start_side"] = c.get("start_side", item["side"])
        body["comments"].append(item)
    return body


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("draft")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--gh", default="gh")
    args = parser.parse_args(argv[1:])
    path = Path(args.draft)
    try:
        draft = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        return 1
    if draft.get("posted"):
        print(f"error: already posted as {draft['posted'].get('url')}; nothing to do",
              file=sys.stderr)
        return 1
    repo, number = draft.get("repo"), draft.get("pr")
    try:
        pr = gh(args.gh, "api", f"repos/{repo}/pulls/{number}")
        files = [f for page in gh(args.gh, "api", f"repos/{repo}/pulls/{number}/files",
                                  "--paginate", "--slurp") for f in page]
        viewer = gh(args.gh, "api", "user").get("login")
    except GhError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    errors = check_draft(draft, pr, files, viewer)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"\n{len(errors)} problem(s); nothing was posted.", file=sys.stderr)
        return 1
    n = len(draft.get("comments") or [])
    if args.dry_run:
        print(f"would post a {draft['event']} review on {repo}#{number} at "
              f"`{draft['commit_id'][:9]}` with {n} inline comment(s)")
        return 0
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        json.dump(payload(draft), tmp)
    try:
        review = gh(args.gh, "api", "-X", "POST", f"repos/{repo}/pulls/{number}/reviews",
                    "--input", tmp.name)
    except GhError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        Path(tmp.name).unlink(missing_ok=True)
    draft["posted"] = {"id": review.get("id"), "url": review.get("html_url")}
    path.write_text(json.dumps(draft, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"posted {draft['event']} with {n} inline comment(s): {review.get('html_url')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
