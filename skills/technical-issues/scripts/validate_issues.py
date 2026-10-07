#!/usr/bin/env python3
"""Validates the issue drafts produced by the technical-issues skill before publishing.

Checks only what is mechanical (format in references/issue-anatomy.md):
manifest.json well formed, unique keys, files present, one level of nesting with the
epic created before its sub-issues, every sub-issue key listed in its epic, no H1 in
bodies, emojis outside the allowed set, no checked boxes, [Fn] citations consistent
with each body's own sources table, `file:line` evidence, and the required labels per
kind (epic, finding, task), with the fix label directly followed by the acceptance
criteria.

Labels are localized; the manifest's `language` picks the set. For a language with no
label table the structural checks still run and the label checks are skipped with a
warning.

Usage: python3 validate_issues.py DRAFTS_DIR
Output: one `file:line: message` line per error; exit code 1 if there is any error.
"""

import json
import re
import sys
from pathlib import Path

ALLOWED_EMOJI = {"✅", "\U0001F7E1", "❌", "⚠"}  # ✅ 🟡 ❌ ⚠
EMOJI_RANGES = [(0x1F000, 0x1FAFF), (0x2600, 0x27BF), (0x2B00, 0x2BFF)]
KINDS = ("epic", "finding", "task")

# Keep in sync with the "Labels per language" table in references/issue-anatomy.md.
LOCALES = {
    "en": {
        "evidence": "**Evidence:**",
        "reproduction": "**Reproduction:**",
        "fix": "**Fix:**",
        "implementation": "**Implementation:**",
        "acceptance": "**Acceptance criteria:**",
        "verdict": "**Verdict:**",
        "not_verified": "**Not verified:**",
    },
    "pt-BR": {
        "evidence": "**Evidência:**",
        "reproduction": "**Reprodução:**",
        "fix": "**Correção:**",
        "implementation": "**Implementação:**",
        "acceptance": "**Critério de aceite:**",
        "verdict": "**Veredicto:**",
        "not_verified": "**Não verificado:**",
    },
}
REQUIRED = {
    "epic": ("verdict", "not_verified"),
    "finding": ("evidence", "reproduction", "fix", "acceptance"),
    "task": ("evidence", "implementation", "acceptance"),
}

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
CITATION_RE = re.compile(r"\[F(\d+)\]")
SOURCE_ROW_RE = re.compile(r"^\|\s*F(\d+)\s*\|")
CHECKED_RE = re.compile(r"^\s*[-*] \[[xX]\]")
FILE_LINE_RE = re.compile(r"`[^`\s]*:\d+(?:[-,]\d+)*`")
ZERO_RESULT_RE = re.compile(r"#\s*→\s*0\b")


def prose_lines(lines):
    """Returns (number, line) for everything outside fenced code blocks."""
    fence = None
    out = []
    for n, line in enumerate(lines, 1):
        m = FENCE_RE.match(line)
        if fence is None:
            if m:
                fence = m.group(1)
                continue
            out.append((n, line))
        elif m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
            fence = None
    return out


def is_emoji(ch):
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in EMOJI_RANGES) and ch not in ALLOWED_EMOJI


def validate_body(path, issue, children, L, err):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not text.strip():
        err(path, 1, "empty body")
        return
    prose = prose_lines(lines)

    cited, defined = {}, {}
    for n, line in prose:
        if line.startswith("# "):
            err(path, n, "H1 in the body; the title goes in the manifest")
        bare = INLINE_CODE_RE.sub("", line)
        for ch in bare:
            if is_emoji(ch):
                err(path, n, f"emoji outside the allowed set (✅ 🟡 ❌ ⚠️): '{ch}'")
                break
        if CHECKED_RE.match(bare):
            err(path, n, "checked `[x]` box; nothing in a new issue has been done")
        m = SOURCE_ROW_RE.match(line)
        if m:
            defined.setdefault(int(m.group(1)), n)
        for m in CITATION_RE.finditer(bare):
            cited.setdefault(int(m.group(1)), n)
    for f, n in sorted(cited.items()):
        if f not in defined:
            err(path, n, f"[F{f}] cited but missing from this issue's sources table")
    for f, n in sorted(defined.items()):
        if f not in cited:
            err(path, n, f"F{f} is in the sources table but never cited in this issue")

    kind = issue["kind"]
    if kind != "epic" and not (FILE_LINE_RE.search(text) or ZERO_RESULT_RE.search(text)):
        err(path, 1, "no `file:line` evidence and no zero-result search (`# → 0 …`)")
    if kind == "epic":
        for child in children:
            if not re.search(r"^\|.*\|\s*" + re.escape(child) + r"\s*\|", text, re.M):
                err(path, 1, f"sub-issue '{child}' is not a row of the epic's table")

    if not L:
        return
    required = list(REQUIRED[kind])
    if kind != "epic" and not issue.get("parent"):
        required.append("not_verified")
    for key in required:
        if not any(line.startswith(L[key]) for _, line in prose):
            err(path, 1, f"{kind} without the {L[key]} field")
    for i, line in enumerate(lines):
        if not line.startswith(L["fix"]):
            continue
        j = i + 1
        while j < len(lines) and lines[j].strip() and not lines[j].startswith(L["acceptance"]):
            j += 1
        if j >= len(lines) or not lines[j].startswith(L["acceptance"]):
            err(path, i + 1, f"`{L['acceptance']}` must come right below `{L['fix']}`, "
                             "with no blank line")


def validate(drafts_dir):
    drafts = Path(drafts_dir)
    manifest_path = drafts / "manifest.json"
    errors = []

    def err(path, n, msg):
        errors.append(f"{path}:{n}: {msg}")

    if not manifest_path.is_file():
        return [f"{manifest_path}:0: manifest.json not found"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{manifest_path}:{exc.lineno}: invalid JSON: {exc.msg}"]

    issues = manifest.get("issues") if isinstance(manifest, dict) else None
    if not isinstance(issues, list) or not issues:
        return [f"{manifest_path}:1: `issues` must be a non-empty list"]
    if not isinstance(manifest.get("repo"), str) or "/" not in manifest["repo"]:
        err(manifest_path, 1, "`repo` must be `owner/name`")

    lang = manifest.get("language")
    L = LOCALES.get(lang)
    if not L:
        print(f"{manifest_path}: warning: no label table for language '{lang}' (known: "
              f"{', '.join(LOCALES)}); label checks skipped — check them by hand",
              file=sys.stderr)

    seen = {}
    for idx, issue in enumerate(issues):
        where = f"issues[{idx}]"
        if not isinstance(issue, dict):
            err(manifest_path, 1, f"{where} must be an object")
            continue
        key = issue.get("key")
        if not isinstance(key, str) or not key:
            err(manifest_path, 1, f"{where} without `key`")
            continue
        if key in seen:
            err(manifest_path, 1, f"duplicate key '{key}'")
        seen[key] = (idx, issue)
        if issue.get("kind") not in KINDS:
            err(manifest_path, 1, f"'{key}': `kind` must be one of {', '.join(KINDS)}")
        title = issue.get("title")
        if not isinstance(title, str) or not title.strip():
            err(manifest_path, 1, f"'{key}': empty `title`")
        elif title.lstrip().startswith("#") or any(is_emoji(ch) for ch in title):
            err(manifest_path, 1, f"'{key}': title must be plain text, no Markdown or emoji")
        elif title.rstrip().endswith("."):
            err(manifest_path, 1, f"'{key}': title ends with a period")
        if not isinstance(issue.get("labels", []), list):
            err(manifest_path, 1, f"'{key}': `labels` must be a list")
        if not isinstance(issue.get("file"), str) or not (drafts / issue["file"]).is_file():
            err(manifest_path, 1, f"'{key}': body file '{issue.get('file')}' not found")

    children = {k: [] for k, (_, i) in seen.items() if i.get("kind") == "epic"}
    for key, (idx, issue) in seen.items():
        parent = issue.get("parent")
        if not parent:
            continue
        if issue.get("kind") == "epic":
            err(manifest_path, 1, f"'{key}': an epic cannot have a parent (one level only)")
        elif parent not in children:
            err(manifest_path, 1, f"'{key}': parent '{parent}' is not an epic in the manifest")
        else:
            children[parent].append(key)
            if seen[parent][0] > idx:
                err(manifest_path, 1, f"'{key}' comes before its epic '{parent}'; "
                                      "the epic is created first")
    for epic, kids in children.items():
        if not kids:
            err(manifest_path, 1, f"epic '{epic}' has no sub-issues; make it a single issue")

    if errors:
        return errors
    for key, (_, issue) in seen.items():
        validate_body(drafts / issue["file"], issue, children.get(key, []), L, err)
    return errors


def main(argv):
    if len(argv) != 2 or argv[1] in ("-h", "--help"):
        print(__doc__.strip())
        return 0 if len(argv) == 2 else 2
    errors = validate(argv[1])
    for e in errors:
        print(e)
    if errors:
        print(f"\n{len(errors)} error(s).", file=sys.stderr)
        return 1
    print("OK — drafts ready for preview.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
