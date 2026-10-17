#!/usr/bin/env python3
"""Validates the issue drafts produced by the technical-issues skill before publishing.

Checks only what is mechanical (format in references/issue-anatomy.md and, when the
manifest names one, the repository profile in references/repo-profile.md):

- manifest: well formed, unique keys, files present, parents (an epic of the manifest
  created first, or an existing issue `#N`), `blocked_by` pointing to known issues with
  no cycle, and no security finding filed on a public repository;
- bodies: the GitHub size limit, no H1, emojis outside the allowed set, no checked
  boxes, no secrets, no hard-wrapped prose, [Fn] citations consistent with each body's
  own sources table, `file:line` evidence inside the evidence field, the base commit,
  the required labels per kind with the fix or implementation label directly followed
  by the acceptance criteria, every sub-issue listed in its epic, and `Depends on`
  mirroring `blocked_by`;
- profile: title pattern, required labels, milestone and parent, section headings,
  required text, and forbidden fields.

Labels are localized; the manifest's `language` picks the set. For a language with no
label table the structural checks still run and the label checks are skipped with a
warning.

Usage: python3 validate_issues.py DRAFTS_DIR
Output: one `file:line: message` line per error, warnings on stderr; exit code 1 if
there is any error.
"""

import json
import re
import sys
from pathlib import Path

ALLOWED_EMOJI = {"✅", "\U0001F7E1", "❌", "⚠"}  # ✅ 🟡 ❌ ⚠
EMOJI_RANGES = [(0x1F000, 0x1FAFF), (0x2600, 0x27BF), (0x2B00, 0x2BFF)]
KINDS = ("epic", "finding", "task")
MODES = ("audit", "proposal")
VISIBILITIES = ("public", "private", "internal")
BODY_LIMIT = 65536  # GitHub rejects a longer issue body
TITLE_WARN = 80
TITLE_MAX = 100

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
        "base_commit": "**Base commit:**",
        "depends_on": "**Depends on:**",
        "depends_section": "Depends on",
    },
    "pt-BR": {
        "evidence": "**Evidência:**",
        "reproduction": "**Reprodução:**",
        "fix": "**Correção:**",
        "implementation": "**Implementação:**",
        "acceptance": "**Critério de aceite:**",
        "verdict": "**Veredicto:**",
        "not_verified": "**Não verificado:**",
        "base_commit": "**Commit base:**",
        "depends_on": "**Depende de:**",
        "depends_section": "Depende de",
    },
}
REQUIRED = {
    "epic": ("not_verified",),
    "finding": ("evidence", "reproduction", "fix", "acceptance"),
    "task": ("evidence", "implementation", "acceptance"),
}

# Keep in sync with the schema in references/repo-profile.md.
PROFILE_KEYS = {
    "sources", "title_pattern", "epic_label", "epic_title_pattern", "title_max", "labels",
    "require_milestone", "require_parent", "heading_level", "sections", "required_text",
    "forbidden_fields", "post_create",
}

SECRET_PATTERNS = [
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,})")),
    ("API key", re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{20,}")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("hard-coded credential", re.compile(
        r"(?i)\b(?:password|passwd|secret|token|api[_-]?key)\b\s*[:=]\s*[\"']([^\"'\s]{8,})[\"']")),
]
REDACTED_RE = re.compile(r"(?i)[<*…]|\.\.\.|redacted|example|placeholder|xxxx|changeme")

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
CITATION_RE = re.compile(r"\[F(\d+)\]")
SOURCE_ROW_RE = re.compile(r"^\|\s*F(\d+)\s*\|")
CHECKED_RE = re.compile(r"^\s*[-*] \[[xX]\]")
CODE_TOKEN_RE = re.compile(r"`([^`\s]+)`")
LOCATION_RE = re.compile(r"^(?P<path>.+?):\d+(?:[-–,]\d+)*$")
PERMALINK_RE = re.compile(r"https://github\.com/[^/\s]+/[^/\s]+/blob/[0-9a-f]{7,40}/\S+?#L\d+")
ZERO_RESULT_RE = re.compile(r"#\s*→\s*0\b")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
FIELD_LABEL_RE = re.compile(r"^\*\*[^*]+:\*\*")
TABLE_SEP_RE = re.compile(r"^\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)*\|?$")
LIST_ITEM_RE = re.compile(r"^\s*[-*+] (?:\[ \] )?(\S+)")
BLOCK_START_RE = re.compile(r"^(?:[-*+] |\d+[.)] |\||#|>|\*\*[^*]+:\*\*|<|`{3}|~{3})")
ISSUE_REF_RE = re.compile(r"^#\d+$")
PARENT_REF_RE = re.compile(r"^(?:#\d+|https://github\.com/[^/\s]+/[^/\s]+/issues/\d+)$")
KEYLIKE_RE = re.compile(
    r"(?<![\w#+-])[A-Z]{1,3}-?\d+(?:\.\d+)?(?:\+[A-Z]{1,3}-?\d+(?:\.\d+)?)*(?![\w+-])")
FALSIFIABLE_RE = re.compile(r"[`\d≤≥<>=]|\[F\d+\]")
HOST_SUFFIXES = {"com", "org", "net", "io", "dev", "app", "local", "internal", "localhost"}


def prose_lines(lines):
    """Returns (number, line) for everything outside fenced code and HTML comments."""
    fence = None
    comment = False
    out = []
    for n, line in enumerate(lines, 1):
        m = FENCE_RE.match(line)
        if fence is not None:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                fence = None
            continue
        if comment or line.lstrip().startswith("<!--"):
            comment = "-->" not in line
            continue
        if m:
            fence = m.group(1)
            continue
        out.append((n, line))
    return out


def is_emoji(ch):
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in EMOJI_RANGES) and ch not in ALLOWED_EMOJI


def is_file_location(token):
    """`src/a.ts:12-30` or `Dockerfile:3`, but not `localhost:3000` or `api.example.com:443`."""
    m = LOCATION_RE.match(token)
    if not m:
        return False
    path = m.group("path")
    if "//" in path:
        return False
    base = path.rsplit("/", 1)[-1]
    if "." not in base:
        return "/" in path or base.lower().endswith("file")
    ext = base.rsplit(".", 1)[1]
    if not ext[:1].isalpha():
        return False
    return "/" in path or ext.lower() not in HOST_SUFFIXES


def has_location(text):
    if PERMALINK_RE.search(text) or ZERO_RESULT_RE.search(text):
        return True
    return any(is_file_location(t) for t in CODE_TOKEN_RE.findall(text))


def field_block(lines, label):
    """Text of the field that opens with `label`, up to the next field label or heading."""
    for i, line in enumerate(lines):
        if not line.startswith(label):
            continue
        block = [line]
        fence = None
        for nxt in lines[i + 1:]:
            m = FENCE_RE.match(nxt)
            if fence is None:
                if FIELD_LABEL_RE.match(nxt) or HEADING_RE.match(nxt):
                    break
                if m:
                    fence = m.group(1)
            elif m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                fence = None
            block.append(nxt)
        return "\n".join(block)
    return None


def section_block(lines, name):
    """Lines under the heading `name`, up to the next heading of the same or a higher level."""
    out, level = [], None
    for line in lines:
        m = HEADING_RE.match(line)
        if level is None:
            if m and m.group(2) == name:
                level = len(m.group(1))
            continue
        if m and len(m.group(1)) <= level:
            break
        out.append(line)
    return out if level is not None else None


def hard_wrapped(lines):
    """First line of each paragraph that continues the previous line: GitHub renders the
    newline inside issues as <br>, so a paragraph wrapped at ~100 columns comes out ragged."""
    hits, prev, flagged = [], None, False
    prose = dict(prose_lines(lines))
    for n, line in enumerate(lines, 1):
        stripped = line.strip()
        if n not in prose or not stripped:
            prev, flagged = None, False
            continue
        if (prev is not None and not flagged and not BLOCK_START_RE.match(stripped)
                and not prev.endswith(("  ", "\\")) and not HEADING_RE.match(prev.strip())):
            hits.append(n)
            flagged = True
        prev = line
    return hits


def listed_keys(prose):
    """Keys in a table body row (not the header, not a sources row) or opening a list item."""
    keys = set()
    for i, (_, line) in enumerate(prose):
        s = line.strip()
        if s.startswith("|"):
            nxt = prose[i + 1][1].strip() if i + 1 < len(prose) else ""
            if TABLE_SEP_RE.match(s) or TABLE_SEP_RE.match(nxt) or SOURCE_ROW_RE.match(s):
                continue
            keys.update(c.strip() for c in s.strip("|").split("|"))
            continue
        m = LIST_ITEM_RE.match(line)
        if m:
            keys.add(m.group(1))
    return keys


def depends_refs(lines, L, all_keys):
    """Issue references written under the Depends on field or section, or None if neither."""
    segments = []
    for line in lines:
        i = line.find(L["depends_on"])
        if i >= 0:
            segments.append(line[i + len(L["depends_on"]):].split(" · **")[0])
    section = section_block(lines, L["depends_section"])
    if section is not None:
        segments.extend(section)
    if not segments:
        return None
    text = INLINE_CODE_RE.sub("", "\n".join(segments))
    refs = set(re.findall(r"#\d+", text)) | set(KEYLIKE_RE.findall(text))
    refs |= {k for k in all_keys
             if re.search(r"(?<![\w#+-])" + re.escape(k) + r"(?![\w+-])", text)}
    return refs


def find_secret(text):
    for name, pattern in SECRET_PATTERNS:
        for m in pattern.finditer(text):
            # Only the generic credential captures its value: a token with a fixed prefix
            # is never a placeholder.
            if not (m.lastindex and REDACTED_RE.search(m.group(1))):
                return name
    return None


def validate_body(path, issue, ctx, err, warn):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not text.strip():
        err(path, 1, "empty body")
        return
    if len(text) > BODY_LIMIT:
        err(path, 1, f"body has {len(text)} characters; GitHub rejects more than {BODY_LIMIT}")
    secret = find_secret(text)
    if secret:
        err(path, 1, f"possible {secret} in the body; redact it before publishing")
    prose = prose_lines(lines)
    L, profile, kind = ctx["L"], ctx["profile"], issue["kind"]

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
    for n in hard_wrapped(lines):
        err(path, n, "hard-wrapped paragraph: GitHub renders this newline as a line break; "
                     "keep each paragraph or list item on one line")

    if kind == "epic":
        listed = listed_keys(prose)
        for child in ctx["children"].get(issue["key"], []):
            if child not in listed:
                err(path, 1, f"sub-issue '{child}' is not a row of the epic's table "
                             "nor an item of its checklist")

    if profile:
        validate_body_profile(path, issue, profile, text, prose, err)

    if not L:
        if kind != "epic" and not has_location(text):
            err(path, 1, "no `file:line` evidence and no zero-result search (`# → 0 …`)")
        return

    required = list(REQUIRED[kind])
    if kind == "epic" and ctx["mode"] == "audit":
        required.append("verdict")
    if kind != "epic" and issue.get("parent") not in ctx["epics"]:
        required.append("not_verified")
    for key in required:
        if not any(line.startswith(L[key]) for _, line in prose):
            err(path, 1, f"{kind} without the {L[key]} field")

    if kind != "epic":
        evidence = field_block(lines, L["evidence"])
        if evidence is not None and not has_location(evidence):
            err(path, 1, f"{L['evidence']} has no `file:line`, permalink, or zero-result search")
    if not (PERMALINK_RE.search(text) or any(L["base_commit"] in line for _, line in prose)):
        err(path, 1, f"no {L['base_commit']} and no permalink with a commit SHA; "
                     "line numbers drift once the code changes")

    for lead in ("fix", "implementation"):
        for i, line in enumerate(lines):
            if not line.startswith(L[lead]):
                continue
            j = i + 1
            while j < len(lines) and lines[j].strip() and not lines[j].startswith(L["acceptance"]):
                j += 1
            if j >= len(lines) or not lines[j].startswith(L["acceptance"]):
                err(path, i + 1, f"`{L['acceptance']}` must come right below `{L[lead]}`, "
                                 "with no blank line")
    acceptance = field_block(lines, L["acceptance"])
    if acceptance is not None:
        criterion = acceptance[len(L["acceptance"]):]
        if not FALSIFIABLE_RE.search(INLINE_CODE_RE.sub("`", criterion)):
            warn(path, f"{L['acceptance']} names no command, number, or source; "
                       "check that it can fail")

    expected = set(issue.get("blocked_by") or [])
    refs = depends_refs(lines, L, ctx["keys"])
    if refs is None:
        if expected:
            err(path, 1, f"blocked_by {sorted(expected)} is not mirrored under "
                         f"{L['depends_on']} or `{L['depends_section']}`")
        return
    for ref in sorted(refs - expected):
        if ref.startswith("#") or ref in ctx["keys"]:
            err(path, 1, f"'{ref}' is under Depends on but not in `blocked_by`: "
                         "the native blocked-by link would be missing")
        else:
            err(path, 1, f"'{ref}' is under Depends on but is not a key of the manifest")
    for ref in sorted(expected - refs):
        err(path, 1, f"blocked_by '{ref}' is not mirrored under Depends on")


def validate_body_profile(path, issue, profile, text, prose, err):
    kind = issue["kind"]
    level = profile.get("heading_level")
    pattern = "#" * level if level else "#{2,3}"
    for name in profile.get("sections", {}).get(kind, []):
        if not any(re.match(rf"^{pattern} {re.escape(name)}\s*$", line) for _, line in prose):
            err(path, 1, f"profile: missing the `{'#' * (level or 2)} {name}` section")
    for snippet in profile.get("required_text", {}).get(kind, []):
        if snippet not in text:
            err(path, 1, f"profile: missing the required text `{snippet}`")
    for field in profile.get("forbidden_fields", []):
        for n, line in prose:
            if field in line:
                err(path, n, f"profile: `{field}` does not go in the body in this repository")
                break


def load_profile(drafts, manifest_path, name, err):
    path = drafts / name
    if not path.is_file():
        err(manifest_path, 1, f"profile '{name}' not found")
        return None
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        err(path, exc.lineno, f"invalid JSON: {exc.msg}")
        return None
    if not isinstance(profile, dict):
        err(path, 1, "the profile must be an object")
        return None
    for key in sorted(set(profile) - PROFILE_KEYS):
        err(path, 1, f"unknown key '{key}' (known: {', '.join(sorted(PROFILE_KEYS))})")
    if not profile.get("sources"):
        err(path, 1, "`sources` must list where each rule came from (AGENTS.md, a form, issues)")
    for key in ("title_pattern", "epic_title_pattern"):
        try:
            re.compile(profile.get(key) or "")
        except re.error as exc:
            err(path, 1, f"`{key}` is not a valid regex: {exc}")
    for rule in profile.get("labels", []):
        if not isinstance(rule, dict) or "pattern" not in rule:
            err(path, 1, "each `labels` rule needs a `pattern`")
    if profile.get("heading_level") not in (None, 2, 3):
        err(path, 1, "`heading_level` must be 2 or 3")
    return profile


def validate_issue_profile(manifest_path, key, issue, profile, err):
    labels = issue.get("labels") or []
    title = issue.get("title") or ""
    is_epic = profile.get("epic_label") in labels
    pattern = profile.get("epic_title_pattern") if is_epic else profile.get("title_pattern")
    if pattern and not re.search(pattern, title):
        err(manifest_path, 1, f"'{key}': title does not match the profile pattern `{pattern}`")
    for rule in profile.get("labels", []):
        count = sum(1 for label in labels if re.search(rule["pattern"], label))
        if count < rule.get("min", 0) or count > rule.get("max", count):
            bounds = f"{rule.get('min', 0)}–{rule.get('max', '∞')}"
            err(manifest_path, 1, f"'{key}': {count} label(s) match `{rule['pattern']}`, "
                                  f"the profile asks for {bounds}")
    if profile.get("require_milestone") and not issue.get("milestone"):
        err(manifest_path, 1, f"'{key}': the profile requires a milestone")
    if profile.get("require_parent") and not is_epic and not issue.get("parent"):
        err(manifest_path, 1, f"'{key}': the profile requires a parent (a manifest epic or `#N`)")


def find_cycle(graph):
    state = {}

    def visit(node, trail):
        state[node] = "open"
        for nxt in graph.get(node, []):
            if state.get(nxt) == "open":
                return trail + [node, nxt]
            if nxt not in state:
                found = visit(nxt, trail + [node])
                if found:
                    return found
        state[node] = "done"
        return None

    for node in graph:
        if node not in state:
            found = visit(node, [])
            if found:
                return found
    return None


def validate(drafts_dir):
    """Returns (errors, warnings)."""
    drafts = Path(drafts_dir)
    manifest_path = drafts / "manifest.json"
    errors, warnings = [], []

    def err(path, n, msg):
        errors.append(f"{path}:{n}: {msg}")

    def warn(path, msg):
        warnings.append(f"{path}: warning: {msg}")

    if not manifest_path.is_file():
        return [f"{manifest_path}:0: manifest.json not found"], warnings
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{manifest_path}:{exc.lineno}: invalid JSON: {exc.msg}"], warnings

    issues = manifest.get("issues") if isinstance(manifest, dict) else None
    if not isinstance(issues, list) or not issues:
        return [f"{manifest_path}:1: `issues` must be a non-empty list"], warnings
    if not isinstance(manifest.get("repo"), str) or "/" not in manifest["repo"]:
        err(manifest_path, 1, "`repo` must be `owner/name`")
    mode = manifest.get("mode")
    if mode not in MODES:
        err(manifest_path, 1, f"`mode` must be one of {', '.join(MODES)}")
    visibility = manifest.get("visibility")
    if visibility not in VISIBILITIES:
        err(manifest_path, 1, f"`visibility` must be one of {', '.join(VISIBILITIES)} "
                              "(from `gh repo view --json visibility`)")
    profile = None
    if manifest.get("profile") is not None:
        profile = load_profile(drafts, manifest_path, manifest["profile"], err)

    lang = manifest.get("language")
    L = LOCALES.get(lang)
    if not L:
        warn(manifest_path, f"no label table for language '{lang}' (known: "
                            f"{', '.join(LOCALES)}); label checks skipped — check them by hand")

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
        title_max = (profile or {}).get("title_max", TITLE_MAX)
        if not isinstance(title, str) or not title.strip():
            err(manifest_path, 1, f"'{key}': empty `title`")
        elif title.lstrip().startswith("#") or any(is_emoji(ch) for ch in title):
            err(manifest_path, 1, f"'{key}': title must be plain text, no Markdown or emoji")
        elif title.rstrip().endswith("."):
            err(manifest_path, 1, f"'{key}': title ends with a period")
        elif len(title) > title_max:
            err(manifest_path, 1, f"'{key}': title has {len(title)} characters (max {title_max})")
        elif len(title) > TITLE_WARN:
            warn(manifest_path, f"'{key}': title has {len(title)} characters; "
                                f"a board card shows about {TITLE_WARN}")
        if isinstance(title, str) and find_secret(title):
            err(manifest_path, 1, f"'{key}': possible secret in the title")
        labels = issue.get("labels", [])
        if not isinstance(labels, list) or not all(isinstance(x, str) for x in labels):
            err(manifest_path, 1, f"'{key}': `labels` must be a list of strings")
            issue["labels"] = []
        for field in ("milestone", "type", "project", "parent"):
            if field in issue and not (isinstance(issue[field], str) and issue[field]):
                err(manifest_path, 1, f"'{key}': `{field}` must be a non-empty string")
        for field in ("assignees", "blocked_by"):
            value = issue.get(field, [])
            if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
                err(manifest_path, 1, f"'{key}': `{field}` must be a list of strings")
                issue[field] = []
        if "security" in issue and not isinstance(issue["security"], bool):
            err(manifest_path, 1, f"'{key}': `security` must be true or false")
        if issue.get("security") and visibility == "public":
            err(manifest_path, 1, f"'{key}': a security finding is never filed as an issue on a "
                                  "public repository; route it through SECURITY.md")
        if issue.get("number") is not None and not isinstance(issue["number"], int):
            err(manifest_path, 1, f"'{key}': `number` is written by publish_issues.py")
        if not isinstance(issue.get("file"), str) or not (drafts / issue["file"]).is_file():
            err(manifest_path, 1, f"'{key}': body file '{issue.get('file')}' not found")
        if profile:
            validate_issue_profile(manifest_path, key, issue, profile, err)

    epics = {k for k, (_, i) in seen.items() if i.get("kind") == "epic"}
    children = {k: [] for k in epics}
    for key, (idx, issue) in seen.items():
        parent = issue.get("parent")
        if not isinstance(parent, str) or not parent:
            continue
        if PARENT_REF_RE.match(parent):
            continue
        if issue.get("kind") == "epic":
            err(manifest_path, 1, f"'{key}': an epic's parent can only be an existing issue "
                                  "(`#N`); one level of nesting inside the manifest")
        elif parent not in epics:
            err(manifest_path, 1, f"'{key}': parent '{parent}' is neither an epic of the "
                                  "manifest nor an existing issue `#N`")
        else:
            children[parent].append(key)
            if seen[parent][0] > idx:
                err(manifest_path, 1, f"'{key}' comes before its epic '{parent}'; "
                                      "the epic is created first")
    for epic, kids in children.items():
        if not kids:
            err(manifest_path, 1, f"epic '{epic}' has no sub-issues; make it a single issue")

    graph = {}
    for key, (_, issue) in seen.items():
        for ref in issue.get("blocked_by") or []:
            if ref == key:
                err(manifest_path, 1, f"'{key}': an issue cannot block itself")
            elif ref in seen:
                graph.setdefault(key, []).append(ref)
            elif not ISSUE_REF_RE.match(ref):
                err(manifest_path, 1, f"'{key}': blocked_by '{ref}' is neither a key of the "
                                      "manifest nor an existing issue `#N`")
    cycle = find_cycle(graph)
    if cycle:
        err(manifest_path, 1, f"blocked-by cycle: {' → '.join(cycle)}")

    if errors:
        return errors, warnings
    ctx = {"L": L, "profile": profile, "mode": mode, "epics": epics,
           "children": children, "keys": set(seen)}
    for key, (_, issue) in seen.items():
        validate_body(drafts / issue["file"], issue, ctx, err, warn)
    return errors, warnings


def main(argv):
    if len(argv) != 2 or argv[1] in ("-h", "--help"):
        print(__doc__.strip())
        return 0 if len(argv) == 2 else 2
    errors, warnings = validate(argv[1])
    for w in warnings:
        print(w, file=sys.stderr)
    for e in errors:
        print(e)
    if errors:
        print(f"\n{len(errors)} error(s).", file=sys.stderr)
        return 1
    print("OK — drafts ready for preview.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
