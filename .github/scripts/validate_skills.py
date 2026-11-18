#!/usr/bin/env python3
"""Validates SKILL.md frontmatter against the open Agent Skills spec
(agentskills.io/specification) and this hub's cross-agent portability rule.
"""

import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_deps import parse_requires_skills, resolve_closure

SKILLS_DIR = Path("skills")
INSTALL_SH = Path("install.sh")
MAX_DESCRIPTION_LEN = 1024
MAX_COMPATIBILITY_LEN = 500

# Frontmatter keys documented as Claude-Code-only extensions of the open
# Agent Skills spec. A hub whose whole purpose is portability across
# Gemini/Copilot/Cursor/etc. must not rely on these being honored elsewhere.
CLAUDE_CODE_ONLY_KEYS = {
    "allowed-tools",
    "disallowed-tools",
    "context",
    "agent",
    "background",
    "model",
    "effort",
    "shell",
    "hooks",
    "paths",
    "argument-hint",
    "arguments",
    "disable-model-invocation",
    "user-invocable",
    "when_to_use",
}


def extract_frontmatter(text: str):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    return None


def parse_install_sh_deps(path: Path) -> dict[str, set[str]]:
    """Parse `skill_deps()` cases from install.sh for consistency checks."""
    text = path.read_text(encoding="utf-8")
    block_match = re.search(r"skill_deps\(\)\s*\{(.*?)\n\}", text, re.DOTALL)
    if not block_match:
        raise ValueError(f"Could not find skill_deps() in {path}")
    deps: dict[str, set[str]] = {}
    for skill, raw_deps in re.findall(
        r'^\s*([a-z0-9-]+)\)\s*echo\s+"([^"]*)"\s*;;',
        block_match.group(1),
        re.MULTILINE,
    ):
        deps[skill] = set(raw_deps.split())
    return deps


def validate_skill(skill_dir: Path) -> tuple[list[str], dict]:
    errors = []
    skill_name = skill_dir.name
    skill_file = skill_dir / "SKILL.md"

    if not skill_file.is_file():
        return [f"Skill '{skill_name}' is missing SKILL.md"], {}

    text = skill_file.read_text(encoding="utf-8")
    raw_frontmatter = extract_frontmatter(text)
    if raw_frontmatter is None:
        return [f"Skill '{skill_name}' SKILL.md has no valid '---' delimited frontmatter block"], {}

    try:
        frontmatter = yaml.safe_load(raw_frontmatter)
    except yaml.YAMLError as exc:
        return [f"Skill '{skill_name}' SKILL.md frontmatter is not valid YAML: {exc}"], {}

    if not isinstance(frontmatter, dict):
        return [f"Skill '{skill_name}' SKILL.md frontmatter must be a YAML mapping"], {}

    name = frontmatter.get("name")
    if not name or not isinstance(name, str):
        errors.append(f"Skill '{skill_name}' SKILL.md missing non-empty 'name' field")
    elif name != skill_name:
        errors.append(
            f"Skill '{skill_name}' SKILL.md 'name: {name}' does not match its directory name"
        )

    description = frontmatter.get("description")
    if not description or not isinstance(description, str):
        errors.append(f"Skill '{skill_name}' SKILL.md missing non-empty 'description' field")
    elif len(description) > MAX_DESCRIPTION_LEN:
        errors.append(
            f"Skill '{skill_name}' description is {len(description)} chars, "
            f"exceeds the spec's {MAX_DESCRIPTION_LEN}-char limit"
        )

    compatibility = frontmatter.get("compatibility")
    if compatibility is not None:
        if not isinstance(compatibility, str) or not compatibility.strip():
            errors.append(f"Skill '{skill_name}' 'compatibility' must be a non-empty string")
        elif len(compatibility) > MAX_COMPATIBILITY_LEN:
            errors.append(
                f"Skill '{skill_name}' compatibility is {len(compatibility)} chars, "
                f"exceeds the spec's {MAX_COMPATIBILITY_LEN}-char limit"
            )

    used_forbidden_keys = CLAUDE_CODE_ONLY_KEYS & frontmatter.keys()
    if used_forbidden_keys:
        errors.append(
            f"Skill '{skill_name}' SKILL.md uses Claude-Code-only frontmatter key(s) "
            f"{sorted(used_forbidden_keys)}, breaking portability to other agents"
        )

    return errors, frontmatter


def validate_dependencies(frontmatters: dict[str, dict]) -> list[str]:
    errors = []
    graph: dict[str, list[str]] = {}

    for skill_name, fm in frontmatters.items():
        compat = fm.get("compatibility")
        if not isinstance(compat, str):
            graph[skill_name] = []
            continue
        try:
            graph[skill_name] = parse_requires_skills(compat)
        except ValueError as exc:
            errors.append(f"Skill '{skill_name}' invalid compatibility: {exc}")
            graph[skill_name] = []

    closures: dict[str, set[str]] = {}
    for skill_name, declared in graph.items():
        if not declared:
            continue
        try:
            closure = set(resolve_closure(graph, skill_name))
        except ValueError as exc:
            errors.append(f"Skill '{skill_name}' dependency error: {exc}")
            continue

        closures[skill_name] = closure
        missing_transitive = sorted(closure - set(declared))
        if missing_transitive:
            errors.append(
                f"Skill '{skill_name}' compatibility omits transitive dependencies: "
                f"{missing_transitive}"
            )

        desc = frontmatters[skill_name].get("description", "")
        if isinstance(desc, str):
            for dep in sorted(closure):
                if dep not in desc:
                    errors.append(
                        f"Skill '{skill_name}' description does not mention required skill '{dep}'"
                    )

    if INSTALL_SH.is_file():
        try:
            install_deps = parse_install_sh_deps(INSTALL_SH)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            if install_deps != closures:
                errors.append(
                    f"install.sh skill_deps() {install_deps} does not match SKILL.md "
                    f"dependencies {closures}"
                )

    return errors


def main() -> int:
    all_errors = []
    frontmatters: dict[str, dict] = {}
    for skill_dir in sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir()):
        print(f"Checking skill: {skill_dir.name}")
        errs, fm = validate_skill(skill_dir)
        all_errors.extend(errs)
        if fm:
            frontmatters[skill_dir.name] = fm

    all_errors.extend(validate_dependencies(frontmatters))

    for error in all_errors:
        print(f"::error::{error}")

    if all_errors:
        print(f"Validation failed with {len(all_errors)} error(s).")
        return 1

    print("All skills validated successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
