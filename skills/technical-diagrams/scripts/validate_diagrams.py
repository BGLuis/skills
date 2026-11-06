#!/usr/bin/env python3
"""Validates the Mermaid diagrams embedded in Markdown files by the technical-diagrams skill.

For every ```mermaid block outside other code blocks:
- the type is one GitHub renders reliably (beta types and C4 are rejected);
- an `accTitle:` line names the figure for screen readers;
- every node, participant, state, or entity has exactly one anchor comment,
  `%% @<id>: <anchor>`, and no anchor names an id the diagram does not draw.
  An anchor is `external`, `inferred`, or locations joined by ` + `, each
  `path`, `path:12`, `path:12-30`, `path:12,40-44`, or `path#symbol`;
- with --repo-root, each location exists under that root: the path, the lines
  within the file's length, and the symbol as a definition — in Python a
  `def`, `class`, or module-level assignment (`Class.method` for a method), in
  shell a function or variable assignment, in any other file the name as a
  whole word;
- the diagram stays within the size budget (warning above the target, error
  above the maximum) — a bigger one is two diagrams;
- no `end`/`graph`/`subgraph` as an id, no literal `\\n`, no HTML other than
  <br>, no emoji, no unquoted label holding brackets or parentheses, no edge
  to a subgraph id, no `click` handler.

With --render, each block is rendered to SVG with mmdc (from PATH, or the command
given in --mmdc), falling back to the minlag/mermaid-cli Docker image. When no
renderer exists the render check is reported as skipped, never as passed.
--keep-svg DIR and --png DIR save each render as `<file stem>-<line>.svg|png`,
where <line> is the line of the block's first line inside the fence.

Usage: python3 validate_diagrams.py [--repo-root DIR] [--render] [--mmdc CMD]
                                    [--keep-svg DIR] [--png DIR]
                                    [--max-nodes N] [--max-edges N] FILE.md [...]
Output: `file:line: message` per error, `file:line: warning: message` per warning;
exit code 1 if there is any error.
"""

import argparse
import ast
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

TARGET_NODES, TARGET_EDGES = 9, 12
MAX_NODES, MAX_EDGES = 12, 16

RESERVED_IDS = {"end", "graph", "subgraph"}
EMOJI_RANGES = [(0x1F000, 0x1FAFF), (0x2600, 0x27BF), (0x2B00, 0x2BFF)]
HTML_TAG = re.compile(r"<(?!br\s*/?>)/?[A-Za-z][^>]*>")
ANCHOR = re.compile(r"^%%\s*@([\w-]+)\s*:\s*(.*)$")
LOCATION = re.compile(r"^([^\s:#]+)(?::(\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*))?(?:#(\S+))?$")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([\w-]*)")

CHECKED_TYPES = {"flowchart", "graph", "sequenceDiagram", "stateDiagram",
                 "stateDiagram-v2", "erDiagram"}
UNCHECKED_TYPES = {"classDiagram", "gantt", "pie", "mindmap", "journey", "gitGraph",
                   "timeline", "quadrantChart", "requirementDiagram"}


@dataclass
class Block:
    path: str
    start: int  # file line of the first line inside the fence
    lines: list


@dataclass
class Graph:
    nodes: dict = field(default_factory=dict)  # id -> file line of first appearance
    edges: int = 0
    issues: list = field(default_factory=list)  # (file line, message)
    linked: dict = field(default_factory=dict)  # id -> file line of first edge touching it

    def add(self, node_id, line):
        self.nodes.setdefault(node_id, line)


def extract_blocks(path, text):
    """Mermaid blocks outside other fenced code blocks (those are samples, not figures)."""
    blocks, fence, current = [], None, None
    for n, line in enumerate(text.splitlines(), 1):
        m = FENCE.match(line)
        if fence is None:
            if m:
                fence = m.group(1)
                if m.group(2) == "mermaid":
                    current = Block(path, n + 1, [])
            continue
        if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not m.group(2):
            if current is not None:
                blocks.append(current)
            fence, current = None, None
            continue
        if current is not None:
            current.lines.append(line)
    return blocks


# --- flowchart ------------------------------------------------------------------------

FLOW_ID = re.compile(r"[A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)*")
EDGE_TEXT = re.compile(r"<?(?:--|==|-\.)\s+(.*?)\s+(?:-->|---|\.->|\.-|==>|===)")
EDGE = re.compile(r"<?(?:-\.+-|-{2,}|={2,}|~{3,})[>ox]?")
SHAPES = [("(((", (")))",)), ("((", ("))",)), ("([", ("])",)), ("[(", (")]",)),
          ("[[", ("]]",)), ("{{", ("}}",)), ("[/", ("/]", "\\]")), ("[\\", ("\\]", "/]")),
          ("[", ("]",)), ("(", (")",)), ("{", ("}",)), (">", ("]",))]
FLOW_SKIP = re.compile(r"^(direction|classDef|class|style|linkStyle|click|accTitle|accDescr)\b")
SPECIAL = set("()[]{}")


def _label(line, pos, closers, n, issues):
    """Parses a shape's label starting at pos; returns the position after the closer."""
    if line.startswith('"', pos):
        end = line.find('"', pos + 1)
        if end < 0:
            issues.append((n, "unterminated quoted label"))
            return None
        rest = end + 1
        while rest < len(line) and line[rest] == " ":
            rest += 1
        for c in closers:
            if line.startswith(c, rest):
                return rest + len(c)
        issues.append((n, "quoted label is not closed by its shape"))
        return None
    hits = [(line.find(c, pos), c) for c in closers if line.find(c, pos) >= 0]
    if not hits:
        issues.append((n, "unclosed node label"))
        return None
    end, closer = min(hits)
    if SPECIAL & set(line[pos:end]):
        issues.append((n, f'label "{line[pos:end]}" holds brackets or parentheses; quote it'))
        return None
    return end + len(closer)


def _scan_flow_line(line, n, graph):
    groups, pos = [[]], 0
    while pos < len(line):
        if line[pos] in " \t;":
            pos += 1
            continue
        if line[pos] == "&":
            pos += 1
            continue
        m = EDGE_TEXT.match(line, pos) or EDGE.match(line, pos)
        if m:
            if m.re is EDGE_TEXT and SPECIAL & set(m.group(1)):
                graph.issues.append((n, f'edge text "{m.group(1)}" holds brackets; use |"..."|'))
            pos = m.end()
            if line.startswith("|", pos):
                end = line.find("|", pos + 1)
                text = line[pos + 1:end] if end > 0 else ""
                if not text.startswith('"') and SPECIAL & set(text):
                    graph.issues.append((n, f'edge label "{text}" holds brackets; quote it'))
                pos = end + 1 if end > 0 else len(line)
            groups.append([])
            continue
        m = FLOW_ID.match(line, pos)
        if not m:
            graph.issues.append((n, f"cannot parse `{line[pos:].strip()}`"))
            return
        node_id, pos = m.group(0), m.end()
        if line.startswith("@{", pos):
            end = line.find("}", pos)
            pos = end + 1 if end > 0 else len(line)
        else:
            for opener, closers in SHAPES:
                if line.startswith(opener, pos):
                    pos = _label(line, pos + len(opener), closers, n, graph.issues)
                    if pos is None:
                        return
                    break
        if line.startswith(":::", pos):
            m2 = re.compile(r":::[\w-]+").match(line, pos)
            pos = m2.end() if m2 else len(line)
        groups[-1].append(node_id)
        graph.add(node_id, n)
    groups = [g for g in groups if g]
    graph.edges += sum(len(a) * len(b) for a, b in zip(groups, groups[1:]))
    if len(groups) > 1:
        for node_id in (i for g in groups for i in g):
            graph.linked.setdefault(node_id, n)


def parse_flowchart(body):
    graph, subgraphs = Graph(), set()
    for n, raw in body:
        line = raw.strip()
        if not line or line.startswith("%%") or FLOW_SKIP.match(line):
            continue
        if line == "end" or line == "}":
            continue
        if line.startswith("subgraph"):
            m = re.match(r"subgraph\s+([\w-]+)", line)
            if m:
                subgraphs.add(m.group(1))
            continue
        _scan_flow_line(line, n, graph)
    for sg in subgraphs:
        graph.nodes.pop(sg, None)
        if sg in graph.linked:
            graph.issues.append((graph.linked[sg], f"edge to subgraph `{sg}`; "
                                 "connect to a node inside it"))
    return graph


# --- sequence, state, ER ----------------------------------------------------------------

SEQ_DECL = re.compile(r"^(?:create\s+)?(?:participant|actor)\s+([^\s]+)")
SEQ_MSG = re.compile(r"^(.+?)\s*(<<-->>|<<->>|-->>|->>|--x|-x|--\)|-\)|-->|->)\s*[+-]?\s*(.+?)\s*:")


def parse_sequence(body):
    graph = Graph()
    for n, raw in body:
        line = raw.strip()
        m = SEQ_DECL.match(line)
        if m:
            graph.add(m.group(1), n)
            continue
        m = SEQ_MSG.match(line)
        if m and not line.startswith(("Note", "note", "%%")):
            graph.add(m.group(1).strip(), n)
            graph.add(m.group(3).strip(), n)
            graph.edges += 1
    return graph


STATE_ALIAS = re.compile(r'^state\s+"[^"]*"\s+as\s+([\w-]+)')
STATE_DECL = re.compile(r"^state\s+([\w-]+)")
STATE_EDGE = re.compile(r"^(\S+)\s*-->\s*([^\s:]+)")
STATE_DESC = re.compile(r"^([\w-]+)\s*:")


def parse_state(body):
    graph, in_note = Graph(), False
    for n, raw in body:
        line = raw.strip()
        if in_note:
            in_note = line != "end note"
            continue
        if line.startswith("note ") and ":" not in line:
            in_note = True
            continue
        m = STATE_ALIAS.match(line) or STATE_DECL.match(line)
        if m:
            graph.add(m.group(1), n)
            continue
        m = STATE_EDGE.match(line)
        if m:
            for s in (m.group(1), m.group(2)):
                if s != "[*]":
                    graph.add(s, n)
            graph.edges += 1
            continue
        m = STATE_DESC.match(line)
        if m and not line.startswith(("accTitle", "accDescr")):
            graph.add(m.group(1), n)
    return graph


ER_REL = re.compile(r'^([\w-]+)\s+\S+(?:--|\.\.)\S+\s+([\w-]+)\s*:')
ER_ENTITY = re.compile(r"^([\w-]+)\s*(?:\[[^\]]*\])?\s*\{")


def parse_er(body):
    graph, in_entity = Graph(), False
    for n, raw in body:
        line = raw.strip()
        if in_entity:
            in_entity = line != "}"
            continue
        m = ER_ENTITY.match(line)
        if m:
            graph.add(m.group(1), n)
            in_entity = not line.endswith("}")
            continue
        m = ER_REL.match(line)
        if m:
            graph.add(m.group(1), n)
            graph.add(m.group(2), n)
            graph.edges += 1
    return graph


PARSERS = {"flowchart": parse_flowchart, "graph": parse_flowchart,
           "sequenceDiagram": parse_sequence, "stateDiagram": parse_state,
           "stateDiagram-v2": parse_state, "erDiagram": parse_er}


# --- anchors ----------------------------------------------------------------------------

def check_location(loc, root, n, err):
    m = LOCATION.match(loc)
    if not m:
        err(n, f"anchor location `{loc}` is not `path`, `path:lines`, or `path#symbol`")
        return
    rel, lines, symbol = m.groups()
    if root is None:
        return
    target = (root / rel).resolve()
    if root.resolve() not in target.parents and target != root.resolve():
        err(n, f"anchor `{rel}` points outside the repository")
        return
    if not target.exists():
        err(n, f"anchor `{rel}` does not exist under {root}")
        return
    if (lines or symbol) and not target.is_file():
        err(n, f"anchor `{rel}` is a directory; lines and symbols need a file")
        return
    if lines:
        count = len(target.read_text(errors="replace").splitlines())
        for part in lines.split(","):
            a, _, b = part.partition("-")
            lo, hi = int(a), int(b or a)
            if lo < 1 or hi < lo or hi > count:
                err(n, f"anchor `{rel}:{part}` is outside the file's {count} lines")
    if symbol and not defines(target, symbol):
        err(n, f"anchor `{rel}#{symbol}`: no definition of `{symbol}` in the file")


def _python_defines(tree, parts):
    """True when `parts` (e.g. ["Class", "method"]) names a def/class/assignment path."""
    scope = tree.body
    for i, part in enumerate(parts):
        last = i == len(parts) - 1
        found = None
        for node in scope:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name == part:
                    found = node
                    break
            elif last and isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if any(isinstance(t, ast.Name) and t.id == part for t in targets):
                    return True
        if found is None:
            return False
        scope = found.body
    return True


def defines(target, symbol):
    text = target.read_text(errors="replace")
    if target.suffix == ".py":
        try:
            return _python_defines(ast.parse(text), symbol.split("."))
        except SyntaxError:
            pass  # not parseable as Python; fall back to the whole-word check
    if target.suffix in (".sh", ".bash") or text.startswith("#!/usr/bin/env bash") \
            or text.startswith("#!/bin/bash") or text.startswith("#!/bin/sh"):
        name = re.escape(symbol)
        return re.search(rf"^\s*(?:function\s+)?{name}\s*\(\)|"
                         rf"^\s*(?:export\s+|readonly\s+|local\s+|declare\s+\S+\s+)?{name}=",
                         text, re.M) is not None
    return re.search(rf"(?<![\w-]){re.escape(symbol)}(?![\w-])", text) is not None


def check_anchors(graph, anchors, root, err, warn):
    seen = {}
    for n, node_id, value in anchors:
        if node_id in seen:
            err(n, f"`{node_id}` is anchored twice (first at line {seen[node_id]})")
            continue
        seen[node_id] = n
        if node_id not in graph.nodes:
            err(n, f"anchor for `{node_id}`, which the diagram does not draw")
            continue
        if not value:
            err(n, f"anchor for `{node_id}` is empty")
        elif value not in ("external", "inferred"):
            for loc in value.split(" + "):
                check_location(loc.strip(), root, n, err)
    for node_id, n in graph.nodes.items():
        if node_id not in seen:
            err(n, f"`{node_id}` has no anchor; add `%% @{node_id}: <path:lines | external | inferred>`")
    inferred = [i for _, i, v in anchors if v == "inferred"]
    if inferred:
        warn(anchors[0][0], f"inferred: {', '.join(inferred)} — say so in the text beside the diagram")


# --- per block --------------------------------------------------------------------------

def diagram_type(body):
    for n, raw in body:
        line = raw.strip()
        if line and not line.startswith("%%"):
            return n, line.split()[0]
    return None, None


def validate_block(block, root, limits, out):
    def err(n, msg):
        out.append((block.path, n, msg, False))

    def warn(n, msg):
        out.append((block.path, n, msg, True))

    body = list(enumerate(block.lines, block.start))
    n0, kind = diagram_type(body)
    if kind is None:
        err(block.start, "empty mermaid block")
        return
    if kind == "---":
        err(n0, "drop the frontmatter config; GitHub picks the theme for light and dark mode")
        return

    for n, raw in body:
        if raw.strip().startswith("%%"):
            continue
        if re.match(r"\s*click\s", raw):
            err(n, "`click` handler; GitHub's sandbox may drop it — the anchor points at the code")
        if "\\n" in raw:
            err(n, "literal `\\n` in a label; use <br> or a shorter label")
        if HTML_TAG.search(raw):
            err(n, "HTML tag in the diagram; only <br> is allowed")
        if any(lo <= ord(c) <= hi for c in raw for lo, hi in EMOJI_RANGES):
            err(n, "emoji in the diagram")

    if kind.startswith("C4") or kind.endswith("-beta") or kind in ("architecture", "block"):
        err(n0, f"`{kind}` does not render reliably on GitHub; use `flowchart` with subgraphs")
        return
    if kind in UNCHECKED_TYPES:
        warn(n0, f"`{kind}`: anchors and budget are not checked for this type")
        return
    if kind not in CHECKED_TYPES:
        err(n0, f"unknown diagram type `{kind}`")
        return

    if not any(raw.strip().startswith("accTitle") for _, raw in body):
        err(n0, "missing `accTitle:` — the figure needs a name for screen readers")

    content, in_descr = [], False
    for n, raw in body:
        line = raw.strip()
        if in_descr:
            in_descr = line != "}"
        elif re.match(r"accDescr\s*\{", line):
            in_descr = not line.endswith("}")
        elif n != n0:
            content.append((n, raw))
    graph = PARSERS[kind](content)
    for n, msg in graph.issues:
        err(n, msg)
    for node_id, n in graph.nodes.items():
        if node_id.lower() in RESERVED_IDS:
            err(n, f"`{node_id}` is a reserved word in Mermaid; rename the id")

    nodes, edges = len(graph.nodes), graph.edges
    max_nodes, max_edges = limits
    counts = ((nodes, "nodes", max_nodes, TARGET_NODES), (edges, "edges", max_edges, TARGET_EDGES))
    over = [f"{v} {k} (max {m})" for v, k, m, _ in counts if v > m]
    above = [f"{v} {k} (target {t})" for v, k, _, t in counts if v > t]
    if over:
        err(n0, f"{' and '.join(over)}; split into an overview and a detail diagram")
    elif above:
        warn(n0, f"{' and '.join(above)}; check the render for crowding")

    anchors = []
    for n, raw in body:
        m = ANCHOR.match(raw.strip())
        if m:
            anchors.append((n, m.group(1), m.group(2).strip()))
    check_anchors(graph, anchors, root, err, warn)


# --- render -----------------------------------------------------------------------------

def find_renderer(mmdc):
    """Returns (description, function that renders src -> dst or returns an error string)."""
    if mmdc:
        cmd = shlex.split(mmdc)
    elif shutil.which("mmdc"):
        cmd = ["mmdc"]
    else:
        cmd = None
    if cmd:
        def run(src, dst):
            p = subprocess.run(cmd + ["-q", "-i", str(src), "-o", str(dst)],
                               capture_output=True, text=True, timeout=180)
            return None if p.returncode == 0 else (p.stderr or p.stdout)
        return " ".join(cmd), run
    if shutil.which("docker"):
        def run(src, dst):
            p = subprocess.run(
                ["docker", "run", "--rm", "-u", f"{os.getuid()}:{os.getgid()}",
                 "-v", f"{src.parent}:/data", "minlag/mermaid-cli",
                 "-q", "-i", f"/data/{src.name}", "-o", f"/data/{dst.name}"],
                capture_output=True, text=True, timeout=300)
            return None if p.returncode == 0 else (p.stderr or p.stdout)
        return "docker minlag/mermaid-cli", run
    return None, None


def render_blocks(blocks, mmdc, out, keep=None, png=None):
    """Renders every block; returns summary lines for stdout."""
    name, run = find_renderer(mmdc)
    if run is None:
        out.append(("render", 0, "render skipped (no mmdc or docker); syntax not verified", True))
        return []
    print(f"render: using {name}", file=sys.stderr)
    rendered, written = 0, []
    with tempfile.TemporaryDirectory() as tmp:
        for i, block in enumerate(blocks):
            src = Path(tmp) / f"d{i}.mmd"
            dst = Path(tmp) / f"d{i}.svg"
            src.write_text("\n".join(block.lines) + "\n")
            try:
                failure = run(src, dst)
            except subprocess.TimeoutExpired:
                failure = "renderer timed out"
            if failure is None and (not dst.exists() or dst.stat().st_size == 0):
                failure = "renderer produced no SVG"
            if failure:
                lines = failure.strip().splitlines()
                at = next((i for i, l in enumerate(lines) if "rror" in l), 0)
                detail = " | ".join(l.strip() for l in lines[at:at + 4] if l.strip())
                out.append((block.path, block.start, f"render failed: {detail[:400]}", False))
                continue
            rendered += 1
            stem = f"{Path(block.path).stem}-{block.start}"
            if keep:
                Path(keep).mkdir(parents=True, exist_ok=True)
                shutil.copy(dst, Path(keep) / f"{stem}.svg")
            if png:
                dst_png = Path(tmp) / f"d{i}.png"
                try:
                    failure = run(src, dst_png)
                except subprocess.TimeoutExpired:
                    failure = "renderer timed out"
                if failure or not dst_png.exists():
                    out.append((block.path, block.start, "PNG render failed; the SVG rendered", True))
                else:
                    Path(png).mkdir(parents=True, exist_ok=True)
                    shutil.copy(dst_png, Path(png) / f"{stem}.png")
                    written.append(Path(png) / f"{stem}.png")
    summary = [f"render: {rendered} of {len(blocks)} diagram(s) rendered"]
    summary += [f"png: {p}" for p in written]
    if png:
        stems = {Path(b.path).stem for b in blocks}
        for old in sorted(Path(png).glob("*.png")):
            if old not in written and any(re.fullmatch(rf"{re.escape(st)}-\d+", old.stem) for st in stems):
                out.append((str(old), 0, "PNG from an earlier run (the block moved or was removed); "
                            "look only at the files listed under png:", True))
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("files", nargs="+")
    parser.add_argument("--repo-root", help="check that anchor locations exist under this directory")
    parser.add_argument("--render", action="store_true", help="render each block to SVG")
    parser.add_argument("--mmdc", help="renderer command, e.g. 'npx -y @mermaid-js/mermaid-cli'")
    parser.add_argument("--keep-svg", help="with --render, copy the SVGs into this directory")
    parser.add_argument("--png", help="with --render, also save a PNG of each block here, to look at")
    parser.add_argument("--max-nodes", type=int, default=MAX_NODES)
    parser.add_argument("--max-edges", type=int, default=MAX_EDGES)
    args = parser.parse_args(argv)

    root = Path(args.repo_root) if args.repo_root else None
    if root is not None and not root.is_dir():
        print(f"--repo-root {root} is not a directory", file=sys.stderr)
        return 2

    out, blocks = [], []
    for f in args.files:
        p = Path(f)
        if not p.is_file():
            out.append((f, 0, "file not found", False))
            continue
        found = extract_blocks(f, p.read_text(errors="replace"))
        if not found:
            out.append((f, 0, "no mermaid blocks found", True))
        for block in found:
            validate_block(block, root, (args.max_nodes, args.max_edges), out)
        blocks.extend(found)

    if root is None and blocks:
        out.append(("anchors", 0, "locations not checked against the code (no --repo-root)", True))
    summary = []
    if args.render and blocks:
        summary = render_blocks(blocks, args.mmdc, out, args.keep_svg, args.png)

    errors = [o for o in out if not o[3]]
    for path, n, msg, is_warning in out:
        print(f"{path}:{n}: {'warning: ' if is_warning else ''}{msg}")
    for line in summary:
        print(line)
    if errors:
        print(f"\n{len(errors)} error(s).", file=sys.stderr)
        return 1
    print(f"OK — {len(blocks)} diagram(s) checked.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
