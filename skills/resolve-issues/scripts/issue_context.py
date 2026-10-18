#!/usr/bin/env python3
"""Gathers what has to be known about GitHub issues before resolving them.

For each issue: title, state, labels, milestone, type, parent, blockers, the pull
requests that close it (with their state), the body, the comments, and, for an issue
with sub-issues, the order to work them in (siblings that block others come first).
Then the flags that stop the work (a closed issue, an open blocker, an open pull
request that already closes it, a blocked-by cycle) and how the given issues relate
to each other (one inside another, same parent, one blocking another).

Usage: python3 issue_context.py ISSUE [ISSUE ...] [-R OWNER/REPO] [--gh PATH]
ISSUE is a number, `#N`, or an issue URL (whose repository wins over -R). Without -R,
`gh` uses the repository of the current directory.
Output: Markdown on stdout. Exit code 1 when an issue cannot be read, 0 otherwise —
flags are information for the agent, not failures.
"""

import argparse
import json
import re
import subprocess
import sys

FIELDS = ("number,title,state,stateReason,url,body,labels,milestone,issueType,parent,"
          "subIssues,blockedBy,closedByPullRequestsReferences,comments")
URL_RE = re.compile(r"^https://github\.com/([^/\s]+/[^/\s]+)/issues/(\d+)/?$")


class GhError(Exception):
    pass


class Gh:
    def __init__(self, exe, repo):
        self.exe, self.repo, self.cache = exe, repo, {}

    def run(self, *args, repo=None):
        target = repo or self.repo
        cmd = [self.exe, *args] + (["-R", target] if target else [])
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
        if out.returncode != 0:
            raise GhError(f"`{' '.join(cmd)}` failed: {out.stderr.strip() or out.stdout.strip()}")
        return json.loads(out.stdout)

    def issue(self, number, repo=None):
        key = ("issue", repo or self.repo, number)
        if key not in self.cache:
            self.cache[key] = self.run("issue", "view", str(number), "--json", FIELDS, repo=repo)
        return self.cache[key]

    def pr(self, number, repo):
        key = ("pr", repo, number)
        if key not in self.cache:
            self.cache[key] = self.run("pr", "view", str(number), "--json",
                                       "number,state,isDraft,headRefName,url", repo=repo)
        return self.cache[key]


def parse_ref(ref, default_repo):
    m = URL_RE.match(ref)
    if m:
        return m.group(1), int(m.group(2))
    if re.fullmatch(r"#?\d+", ref):
        return default_repo, int(ref.lstrip("#"))
    raise ValueError(f"'{ref}' is not an issue number, `#N`, or an issue URL")


def nodes(value):
    if isinstance(value, dict):
        return value.get("nodes") or []
    return value or []


def is_open(item):
    return (item or {}).get("state", "").upper() == "OPEN"


def ref_line(item):
    return f"#{item['number']} {item.get('title', '')} ({item.get('state', '?')})".rstrip()


def work_order(subs, blockers_of):
    """Open sub-issues with every open sibling blocker first; a cycle is returned apart."""
    open_subs = [s["number"] for s in subs if is_open(s)]
    pending = {n: {b for b in blockers_of.get(n, set()) if b in open_subs} for n in open_subs}
    order = []
    while pending:
        ready = [n for n in open_subs if n in pending and not pending[n]]
        if not ready:
            return order, sorted(pending)
        for n in ready:
            order.append(n)
            del pending[n]
        for deps in pending.values():
            deps.difference_update(ready)
    return order, []


def describe(gh, repo, number, out):
    issue = gh.issue(number, repo)
    flags = []
    out.append(f"# #{issue['number']} {issue['title']}")
    out.append("")
    meta = [f"**State:** {issue['state']}"
            + (f" ({issue['stateReason']})" if issue.get("stateReason") else ""),
            f"**URL:** {issue['url']}"]
    if issue.get("labels"):
        meta.append("**Labels:** " + ", ".join(lb["name"] for lb in issue["labels"]))
    if issue.get("milestone"):
        meta.append(f"**Milestone:** {issue['milestone'].get('title')}")
    if issue.get("issueType"):
        meta.append(f"**Type:** {issue['issueType'].get('name')}")
    if issue.get("parent"):
        meta.append(f"**Parent:** {ref_line(issue['parent'])}")
    out.extend(f"- {m}" for m in meta)
    if not is_open(issue):
        flags.append("the issue is closed: confirm with the user before working on it")

    blockers = nodes(issue.get("blockedBy"))
    if blockers:
        out.append("- **Blocked by:** " + "; ".join(ref_line(b) for b in blockers))
        for b in blockers:
            if is_open(b):
                flags.append(f"open blocker #{b['number']}: it has to close first")

    prs = issue.get("closedByPullRequestsReferences") or []
    for ref in prs:
        owner = ref.get("repository", {}).get("owner", {}).get("login")
        name = ref.get("repository", {}).get("name")
        pr_repo = f"{owner}/{name}" if owner and name else repo
        pr = gh.pr(ref["number"], pr_repo)
        draft = " draft" if pr.get("isDraft") else ""
        out.append(f"- **Closing pull request:** #{pr['number']} {pr['state']}{draft} "
                   f"(`{pr.get('headRefName', '')}`) {pr.get('url', '')}")
        if pr["state"].upper() == "OPEN":
            flags.append(f"pull request #{pr['number']} already closes this issue and is open: "
                         "someone may be on it")

    subs = nodes(issue.get("subIssues"))
    order, cycle = [], []
    if subs:
        blockers_of = {}
        for s in subs:
            if is_open(s):
                child = gh.issue(s["number"], repo)
                blockers_of[s["number"]] = {b["number"] for b in nodes(child.get("blockedBy"))}
                outside = [b for b in nodes(child.get("blockedBy"))
                           if is_open(b) and b["number"] not in {x["number"] for x in subs}]
                for b in outside:
                    flags.append(f"sub-issue #{s['number']} waits for open #{b['number']}, "
                                 "outside this tree")
        order, cycle = work_order(subs, blockers_of)
        done = [s for s in subs if not is_open(s)]
        out.append("")
        out.append(f"## Sub-issues ({len(subs) - len(done)} open of {len(subs)})")
        out.append("")
        by_number = {s["number"]: s for s in subs}
        for i, n in enumerate(order, 1):
            waits = sorted(b for b in blockers_of.get(n, set()) if b in by_number
                           and is_open(by_number[b]))
            after = f" — after {', '.join(f'#{w}' for w in waits)}" if waits else ""
            out.append(f"{i}. {ref_line(by_number[n])}{after}")
        for n in cycle:
            out.append(f"- {ref_line(by_number[n])} — in a blocked-by cycle")
        for s in done:
            out.append(f"- {ref_line(s)} — done")
        if cycle:
            flags.append("blocked-by cycle among sub-issues " + ", ".join(f"#{n}" for n in cycle))

    out.append("")
    out.append("## Body")
    out.append("")
    out.append((issue.get("body") or "").strip() or "(empty)")
    comments = issue.get("comments") or []
    out.append("")
    out.append(f"## Comments ({len(comments)})")
    for c in comments:
        author = (c.get("author") or {}).get("login", "?")
        out.append("")
        out.append(f"### {author} · {c.get('createdAt', '')[:10]}")
        out.append("")
        out.append((c.get("body") or "").strip())
    out.append("")
    out.append("## Flags")
    out.append("")
    out.extend([f"- ⚠️ {f}" for f in flags] or ["- none"])
    out.append("")
    return issue, order


def relations(issues):
    """How the given issues relate to each other, from the data already read."""
    lines = []
    numbers = {i["number"] for i in issues}
    for i in issues:
        parent = (i.get("parent") or {}).get("number")
        if parent in numbers:
            lines.append(f"#{i['number']} is a sub-issue of #{parent}")
        for b in nodes(i.get("blockedBy")):
            if b["number"] in numbers:
                lines.append(f"#{i['number']} is blocked by #{b['number']}")
    by_parent = {}
    for i in issues:
        parent = (i.get("parent") or {}).get("number")
        if parent and parent not in numbers:
            by_parent.setdefault(parent, []).append(i["number"])
    for parent, kids in sorted(by_parent.items()):
        if len(kids) > 1:
            lines.append(", ".join(f"#{k}" for k in kids) + f" share the parent #{parent}")
    return lines


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("issues", nargs="+")
    parser.add_argument("-R", "--repo")
    parser.add_argument("--gh", default="gh")
    args = parser.parse_args(argv[1:])
    gh = Gh(args.gh, args.repo)
    out, read = [], []
    try:
        for ref in args.issues:
            repo, number = parse_ref(ref, args.repo)
            issue, _ = describe(gh, repo, number, out)
            read.append(issue)
    except (ValueError, GhError, json.JSONDecodeError) as exc:
        print("\n".join(out))
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if len(read) > 1:
        out.append("# Relations between the given issues")
        out.append("")
        out.extend(f"- {line}" for line in relations(read) or ["none found in the issue data"])
        out.append("")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
