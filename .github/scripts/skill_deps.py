#!/usr/bin/env python3
"""Shared skill-dependency resolver and ZIP bundler (Python stdlib only)."""

from __future__ import annotations

import io
import re
import subprocess
import sys
import zipfile
from pathlib import Path

REQUIRES_PREFIX = re.compile(r"^requires\s+skills\s*:\s*(.*)$", re.IGNORECASE)


def parse_requires_skills(compatibility: str | None) -> list[str]:
    """Extract skill names from a `Requires skills: a, b` compatibility string."""
    if not compatibility:
        return []
    match = REQUIRES_PREFIX.match(compatibility.strip())
    if not match:
        return []
    raw_items = match.group(1).strip().rstrip(".")
    if not raw_items:
        raise ValueError("compatibility has 'Requires skills:' with no skill names")
    deps: list[str] = []
    for part in raw_items.split(","):
        name = part.strip()
        if not name:
            raise ValueError(f"empty skill name in compatibility: {compatibility!r}")
        if name not in deps:
            deps.append(name)
    return deps


def extract_compatibility_from_markdown(text: str) -> str | None:
    """Read the scalar `compatibility:` line from YAML frontmatter without PyYAML."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("compatibility:"):
            value = line.split(":", 1)[1].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            return value
    return None


def resolve_closure(graph: dict[str, list[str]], skill: str) -> list[str]:
    """Return transitive dependencies of `skill` in breadth-first order, detecting cycles."""
    if skill not in graph:
        raise ValueError(f"unknown skill: {skill!r}")

    ordered: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node: str) -> None:
        for dep in graph[node]:
            if dep not in graph:
                raise ValueError(f"skill {node!r} depends on unknown skill {dep!r}")
            if dep == skill or dep in visiting:
                raise ValueError(f"dependency cycle involving {node!r} -> {dep!r}")
            if dep not in visited:
                visiting.add(dep)
                dfs(dep)
                visiting.remove(dep)
                visited.add(dep)
                ordered.append(dep)

    visiting.add(skill)
    dfs(skill)
    visiting.remove(skill)
    return ordered


def load_graph_from_git(ref: str) -> dict[str, list[str]]:
    """Build `{skill: direct_deps}` by reading `skills/*/SKILL.md` from a git ref."""
    out = subprocess.check_output(
        ["git", "ls-tree", "-d", "--name-only", f"{ref}:skills"],
        text=True,
    )
    skills = [line.strip() for line in out.splitlines() if line.strip()]
    graph: dict[str, list[str]] = {}
    for skill in sorted(skills):
        skill_md = subprocess.check_output(
            ["git", "show", f"{ref}:skills/{skill}/SKILL.md"],
            text=True,
        )
        compat = extract_compatibility_from_markdown(skill_md)
        graph[skill] = parse_requires_skills(compat)
    return graph


def bundle_skill_zip(ref: str, skill: str, deps: list[str], out_zip: Path) -> None:
    """Create `out_zip` containing `skill/` and each dependency folder from `ref`."""
    items = [skill, *deps]
    seen_names: set[str] = set()

    with zipfile.ZipFile(out_zip, "w") as zf_out:
        for item in items:
            raw_zip = subprocess.check_output(
                ["git", "archive", "--format=zip", f"--prefix={item}/", f"{ref}:skills/{item}"]
            )
            with zipfile.ZipFile(io.BytesIO(raw_zip), "r") as zf_in:
                for info in zf_in.infolist():
                    if info.filename in seen_names:
                        continue
                    seen_names.add(info.filename)
                    zf_out.writestr(info, zf_in.read(info.filename))


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: skill_deps.py <deps|bundle> ...", file=sys.stderr)
        return 2

    cmd = argv[1]
    if cmd == "deps" and len(argv) == 4:
        _, _, ref, skill = argv
        graph = load_graph_from_git(ref)
        print(" ".join(resolve_closure(graph, skill)))
        return 0

    if cmd == "bundle" and len(argv) == 5:
        _, _, ref, skill, out_path = argv
        graph = load_graph_from_git(ref)
        deps = resolve_closure(graph, skill)
        bundle_skill_zip(ref, skill, deps, Path(out_path))
        return 0

    print("Usage: skill_deps.py deps <ref> <skill> | bundle <ref> <skill> <out_zip>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
