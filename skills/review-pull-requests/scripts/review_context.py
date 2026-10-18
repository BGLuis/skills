#!/usr/bin/env python3
"""Gathers what a reviewer must know about a GitHub pull request before reading its diff.

Prints the author and how much the repository trusts them, the issues it closes, the
checks, its size, every changed file marked when it runs code at build, test, or install
time, which code changes have no test change next to them, and the reviews already left —
then the flags: a closed or draft pull request, a size too large to review well, code
from outside the repository that would run on a build, and files with no diff to read.

Usage: python3 review_context.py PR [-R OWNER/REPO] [--gh PATH]
PR is a number, `#N`, or a pull request URL (whose repository wins over -R).
Output: Markdown on stdout. Exit code 1 when the pull request cannot be read.
"""

import argparse
import json
import re
import subprocess
import sys

URL_RE = re.compile(r"^https://github\.com/([^/\s]+/[^/\s]+)/pull/(\d+)(?:/.*)?$")
TRUSTED = {"OWNER", "MEMBER", "COLLABORATOR"}
# Files whose content runs when the branch is built, tested, installed, or opened in CI.
EXECUTES = re.compile(
    r"(^|/)(\.github/(workflows|actions)/|\.husky/|\.devcontainer/)"
    r"|(^|/)(Makefile|justfile|Justfile|Dockerfile[^/]*|docker-compose[^/]*|compose\.ya?ml|"
    r"build\.rs|setup\.py|setup\.cfg|pyproject\.toml|conftest\.py|noxfile\.py|tox\.ini|"
    r"package\.json|\.npmrc|\.yarnrc(\.yml)?|Cargo\.toml|\.cargo/config(\.toml)?|go\.mod|"
    r"Gemfile|Rakefile|build\.gradle(\.kts)?|settings\.gradle(\.kts)?|pom\.xml|"
    r"lefthook\.ya?ml|\.pre-commit-config\.yaml|mise\.toml|\.tool-versions|\.envrc|"
    r"(vite|webpack|rollup|jest|vitest|babel|eslint)\.config\.[cm]?[jt]s)$"
    r"|\.(sh|bash|zsh|ps1)$")
LOCKFILE = re.compile(r"(^|/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|Cargo\.lock|"
                      r"poetry\.lock|uv\.lock|go\.sum|Gemfile\.lock|composer\.lock)$")
TEST = re.compile(r"(^|/)(tests?|spec|__tests__|e2e)/|(_test|\.test|\.spec|_spec)\.[a-z]+$|"
                  r"(^|/)test_[^/]+\.py$")
DOC = re.compile(r"\.(md|rst|txt|adoc)$|(^|/)docs?/")
TOO_LARGE = 1000  # Google eng-practices, "Small CLs": 1000 lines is usually too large


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


def kind_of(name):
    if LOCKFILE.search(name):
        return "lockfile"
    if EXECUTES.search(name):
        return "executes"
    if TEST.search(name):
        return "test"
    if DOC.search(name):
        return "doc"
    return "code"


def render(pr, files, view, reviews, viewer):
    out, flags = [], []
    author = pr["user"]["login"]
    association = pr.get("author_association", "NONE")
    trusted = association in TRUSTED
    fork = pr["head"]["repo"] and pr["head"]["repo"]["full_name"] != pr["base"]["repo"]["full_name"]
    size = pr.get("additions", 0) + pr.get("deletions", 0)
    out += [f"# PR #{pr['number']} {pr['title']}", "",
            f"- **State:** {pr['state']}" + (" (draft)" if pr.get("draft") else ""),
            f"- **URL:** {pr['html_url']}",
            f"- **Author:** {author} ({association}"
            + (", outside the repository" if not trusted else "") + ")",
            f"- **Branches:** `{pr['base']['ref']}` ← `{pr['head']['ref']}`"
            + (f" from the fork {pr['head']['repo']['full_name']}" if fork else "")
            + f" at `{pr['head']['sha'][:9]}`",
            f"- **Size:** +{pr.get('additions', 0)} −{pr.get('deletions', 0)} in "
            f"{pr.get('changed_files', len(files))} files"]
    if pr["state"] != "open":
        flags.append(f"the pull request is {pr['state']}: confirm before reviewing it")
    if pr.get("draft"):
        flags.append("draft: ask whether the author wants a review yet")
    if size > TOO_LARGE:
        flags.append(f"{size} changed lines: too large to review well in one pass; consider "
                     "asking for a split, or say which parts were reviewed")
    if viewer == author:
        flags.append("you are the author: GitHub refuses an approval or a change request on your "
                     "own pull request, so the review can only comment")

    issues = view.get("closingIssuesReferences") or []
    out += ["", "## Issues it closes", ""]
    out += [f"- #{i['number']} {i.get('url', '')}" for i in issues] or [
        "- none: find what asked for this change before judging whether it belongs"]

    checks = view.get("statusCheckRollup") or []
    failing = [c.get("name") or c.get("context") for c in checks
               if (c.get("conclusion") or c.get("state") or "").upper()
               in {"FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "STARTUP_FAILURE"}]
    pending = [c.get("name") or c.get("context") for c in checks
               if c.get("__typename") == "CheckRun" and (c.get("status") or "") != "COMPLETED"]
    out += ["", f"## Checks ({len(checks)}: {len(failing)} failing, {len(pending)} pending)", ""]
    out += [f"- **fail** {n}" for n in failing] + [f"- **pending** {n}" for n in pending] or [
        "- nothing failing or pending" if checks else "- no checks ran on this pull request"]

    kinds = {f["filename"]: kind_of(f["filename"]) for f in files}
    out += ["", "## Files", "", "| File | Status | +/− | Kind |", "|---|---|---|---|"]
    for f in files:
        mark = kinds[f["filename"]]
        if "patch" not in f and f.get("status") != "removed":
            mark += ", no diff shown"
        out.append(f"| `{f['filename']}` | {f.get('status')} | +{f.get('additions', 0)} "
                   f"−{f.get('deletions', 0)} | {mark} |")
    executes = [n for n, k in kinds.items() if k in ("executes", "lockfile")]
    if executes and not trusted:
        flags.append("code from outside the repository changes files that run on build, test, "
                     "or install: " + ", ".join(f"`{n}`" for n in executes)
                     + " — read them before running anything from this branch")
    elif executes:
        out.append("")
        out.append("Files that run on build, test, or install: "
                   + ", ".join(f"`{n}`" for n in executes) + ".")
    hidden = [f["filename"] for f in files if "patch" not in f and f.get("status") != "removed"]
    if hidden:
        flags.append("no diff from the API for " + ", ".join(f"`{n}`" for n in hidden)
                     + ": read them in the checkout")
    code = [n for n, k in kinds.items() if k == "code"]
    if code and not any(k == "test" for k in kinds.values()):
        flags.append("code changes with no test change: ask how the change is verified")

    out += ["", f"## Reviews already left ({len(reviews)})", ""]
    for r in reviews:
        body = " ".join((r.get("body") or "").split())
        body = body if len(body) <= 160 else body[:159] + "…"
        out.append(f"- **{(r.get('user') or {}).get('login', '?')}** {r.get('state')} "
                   f"{(r.get('submitted_at') or '')[:10]}" + (f": {body}" if body else ""))
    if not reviews:
        out.append("- none")

    out += ["", "## Description", ""]
    out.append("\n".join("> " + line for line in (pr.get("body") or "").strip().splitlines())
               or "> (empty)")
    if not (pr.get("body") or "").strip():
        flags.append("no description: ask what the change is for and how it was tested")
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
        pr = gh(args.gh, "api", f"repos/{repo}/pulls/{number}")
        files = [f for page in gh(args.gh, "api", f"repos/{repo}/pulls/{number}/files",
                                  "--paginate", "--slurp") for f in page]
        view = gh(args.gh, "pr", "view", str(number), "-R", repo, "--json",
                  "closingIssuesReferences,statusCheckRollup")
        reviews = [r for page in gh(args.gh, "api", f"repos/{repo}/pulls/{number}/reviews",
                                    "--paginate", "--slurp") for r in page]
        viewer = gh(args.gh, "api", "user").get("login")
    except (ValueError, GhError, KeyError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(render(pr, files, view, reviews, viewer), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
