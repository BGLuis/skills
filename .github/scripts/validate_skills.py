#!/usr/bin/env python3
"""Validates SKILL.md frontmatter against the open Agent Skills spec
(agentskills.io/specification) and this hub's cross-agent portability rule.
"""

import sys
from pathlib import Path

import yaml

SKILLS_DIR = Path("skills")
MAX_DESCRIPTION_LEN = 1024

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


def validate_skill(skill_dir: Path) -> list[str]:
    errors = []
    skill_name = skill_dir.name
    skill_file = skill_dir / "SKILL.md"

    if not skill_file.is_file():
        return [f"Skill '{skill_name}' is missing SKILL.md"]

    text = skill_file.read_text(encoding="utf-8")
    raw_frontmatter = extract_frontmatter(text)
    if raw_frontmatter is None:
        return [f"Skill '{skill_name}' SKILL.md has no valid '---' delimited frontmatter block"]

    try:
        frontmatter = yaml.safe_load(raw_frontmatter)
    except yaml.YAMLError as exc:
        return [f"Skill '{skill_name}' SKILL.md frontmatter is not valid YAML: {exc}"]

    if not isinstance(frontmatter, dict):
        return [f"Skill '{skill_name}' SKILL.md frontmatter must be a YAML mapping"]

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

    used_forbidden_keys = CLAUDE_CODE_ONLY_KEYS & frontmatter.keys()
    if used_forbidden_keys:
        errors.append(
            f"Skill '{skill_name}' SKILL.md uses Claude-Code-only frontmatter key(s) "
            f"{sorted(used_forbidden_keys)}, breaking portability to other agents"
        )

    return errors


def main() -> int:
    all_errors = []
    for skill_dir in sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir()):
        print(f"Checking skill: {skill_dir.name}")
        all_errors.extend(validate_skill(skill_dir))

    for error in all_errors:
        print(f"::error::{error}")

    if all_errors:
        print(f"Validation failed with {len(all_errors)} error(s).")
        return 1

    print("All skills validated successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
