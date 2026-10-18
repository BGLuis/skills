#!/usr/bin/env python3
"""Gathers every piece of feedback a GitHub pull request is waiting on.

Reads the four places feedback lives — inline review threads (GraphQL, the only view
with `isResolved`), inline review comments (REST, to catch any comment no thread
returned), the review summaries, and the conversation comments — plus the checks, the
merge state, and the issues the pull request closes. Prints them as Markdown, with
what is new since the last commit and the flags that stop or limit the work.

Usage: python3 pr_context.py PR [-R OWNER/REPO] [--gh PATH]
PR is a number, `#N`, or a pull request URL (whose repository wins over -R). Without
-R, the repository of the current directory is used.
Output: Markdown on stdout. Exit code 1 when the pull request cannot be read.
"""

import argparse
import json
import re
import subprocess
import sys

PR_FIELDS = ("number,title,state,isDraft,url,body,author,baseRefName,headRefName,headRefOid,"
             "headRepository,headRepositoryOwner,isCrossRepository,maintainerCanModify,"
             "mergeable,mergeStateStatus,reviewDecision,statusCheckRollup,"
             "closingIssuesReferences,reviews,comments,commits")
THREADS_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $endCursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewThreads(first: 100, after: $endCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id isResolved isOutdated path line originalLine viewerCanResolve viewerCanReply
          comments(first: 100) {
            nodes { databaseId url createdAt body author { login __typename } }
          }
        }
      }
    }
  }
}"""
URL_RE = re.compile(r"^https://github\.com/([^/\s]+/[^/\s]+)/pull/(\d+)(?:/.*)?$")
RUN_RE = re.compile(r"/actions/runs/(\d+)(?:/job/(\d+))?")
FAILED = {"FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE"}
PENDING = {"PENDING", "QUEUED", "IN_PROGRESS", "WAITING", "REQUESTED", "EXPECTED"}


class GhError(Exception):
    pass


def gh(exe, *args):
    out = subprocess.run([exe, *args], capture_output=True, text=True, timeout=120, check=False)
    if out.returncode != 0:
        raise GhError(f"`gh {' '.join(args[:3])} …` failed: "
                      f"{out.stderr.strip() or out.stdout.strip()}")
    return json.loads(out.stdout)


def parse_ref(ref, default_repo):
    m = URL_RE.match(ref)
    if m:
        return m.group(1), int(m.group(2))
    if re.fullmatch(r"#?\d+", ref):
        return default_repo, int(ref.lstrip("#"))
    raise ValueError(f"'{ref}' is not a pull request number, `#N`, or a pull request URL")


def check_state(check):
    """(name, bucket, detail) for a CheckRun or a StatusContext."""
    if check.get("__typename") == "StatusContext":
        state = (check.get("state") or "").upper()
        bucket = "fail" if state in FAILED else "pending" if state in PENDING else "pass"
        return check.get("context", "?"), bucket, check.get("targetUrl") or ""
    status = (check.get("status") or "").upper()
    conclusion = (check.get("conclusion") or "").upper()
    if status != "COMPLETED":
        bucket = "pending"
    elif conclusion in FAILED:
        bucket = "fail"
    elif conclusion in ("SKIPPED", "NEUTRAL"):
        bucket = "skip"
    else:
        bucket = "pass"
    name = check.get("name", "?")
    if check.get("workflowName"):
        name = f"{check['workflowName']} / {name}"
    return name, bucket, check.get("detailsUrl") or ""


def one_line(text, limit=100):
    flat = " ".join((text or "").split())
    return flat if len(flat) <= limit else flat[:limit - 1] + "…"


def quote(text):
    return "\n".join("> " + line for line in (text or "").strip().splitlines()) or "> (empty)"


def render(pr, threads, rest_comments, viewer=None):
    out, flags = [], []
    pr_author = (pr.get("author") or {}).get("login", "?")
    if viewer and viewer != pr_author:
        flags.append(f"you ({viewer}) are not the author: commits go to {pr_author}'s branch, "
                     "so keep their intent and say so in the plan")
    commits = pr.get("commits") or []
    last_push = commits[-1].get("committedDate", "") if commits else ""

    def new(ts):
        return " · **new since the last commit**" if last_push and ts and ts > last_push else ""

    fork = pr.get("isCrossRepository")
    head_owner = (pr.get("headRepositoryOwner") or {}).get("login", "?")
    out += [f"# PR #{pr['number']} {pr['title']}", "",
            f"- **State:** {pr['state']}" + (" (draft)" if pr.get("isDraft") else ""),
            f"- **URL:** {pr['url']}",
            f"- **Author:** {pr_author}",
            f"- **Branches:** `{pr['baseRefName']}` ← `{pr['headRefName']}`"
            + (f" (fork of {head_owner})" if fork else "")
            + f" at `{(pr.get('headRefOid') or '')[:9]}`",
            f"- **Merge state:** {pr.get('mergeable')} / {pr.get('mergeStateStatus')}",
            f"- **Review decision:** {pr.get('reviewDecision') or 'none'}",
            f"- **Last commit:** {last_push or 'unknown'}"]
    if pr["state"] != "OPEN":
        flags.append(f"the pull request is {pr['state']}: confirm before changing it")
    if pr.get("mergeable") == "CONFLICTING":
        flags.append(f"conflicts with `{pr['baseRefName']}`: merge the base into the branch")
    if fork and not pr.get("maintainerCanModify"):
        flags.append("fork without \"Allow edits from maintainers\": you cannot push to this "
                     "branch; ask the author, or propose the changes another way")

    issues = pr.get("closingIssuesReferences") or []
    out += ["", "## Issues this pull request closes", ""]
    out += [f"- #{i['number']} {i.get('url', '')}" for i in issues] or ["- none"]

    checks = [check_state(c) for c in pr.get("statusCheckRollup") or []]
    counts = {b: sum(1 for _, x, _ in checks if x == b) for b in ("fail", "pending", "pass", "skip")}
    out += ["", f"## Checks ({counts['fail']} failing, {counts['pending']} pending, "
                f"{counts['pass']} passing, {counts['skip']} skipped)", ""]
    for name, bucket, url in checks:
        if bucket in ("fail", "pending"):
            run = RUN_RE.search(url)
            how = ""
            if run and bucket == "fail":
                how = f" — log: `gh run view {run.group(1)}" + (
                    f" --job {run.group(2)}" if run.group(2) else "") + " --log-failed`"
            out.append(f"- **{bucket}** {name}{how} {'' if run else url}".rstrip())
    if not any(b in ("fail", "pending") for _, b, _ in checks):
        out.append("- nothing failing or pending")
    if counts["fail"]:
        flags.append(f"{counts['fail']} failing check(s)")
    if counts["pending"]:
        flags.append(f"{counts['pending']} check(s) still running: wait before judging them")

    open_threads = [t for t in threads if not t.get("isResolved")]
    covered = {c.get("url") for t in threads for c in t["comments"]["nodes"]}
    out += ["", f"## Unresolved review threads ({len(open_threads)} of {len(threads)})"]
    cannot_resolve = 0
    for t in open_threads:
        comments = t["comments"]["nodes"]
        last = comments[-1] if comments else {}
        last_author = (last.get("author") or {}).get("login", "?")
        waiting = "the reviewer" if last_author == pr_author else "an answer from the PR side"
        line = t.get("line") or t.get("originalLine")
        where = f"`{t.get('path')}:{line}`" if line else f"`{t.get('path')}`"
        out += ["", f"### {where}" + (" · outdated" if t.get("isOutdated") else ""), "",
                f"- **Thread:** `{t['id']}` · waiting for {waiting}"
                + ("" if t.get("viewerCanResolve") else " · you cannot resolve it")
                + new(last.get("createdAt", ""))]
        cannot_resolve += 0 if t.get("viewerCanResolve") else 1
        for c in comments:
            author = (c.get("author") or {})
            bot = " (bot)" if author.get("__typename") == "Bot" else ""
            out += ["", f"**{author.get('login', '?')}{bot}** · {c.get('createdAt', '')[:10]} · "
                        f"{c.get('url', '')}", "", quote(c.get("body"))]
    mine = sum(1 for t in open_threads
               if viewer and (t["comments"]["nodes"] or [{}])[0].get("author", {}).get("login")
               == viewer)
    if mine:
        flags.append(f"you opened {mine} of the unresolved thread(s): a reply would answer your "
                     "own review; confirm who should reply before drafting")
    if cannot_resolve:
        flags.append(f"you cannot resolve {cannot_resolve} open thread(s) on this repository: "
                     "reply, and leave resolving to someone with write access")

    orphans = [c for c in rest_comments if c.get("html_url") not in covered]
    if orphans:
        out += ["", f"## Inline comments outside any thread ({len(orphans)})"]
        for c in orphans:
            out += ["", f"- **{(c.get('user') or {}).get('login', '?')}** on "
                        f"`{c.get('path')}:{c.get('line') or c.get('original_line')}` · id "
                        f"`{c.get('id')}` · {c.get('html_url')}{new(c.get('created_at', ''))}",
                    "", quote(c.get("body"))]

    reviews = [r for r in pr.get("reviews") or [] if (r.get("body") or "").strip()]
    out += ["", f"## Review summaries ({len(reviews)} with text)"]
    for r in reviews:
        out += ["", f"**{(r.get('author') or {}).get('login', '?')}** · {r.get('state')} · "
                    f"{(r.get('submittedAt') or '')[:10]}{new(r.get('submittedAt', ''))}",
                "", quote(r.get("body"))]
    if pr.get("reviewDecision") == "CHANGES_REQUESTED":
        flags.append("changes requested: a reviewer must approve again after the fixes")

    convo = [c for c in pr.get("comments") or [] if (c.get("body") or "").strip()]
    out += ["", f"## Conversation comments ({len(convo)})"]
    for c in convo:
        out += ["", f"**{(c.get('author') or {}).get('login', '?')}** · "
                    f"{(c.get('createdAt') or '')[:10]} · {c.get('url', '')}"
                    f"{new(c.get('createdAt', ''))}", "", quote(c.get("body"))]

    out += ["", "## Description", "", quote(pr.get("body"))]
    out += ["", "## Flags", ""] + ([f"- ⚠️ {f}" for f in flags] or ["- none"])
    return "\n".join(out) + "\n"


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("pr")
    parser.add_argument("-R", "--repo")
    parser.add_argument("--gh", default="gh")
    args = parser.parse_args(argv[1:])
    try:
        repo, number = parse_ref(args.pr, args.repo)
        if not repo:
            repo = gh(args.gh, "repo", "view", "--json", "nameWithOwner")["nameWithOwner"]
        owner, name = repo.split("/", 1)
        pr = gh(args.gh, "pr", "view", str(number), "-R", repo, "--json", PR_FIELDS)
        pages = gh(args.gh, "api", "graphql", "--paginate", "--slurp", "-f",
                   f"query={THREADS_QUERY}", "-F", f"owner={owner}", "-F", f"name={name}",
                   "-F", f"number={number}")
        threads = [t for page in pages
                   for t in page["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]]
        rest = gh(args.gh, "api", f"repos/{repo}/pulls/{number}/comments", "--paginate",
                  "--slurp")
        rest_comments = [c for page in rest for c in page]
        viewer = gh(args.gh, "api", "user").get("login")
    except (ValueError, GhError, KeyError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(render(pr, threads, rest_comments, viewer), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
