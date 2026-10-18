#!/usr/bin/env python3
"""Lists the dependencies a branch adds or changes, and what is known against each version.

Compares the lockfiles of BASE and HEAD in a local clone, then, for every package added or
moved to a new version, asks the public registries for the latest release and whether this
version is yanked or deprecated, and asks OSV (osv.dev) for known vulnerabilities.

Parsed: Cargo.lock (crates.io), package-lock.json (npm), uv.lock and poetry.lock (PyPI),
requirements*.txt pinned with `==` (PyPI), go.sum (Go). Any other lockfile that changed, and
any manifest that changed without its lockfile, is listed for reading by hand. Only package
names and versions leave the machine, and only for public registries.

Usage: python3 dependency_diff.py --base REF --head REF [--repo DIR] [--offline]
       [--max-lookups N]
Output: Markdown on stdout. Exit code 0 even with findings (they are for the reviewer to
weigh); 1 when git cannot read the refs.
"""

import argparse
import json
import re
import subprocess
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from pathlib import PurePosixPath

USER_AGENT = "review-pull-requests-skill (dependency_diff.py)"
LOCK_PARSERS = {}
OTHER_LOCKS = {"pnpm-lock.yaml", "yarn.lock", "Gemfile.lock", "composer.lock", "bun.lockb"}
MANIFESTS = {"Cargo.toml": "Cargo.lock", "package.json": "package-lock.json",
             "pyproject.toml": "uv.lock", "go.mod": "go.sum"}


def lock_parser(*names):
    def register(fn):
        for name in names:
            LOCK_PARSERS[name] = fn
        return fn
    return register


@lock_parser("Cargo.lock")
def parse_cargo(text):
    data = tomllib.loads(text)
    return {("crates.io", p["name"]): p["version"] for p in data.get("package", [])
            if str(p.get("source", "")).startswith("registry+")}


@lock_parser("package-lock.json")
def parse_npm(text):
    data = json.loads(text)
    found = {}
    for key, meta in (data.get("packages") or {}).items():
        if "node_modules/" in key and meta.get("version") and not meta.get("link"):
            found[("npm", key.rsplit("node_modules/", 1)[1])] = meta["version"]
    for name, meta in (data.get("dependencies") or {}).items():  # lockfileVersion 1
        if isinstance(meta, dict) and meta.get("version"):
            found.setdefault(("npm", name), meta["version"])
    return found


@lock_parser("uv.lock", "poetry.lock")
def parse_python_lock(text):
    data = tomllib.loads(text)
    found = {}
    for p in data.get("package", []):
        source = p.get("source") or {}
        if isinstance(source, dict) and set(source) & {"editable", "virtual", "path", "git",
                                                        "directory"}:
            continue
        if p.get("name") and p.get("version"):
            found[("PyPI", p["name"].lower())] = p["version"]
    return found


@lock_parser("go.sum")
def parse_go_sum(text):
    found = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 3:
            found[("Go", parts[0])] = parts[1].removesuffix("/go.mod")
    return found


def parse_requirements(text):
    found = {}
    for line in text.splitlines():
        m = re.match(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)(\[[^\]]*\])?\s*==\s*([^\s;#]+)", line)
        if m:
            found[("PyPI", m.group(1).lower())] = m.group(3)
    return found


def parser_for(path):
    name = PurePosixPath(path).name
    if name in LOCK_PARSERS:
        return LOCK_PARSERS[name]
    if re.fullmatch(r"requirements[^/]*\.txt", name):
        return parse_requirements
    return None


def git(repo, *args):
    out = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                         timeout=60, check=False)
    return out.returncode, out.stdout


def file_at(repo, ref, path):
    code, text = git(repo, "show", f"{ref}:{path}")
    return text if code == 0 else ""


def version_key(version):
    nums = re.findall(r"\d+", version.split("+")[0])
    return tuple(int(n) for n in nums[:4])


def breaking_part(version):
    """The part of a version whose change breaks compatibility: 1.x.y → (1,), 0.3.y → (0, 3)."""
    key = version_key(version)
    return key[:1] if key and key[0] > 0 else key[:2]


def fetch_json(url, body=None):
    request = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode(),
                                     headers={"User-Agent": USER_AGENT,
                                              "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=15) as reply:  # noqa: S310 (fixed hosts)
        return json.loads(reply.read().decode())


def go_escape(module):
    return re.sub(r"[A-Z]", lambda m: "!" + m.group(0).lower(), module)


def registry_facts(ecosystem, name, version):
    """(latest version, status of this version) from the public registry."""
    q = urllib.parse.quote
    if ecosystem == "crates.io":
        latest = fetch_json(f"https://crates.io/api/v1/crates/{q(name)}")["crate"]
        this = fetch_json(f"https://crates.io/api/v1/crates/{q(name)}/{q(version)}")["version"]
        return latest.get("max_stable_version") or latest.get("max_version"), (
            "yanked" if this.get("yanked") else "")
    if ecosystem == "npm":
        latest = fetch_json(f"https://registry.npmjs.org/{q(name, safe='@')}/latest")
        this = fetch_json(f"https://registry.npmjs.org/{q(name, safe='@')}/{q(version)}")
        note = this.get("deprecated")
        return latest.get("version"), f"deprecated: {note}" if note else ""
    if ecosystem == "PyPI":
        latest = fetch_json(f"https://pypi.org/pypi/{q(name)}/json")["info"]["version"]
        info = fetch_json(f"https://pypi.org/pypi/{q(name)}/{q(version)}/json")["info"]
        reason = info.get("yanked_reason") or ""
        return latest, (f"yanked: {reason}" if reason else "yanked") if info.get("yanked") else ""
    if ecosystem == "Go":
        return fetch_json(f"https://proxy.golang.org/{go_escape(name)}/@latest").get("Version"), ""
    return None, ""


def advisories(packages):
    """OSV ids per (ecosystem, name, version), in one batch."""
    queries = [{"package": {"ecosystem": e, "name": n}, "version": v} for e, n, v in packages]
    found = {}
    for start in range(0, len(queries), 1000):
        chunk = queries[start:start + 1000]
        results = fetch_json("https://api.osv.dev/v1/querybatch", {"queries": chunk})["results"]
        for query, result in zip(chunk, results):
            key = (query["package"]["ecosystem"], query["package"]["name"], query["version"])
            found[key] = [v["id"] for v in result.get("vulns") or []]
    return found


def changes(repo, base, head):
    code, names = git(repo, "diff", "--name-only", f"{base}...{head}")
    if code != 0:
        raise RuntimeError(f"git cannot diff {base}...{head} in {repo}")
    changed = [n for n in names.splitlines() if n]
    rows, unparsed, parsed = [], [], []
    for path in changed:
        parse = parser_for(path)
        if parse is None:
            if PurePosixPath(path).name in OTHER_LOCKS:
                unparsed.append(path)
            continue
        try:
            before = parse(file_at(repo, base, path)) if file_at(repo, base, path) else {}
            after = parse(file_at(repo, head, path)) if file_at(repo, head, path) else {}
        except (tomllib.TOMLDecodeError, json.JSONDecodeError, KeyError) as exc:
            unparsed.append(f"{path} ({exc.__class__.__name__})")
            continue
        parsed.append(path)
        for key in sorted(set(before) | set(after)):
            old, new = before.get(key), after.get(key)
            if old == new:
                continue
            if old is None:
                kind = "added"
            elif new is None:
                kind = "removed"
            elif version_key(new) < version_key(old):
                kind = "downgraded"
            else:
                kind = "upgraded"
            rows.append({"lockfile": path, "ecosystem": key[0], "name": key[1], "old": old,
                         "new": new, "kind": kind})
    changed_names = {PurePosixPath(n).name for n in changed}
    orphan_manifests = []
    for path in changed:
        lock = MANIFESTS.get(PurePosixPath(path).name)
        locks = {"uv.lock", "poetry.lock"} if lock == "uv.lock" else {lock}
        if lock and not locks & changed_names:
            orphan_manifests.append(path)
    return rows, unparsed, orphan_manifests, parsed


def render(rows, unparsed, orphans, offline, max_lookups, parsed=()):
    out, flags = ["# Dependency changes", ""], []
    live = [r for r in rows if r["kind"] != "removed"]
    vulns, lookups_done = {}, 0
    if live and not offline:
        try:
            vulns = advisories({(r["ecosystem"], r["name"], r["new"]) for r in live})
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as exc:
            flags.append(f"OSV could not be queried ({exc}): advisories not checked")
    for r in live:
        r["advisories"] = vulns.get((r["ecosystem"], r["name"], r["new"]), [])
        r["latest"], r["status"] = None, ""
        if offline or lookups_done >= max_lookups:
            continue
        lookups_done += 1
        try:
            r["latest"], r["status"] = registry_facts(r["ecosystem"], r["name"], r["new"])
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as exc:
            r["status"] = f"lookup failed: {exc.__class__.__name__}"
    skipped = max(0, len(live) - lookups_done) if not offline else len(live)

    if not rows:
        out.append("- no package version changed in " + (", ".join(f"`{p}`" for p in parsed)
                   if parsed else "any lockfile this script parses"))
    else:
        out += ["| Lockfile | Package | Change | Latest | Status | Advisories |",
                "|---|---|---|---|---|---|"]
        for r in rows:
            change = {"added": f"+ {r['new']}", "removed": f"− {r['old']}"}.get(
                r["kind"], f"{r['old']} → {r['new']} ({r['kind']})")
            out.append(f"| `{r['lockfile']}` | {r['ecosystem']} `{r['name']}` | {change} | "
                       f"{r.get('latest') or '—'} | {r.get('status') or '—'} | "
                       f"{', '.join(r.get('advisories') or []) or '—'} |")
    for r in live:
        label = f"{r['ecosystem']} `{r['name']}` {r['new']}"
        if r.get("advisories"):
            flags.append(f"{label} has known advisories: {', '.join(r['advisories'])}")
        if r.get("status", "").startswith(("yanked", "deprecated")):
            flags.append(f"{label} is {r['status']}")
        latest = r.get("latest")
        if latest and r["kind"] == "added" and breaking_part(latest) > breaking_part(r["new"]):
            flags.append(f"{label} is added a breaking release behind the latest ({latest}): "
                         "ask why, or whether a direct dependency pins it")
    for r in rows:
        if r["kind"] == "downgraded":
            flags.append(f"{r['ecosystem']} `{r['name']}` is downgraded {r['old']} → {r['new']}")
    if unparsed:
        flags.append("read by hand (not parsed): " + ", ".join(f"`{u}`" for u in unparsed))
    if orphans:
        flags.append("manifest changed but no lockfile did: " + ", ".join(f"`{o}`" for o in orphans)
                     + " — check whether it changes a dependency")
    if offline and live:
        flags.append("offline: latest versions, yanked/deprecated status, and advisories not checked")
    elif skipped:
        flags.append(f"registry lookups capped at {max_lookups}: {skipped} package(s) without "
                     "latest version or status (advisories were checked for all)")
    out += ["", "## Flags", ""] + ([f"- ⚠️ {f}" for f in flags] or ["- none"])
    return "\n".join(out) + "\n"


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--max-lookups", type=int, default=40)
    args = parser.parse_args(argv[1:])
    try:
        rows, unparsed, orphans, parsed = changes(args.repo, args.base, args.head)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(render(rows, unparsed, orphans, args.offline, args.max_lookups, parsed), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
