#!/usr/bin/env python3
"""Validates the shape of a technical report produced by the technical-report skill.

Checks only what is mechanical (content rules live in references/checklist.md):
no frontmatter, a single H1 on line 1, numbered and contiguous H2s, no H4, `---`
before every H2, a closing blockquote, the anatomy of P-NN/U-NN findings, the fix
label directly followed by the acceptance-criteria label, required parts per mode
(Precedents and Non-goals in A, Verdict in B/C), emojis outside the allowed set,
checked boxes outside "Verification performed", and [Fn] citations consistent with
the "Sources consulted" table.

Labels are localized (see references/locales.md). The language is detected from the
labels found, or forced with --lang. For a language with no label table, the
structural checks still run and the label-dependent ones are skipped with a warning.

Usage: python3 validate_report.py [--lang en|pt-BR] REPORT.md [OTHER.md ...]
Output: one `file:line: message` line per error; exit code 1 if there is any error.
"""

import re
import sys
from pathlib import Path

ALLOWED_EMOJI = {"✅", "\U0001F7E1", "❌", "⚠"}  # ✅ 🟡 ❌ ⚠
EMOJI_RANGES = [(0x1F000, 0x1FAFF), (0x2600, 0x27BF), (0x2B00, 0x2BFF)]

# Keep in sync with references/locales.md.
LOCALES = {
    "en": {
        "reproduction": "**Reproduction:**",
        "fix": "**Fix:**",
        "acceptance": "**Acceptance criteria:**",
        "verdict": "**Verdict:**",
        "severities": ("Critical", "High", "Medium", "Low"),
        "current_state": "Current state",
        "precedents": "Precedents in the code",
        "non_goals": "Non-goals",
        "executive_summary": "Executive summary",
        "sources": "Sources consulted",
        "verification_performed": "Verification performed",
    },
    "pt-BR": {
        "reproduction": "**Reprodução:**",
        "fix": "**Correção:**",
        "acceptance": "**Critério de aceite:**",
        "verdict": "**Veredicto:**",
        "severities": ("Crítica", "Alta", "Média", "Baixa"),
        "current_state": "Estado atual",
        "precedents": "Precedentes no código",
        "non_goals": "Não-objetivos",
        "executive_summary": "Sumário executivo",
        "sources": "Fontes consultadas",
        "verification_performed": "Verificação executada",
    },
}

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
H2_RE = re.compile(r"^## (?!#)(.*)$")
H2_NUM_RE = re.compile(r"^(\d+)\. \S")
FINDING_ID_RE = re.compile(r"^### ([PU]-\d+)\b")
CITATION_RE = re.compile(r"\[F(\d+)\]")
SOURCE_ROW_RE = re.compile(r"^\|\s*F(\d+)\s*\|")
CHECKED_RE = re.compile(r"^\s*[-*] \[[xX]\]")


def finding_title_re(severities):
    sev = "|".join(severities) if severities else r"[^*]+"
    return re.compile(r"^### [PU]-\d{2} · .+ — \*\*(" + sev + r")\*\*( \(.+\))?$")


def detect_locale(text):
    """Locale with the most distinct labels present, or None below two.

    A single shared word is not enough: Spanish also writes `**Veredicto:**`, and a
    Spanish report must fall back to structural checks, not be judged as pt-BR.
    """
    scores = {
        code: sum(1 for k, v in labels.items() if k != "severities" and v in text)
        for code, labels in LOCALES.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] >= 2 else None


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


def prev_nonblank(lines, idx):
    """Previous non-empty line before 0-based index `idx`, or None."""
    for j in range(idx - 1, -1, -1):
        if lines[j].strip():
            return lines[j].strip()
    return None


def is_emoji(ch):
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in EMOJI_RANGES) and ch not in ALLOWED_EMOJI


def validate(path, lang=None):
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    errors = []

    def err(n, msg):
        errors.append(f"{path}:{n}: {msg}")

    if not lines:
        return [f"{path}:1: empty file"]

    if lang is None:
        lang = detect_locale(text)
        if lang is None:
            print(f"{path}: warning: no known label set (en, pt-BR) found; "
                  "label-dependent checks skipped — check them by hand", file=sys.stderr)
    L = LOCALES.get(lang)

    if lines[0].strip() == "---":
        err(1, "YAML frontmatter is not allowed; the first line is the H1")
    if not lines[0].startswith("# "):
        err(1, "the first line must be the H1 (`# Title`)")

    prose = prose_lines(lines)

    # Headings
    h1_count = 0
    h2s = []  # (line, title)
    for n, line in prose:
        if line.startswith("# "):
            h1_count += 1
            if h1_count > 1:
                err(n, "more than one H1; use a single H1")
        elif line.startswith("####"):
            err(n, "H4 or deeper is not allowed; use H3 or restructure")
        else:
            m = H2_RE.match(line)
            if m:
                h2s.append((n, m.group(1).strip()))

    expected = 1
    for n, title in h2s:
        m = H2_NUM_RE.match(title)
        if not m:
            err(n, f"unnumbered H2 (`## {expected}. …`): '{title}'")
            continue
        num = int(m.group(1))
        if num != expected:
            err(n, f"H2 out of sequence: expected {expected}, found {num}")
        expected = num + 1
        if prev_nonblank(lines, n - 1) != "---":
            err(n, "missing `---` before this H2")

    def section_of(lineno):
        current = ""
        for n, title in h2s:
            if n > lineno:
                break
            current = title
        return current

    # Closing blockquote after the last `---`
    prose_idx = [n for n, line in prose if line.strip() == "---"]
    if not prose_idx:
        err(len(lines), "missing the `---` followed by the closing blockquote")
    else:
        tail = [(n, line) for n, line in prose if n > prose_idx[-1] and line.strip()]
        if not tail:
            err(prose_idx[-1], "missing the closing blockquote after the last `---`")
        elif any(not line.lstrip().startswith(">") for _, line in tail):
            bad = next(n for n, line in tail if not line.lstrip().startswith(">"))
            err(bad, "only the closing blockquote may follow the last `---`")

    # P-NN / U-NN findings
    title_re = finding_title_re(L["severities"] if L else None)
    sev_hint = "/".join(L["severities"]) if L else "Severity"
    seen_ids = {}
    finding_starts = []
    for n, line in prose:
        m = FINDING_ID_RE.match(line)
        if not m:
            continue
        fid = m.group(1)
        if fid in seen_ids:
            err(n, f"duplicate identifier {fid} (first on line {seen_ids[fid]})")
        seen_ids[fid] = n
        finding_starts.append(n)
        if not title_re.match(line):
            err(n, f"finding title not in the form `### {fid[0]}-NN · <title> — "
                   f"**<{sev_hint}>**`")
    if L:
        heading_lines = sorted([n for n, _ in h2s] + [
            n for n, line in prose if line.startswith("### ")
        ])
        for start in finding_starts:
            end = next((h for h in heading_lines if h > start), len(lines) + 1)
            body = [line for n, line in prose if start < n < end]
            for field in (L["reproduction"], L["fix"], L["acceptance"]):
                if not any(line.startswith(field) for line in body):
                    err(start, f"finding without the {field} field")

        # Fix immediately followed by acceptance criteria
        for i, line in enumerate(lines):
            if not line.startswith(L["fix"]):
                continue
            j = i + 1
            found = False
            while j < len(lines) and lines[j].strip():
                if lines[j].startswith(L["acceptance"]):
                    found = True
                    break
                j += 1
            if not found:
                err(i + 1, f"`{L['acceptance']}` must come right below `{L['fix']}`, "
                           "with no blank line")

    # Emojis, checkboxes and citations (outside code blocks and inline code)
    cited = {}
    for n, line in prose:
        bare = INLINE_CODE_RE.sub("", line)
        for ch in bare:
            if is_emoji(ch):
                err(n, f"emoji outside the allowed set (✅ 🟡 ❌ ⚠️): '{ch}'")
                break
        if L and CHECKED_RE.match(bare) and L["verification_performed"] not in section_of(n):
            err(n, f"a checked `[x]` box is only allowed in "
                   f"'{L['verification_performed']}' (mode C)")
        for m in CITATION_RE.finditer(bare):
            cited.setdefault(int(m.group(1)), n)

    # Required parts per mode, detected from the section titles
    if L:
        titles = [t for _, t in h2s]
        h3_titles = [line[4:] for _, line in prose if line.startswith("### ")]
        if any(L["current_state"] in t for t in titles):  # mode A
            for req in (L["precedents"], L["non_goals"]):
                if not any(req in t for t in h3_titles):
                    err(next(n for n, t in h2s if L["current_state"] in t),
                        f"mode A: missing the `### {req}` subsection in "
                        f"'{L['current_state']}'")
        if any(L["executive_summary"] in t for t in titles):  # modes B and C
            if not any(line.startswith(L["verdict"]) for _, line in prose):
                err(next(n for n, t in h2s if L["executive_summary"] in t),
                    f"missing the `{L['verdict']}` in the executive summary")

    # Sources table: by title when the locale is known, else any `| Fn |` row
    defined = {}
    if L:
        sources_h2 = [(n, t) for n, t in h2s if L["sources"] in t]
        if sources_h2:
            start = sources_h2[0][0]
            if h2s and h2s[-1][0] != start:
                err(start, f"'{L['sources']}' must be the last numbered section")
            defined = {int(m.group(1)): n for n, line in prose if n > start
                       for m in [SOURCE_ROW_RE.match(line)] if m}
        elif cited:
            err(min(cited.values()),
                f"there are [Fn] citations but the '## N. {L['sources']}' section is missing")
        has_sources = bool(sources_h2)
    else:
        defined = {int(m.group(1)): n for n, line in prose
                   for m in [SOURCE_ROW_RE.match(line)] if m}
        has_sources = bool(defined) or bool(cited)
    if has_sources:
        for f, n in sorted(cited.items()):
            if f not in defined:
                err(n, f"[F{f}] cited but missing from the sources table")
        for f, n in sorted(defined.items()):
            if f not in cited:
                err(n, f"F{f} is in the sources table but never cited in the text")

    return errors


def main(argv):
    args = argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0 if args else 2
    lang = None
    if args[0] == "--lang" or args[0].startswith("--lang="):
        if "=" in args[0]:
            lang, args = args[0].split("=", 1)[1], args[1:]
        else:
            lang, args = (args[1] if len(args) > 1 else ""), args[2:]
        if lang not in LOCALES:
            print(f"unknown --lang '{lang}'; known: {', '.join(LOCALES)}", file=sys.stderr)
            return 2
    all_errors = []
    for p in args:
        if not Path(p).is_file():
            all_errors.append(f"{p}:0: file not found")
            continue
        all_errors.extend(validate(p, lang))
    for e in all_errors:
        print(e)
    if all_errors:
        print(f"\n{len(all_errors)} error(s).", file=sys.stderr)
        return 1
    print("OK — no shape errors.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
