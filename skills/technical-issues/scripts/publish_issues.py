#!/usr/bin/env python3
"""Publishes validated issue drafts to GitHub; resumable and idempotent.

Phases, in order (references/github-publishing.md):

1. validate the drafts with validate_issues.py, then check the live repository: `gh`
   recent enough for `--parent`, the visibility the manifest declares, and no security
   finding on a public repository;
2. create every issue that has no `number` yet, in manifest order, with its labels,
   milestone, parent, type, project, and assignees. Each new number is written back to
   manifest.json at once, so a rerun after a failure continues from the first issue
   without one instead of duplicating the others;
3. replace each sub-issue key with its `#N` in every body (outside code) and update the
   bodies whose text on GitHub differs;
4. create the native blocked-by links that do not exist yet;
5. read every issue back and compare title, labels, milestone, parent, and blockers
   with the manifest.

Usage: python3 publish_issues.py DRAFTS_DIR [--dry-run] [--gh PATH]
--dry-run prints the plan and calls nothing. Exit code 1 on any failure or mismatch.
"""

import argparse
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_issues  # noqa: E402

MIN_GH = (2, 94, 0)  # first release with `gh issue create --parent`
URL_NUMBER_RE = re.compile(r"/issues/(\d+)$")
INLINE_SPLIT_RE = re.compile(r"(`[^`]*`)")
PARENT_QUERY = ("query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,"
                "name:$name){issue(number:$number){parent{number}}}}")


class PublishError(Exception):
    pass


class Gh:
    def __init__(self, binary):
        self.binary = binary

    def run(self, *args):
        proc = subprocess.run([self.binary, *args], capture_output=True, text=True)
        if proc.returncode != 0:
            raise PublishError(f"`gh {shlex.join(args)}` failed: {proc.stderr.strip()}")
        return proc.stdout

    def json(self, *args):
        return json.loads(self.run(*args))


def ref_number(ref):
    """`#98` or an issue URL → 98."""
    return int(re.search(r"(\d+)$", ref).group(1))


def key_numbers(issues):
    # Epic keys stay as written: nothing points to the epic by key (the parent link is
    # native), and a key like `epic` would rewrite the ordinary word in every body.
    return {i["key"]: i["number"] for i in issues if i.get("number") and i["kind"] != "epic"}


def resolve_keys(text, numbers):
    """Replaces each key that has a number with `#N`, outside fenced and inline code."""
    if not numbers:
        return text
    keys = sorted(numbers, key=len, reverse=True)
    token = re.compile(r"(?<![\w#+-])(" + "|".join(map(re.escape, keys)) + r")(?![\w+-])")
    out, fence = [], None
    for line in text.splitlines(keepends=True):
        m = validate_issues.FENCE_RE.match(line)
        if fence is not None:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                fence = None
        elif m:
            fence = m.group(1)
        else:
            line = "".join(part if part.startswith("`")
                           else token.sub(lambda t: f"#{numbers[t.group(1)]}", part)
                           for part in INLINE_SPLIT_RE.split(line))
        out.append(line)
    return "".join(out)


class Publisher:
    def __init__(self, drafts, gh, dry_run):
        self.drafts = drafts
        self.gh = gh
        self.dry = dry_run
        self.manifest_path = drafts / "manifest.json"
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.repo = self.manifest["repo"]
        self.issues = self.manifest["issues"]
        self.by_key = {i["key"]: i for i in self.issues}
        self.resolved_dir = drafts / ".resolved"

    def say(self, msg):
        print(msg)

    def save(self):
        self.manifest_path.write_text(
            json.dumps(self.manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def body(self, issue):
        text = (self.drafts / issue["file"]).read_text(encoding="utf-8")
        return resolve_keys(text, key_numbers(self.issues))

    def write_resolved(self, issue, text):
        path = self.resolved_dir / issue["file"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def number_of(self, ref):
        if ref in self.by_key:
            number = self.by_key[ref].get("number")
            if number:
                return number
            if self.dry:
                return f"<{ref}>"
            raise PublishError(f"'{ref}' has no issue number yet")
        return ref_number(ref)

    def preflight(self):
        if self.dry:
            self.say(f"would check `gh --version` and the visibility of {self.repo}")
            return
        version = self.gh.run("--version")
        m = re.search(r"(\d+)\.(\d+)\.(\d+)", version)
        if not m or tuple(map(int, m.groups())) < MIN_GH:
            raise PublishError("gh ≥ 2.94.0 is needed for `--parent`; upgrade it or follow "
                               "the REST fallback in references/github-publishing.md")
        live = self.gh.json("repo", "view", self.repo, "--json", "visibility")
        visibility = live["visibility"].lower()
        if visibility != self.manifest["visibility"]:
            raise PublishError(f"the manifest says '{self.manifest['visibility']}' but "
                               f"{self.repo} is '{visibility}'; redo the security triage")
        if visibility == "public" and any(i.get("security") for i in self.issues):
            raise PublishError(f"{self.repo} is public: security findings go through "
                               "SECURITY.md, never an issue")

    def create(self):
        for issue in self.issues:
            key = issue["key"]
            if issue.get("number"):
                self.say(f"skip {key}: already #{issue['number']}")
                continue
            body = self.body(issue)
            body_path = (self.resolved_dir / issue["file"]) if self.dry \
                else self.write_resolved(issue, body)
            args = ["issue", "create", "-R", self.repo, "--title", issue["title"],
                    "--body-file", str(body_path)]
            for label in issue.get("labels") or []:
                args += ["--label", label]
            if issue.get("milestone"):
                args += ["--milestone", issue["milestone"]]
            if issue.get("parent"):
                parent = issue["parent"]
                args += ["--parent", parent if parent.startswith("http")
                         else str(self.number_of(parent))]
            if issue.get("type"):
                args += ["--type", issue["type"]]
            if issue.get("project"):
                args += ["--project", issue["project"]]
            for login in issue.get("assignees") or []:
                args += ["--assignee", login]
            if self.dry:
                self.say("would run: gh " + shlex.join(args))
                continue
            out = self.gh.run(*args).strip()
            m = URL_NUMBER_RE.search(out.splitlines()[-1] if out else "")
            if not m:
                raise PublishError(f"could not read the new issue number from {out!r}")
            issue["number"] = int(m.group(1))
            issue["url"] = out.splitlines()[-1]
            self.save()
            self.say(f"created {key} → {issue['url']}")

    def resolve_bodies(self):
        placeholders = {i["key"]: f"<{i['key']}>" for i in self.issues if i["kind"] != "epic"}
        for issue in self.issues:
            original = (self.drafts / issue["file"]).read_text(encoding="utf-8")
            if self.dry:
                if resolve_keys(original, placeholders) != original:
                    self.say(f"would update the body of {issue['key']} (keys → #N)")
                continue
            resolved = self.body(issue)
            if resolved == original:
                continue
            live = self.gh.json("issue", "view", str(issue["number"]), "-R", self.repo,
                                "--json", "body")["body"]
            if live.strip() == resolved.strip():
                continue
            path = self.write_resolved(issue, resolved)
            self.gh.run("issue", "edit", str(issue["number"]), "-R", self.repo,
                        "--body-file", str(path))
            self.say(f"updated the body of {issue['key']} (keys → #N)")

    def blockers_of(self, number):
        pages = self.gh.json("api", "--paginate", "--slurp",
                             f"repos/{self.repo}/issues/{number}/dependencies/blocked_by")
        items = [x for page in pages for x in page] if pages and isinstance(pages[0], list) \
            else pages
        return {x["number"] for x in items}

    def link_blockers(self):
        for issue in self.issues:
            refs = issue.get("blocked_by") or []
            if not refs:
                continue
            if self.dry:
                for ref in refs:
                    self.say(f"would link {issue['key']} as blocked by {ref}")
                continue
            existing = self.blockers_of(issue["number"])
            for ref in refs:
                blocker = self.number_of(ref)
                if blocker in existing:
                    continue
                blocker_id = self.gh.json("api", f"repos/{self.repo}/issues/{blocker}")["id"]
                self.gh.run("api", "-X", "POST",
                            f"repos/{self.repo}/issues/{issue['number']}/dependencies/blocked_by",
                            "-F", f"issue_id={blocker_id}")
                self.say(f"linked #{issue['number']} as blocked by #{blocker}")

    def verify(self):
        owner, name = self.repo.split("/", 1)
        problems = []
        for issue in self.issues:
            n = issue["number"]
            live = self.gh.json("issue", "view", str(n), "-R", self.repo,
                                "--json", "title,labels,milestone")
            if live["title"] != issue["title"]:
                problems.append(f"#{n}: title is {live['title']!r}")
            missing = set(issue.get("labels") or []) - {x["name"] for x in live["labels"]}
            if missing:
                problems.append(f"#{n}: missing labels {sorted(missing)}")
            milestone = (live.get("milestone") or {}).get("title")
            if issue.get("milestone") and milestone != issue["milestone"]:
                problems.append(f"#{n}: milestone is {milestone!r}, expected "
                                f"{issue['milestone']!r}")
            if issue.get("parent"):
                data = self.gh.json("api", "graphql", "-f", f"query={PARENT_QUERY}",
                                    "-f", f"owner={owner}", "-f", f"name={name}",
                                    "-F", f"number={n}")
                parent = (data["data"]["repository"]["issue"]["parent"] or {}).get("number")
                expected = self.number_of(issue["parent"])
                if parent != expected:
                    problems.append(f"#{n}: parent is {parent}, expected #{expected}")
            if issue.get("blocked_by"):
                expected = {self.number_of(r) for r in issue["blocked_by"]}
                absent = expected - self.blockers_of(n)
                if absent:
                    problems.append(f"#{n}: not blocked by {sorted(absent)}")
        return problems

    def summary(self, profile):
        for issue in self.issues:
            if issue.get("number"):
                parent = f" (parent {issue['parent']})" if issue.get("parent") else ""
                self.say(f"{issue['key']}: {issue.get('url', '#' + str(issue['number']))}{parent}")
        tasks = (profile or {}).get("post_create") or []
        if tasks:
            self.say("\nStill to do by hand (repository profile):")
            for task in tasks:
                self.say(f"- {task}")


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("drafts")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--gh", default="gh")
    args = parser.parse_args(argv[1:])
    drafts = Path(args.drafts)

    errors, warnings = validate_issues.validate(drafts)
    for w in warnings:
        print(w, file=sys.stderr)
    if errors:
        for e in errors:
            print(e)
        print(f"\n{len(errors)} validation error(s); nothing was published.", file=sys.stderr)
        return 1

    pub = Publisher(drafts, Gh(args.gh), args.dry_run)
    profile = None
    if pub.manifest.get("profile"):
        profile = json.loads((drafts / pub.manifest["profile"]).read_text(encoding="utf-8"))
    try:
        pub.preflight()
        pub.create()
        pub.resolve_bodies()
        pub.link_blockers()
        problems = [] if args.dry_run else pub.verify()
    except PublishError as exc:
        print(f"error: {exc}", file=sys.stderr)
        made = [f"{i['key']} #{i['number']}" for i in pub.issues if i.get("number")]
        print(f"created so far: {', '.join(made) or 'none'}. Numbers are saved in "
              "manifest.json: fix the cause and rerun; created issues are skipped.",
              file=sys.stderr)
        return 1
    if problems:
        for p in problems:
            print(f"mismatch: {p}", file=sys.stderr)
        return 1
    pub.summary(profile)
    if not args.dry_run:
        print("\nOK — published and read back.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
