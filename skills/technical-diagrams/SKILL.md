---
name: technical-diagrams
description: Draws Mermaid diagrams — flowcharts, sequence, state, and ER diagrams, system context and container views — embedded in Markdown that GitHub renders, to make technical reports, pull request descriptions, ARCHITECTURE.md, design docs, and ADRs easier to understand. Picks the diagram type from the question the reader brings, reads the code before drawing, anchors every node to a file, line, or symbol in a comment, keeps each figure small enough to read, and validates anchors, budget, and syntax with a script and a real render before handing it off. Use when the user asks for a flowchart, diagram, sequence, architecture view, or before/after picture of a flow, or when a report or pull request needs a graph rather than more paragraphs. Do NOT use for charts of data or metrics, diagrams in Figma or FigJam, UI mockups, a linear flow of three or four steps (that is a numbered list), images for Confluence, PDF, or slides, or writing the report or pull request itself (technical-report writes reports).
---

# Technical Diagrams

A diagram is a set of claims drawn instead of written. Every box and arrow is held to the same bar
as a sentence in a technical report: it is true of the code today, and someone can check it. The
prose says why; the diagram carries what prose serializes badly — branching, ordering, state, and
who talks to whom.

## 0. Decide whether to draw

Ask: would the reader learn more from this figure than from a well-written paragraph? Draw only
when the answer is yes. A linear flow of three or four steps is a numbered list; a list of things
is a table; a figure that restates the paragraph above it is furniture. One figure answers one
question — read `references/choosing.md` to match the question to the type.

## 1. Find the destination and its conventions

Read `references/destinations.md` for where the figure goes: a technical report (and which mode),
a pull request description, `ARCHITECTURE.md`, a design doc, or an ADR. If the repository already
has diagrams, read two of them first; their direction, vocabulary, and anchor style win over this
skill's defaults.

## 2. Read the code before drawing

Collect the real entities first: the modules, services, handlers, states, tables, and the calls
or events between them, each with the file and lines where it lives. Open every file you will
cite. Do not invent a node or an edge to round the picture out. A gap stays a gap, marked
`inferred`, and the text beside the figure says so. For architecture views, also read
`references/architecture.md`.

## 3. Write the Mermaid

Follow `references/mermaid-github.md` — the subset GitHub renders reliably, shapes with meaning,
quoting, and highlighting. Every figure has:

- an `accTitle:` line (and `accDescr:` when the title is not enough), for screen readers;
- **one anchor comment per node**, invisible in the render and visible in review:

  ```text
  %% @<nodeId>: path/to/file.ts:42-60          lines (reports, pull requests)
  %% @<nodeId>: path/to/module/                a directory
  %% @<nodeId>: path/to/file.py#ClassName      a symbol (ARCHITECTURE.md: lines rot)
  %% @<nodeId>: a.ts:10 + b.ts:4-9             several places
  %% @<nodeId>: external                       outside the repository
  %% @<nodeId>: inferred                       not confirmed in the code
  ```

- a size within budget: aim for at most 9 nodes and 12 edges. Above that, draw an overview and a
  detail figure instead of one dense one. The validator fails above 12 nodes or 16 edges.

Edges carry the event or condition in the domain's language ("payment confirmed"), not a
function name. Error paths are drawn where behavior differs. Labels use the names the code and
the project's glossary use.

## 4. Validate

Run the validator that ships with this skill (path relative to the skill directory) from the
repository root, with the render check:

```bash
python3 <skill-directory>/scripts/validate_diagrams.py --repo-root . --render <FILE>.md
```

It checks the anchors against the code (path exists, lines inside the file, symbol present), the
budget, the type, the syntax rules, and renders each block to SVG with `mmdc` or the
`minlag/mermaid-cli` Docker image. Without either installed, pass a command with
`--mmdc "npx -y @mermaid-js/mermaid-cli"` (it needs a Chrome or Chromium; point
`PUPPETEER_EXECUTABLE_PATH` at a local one). Fix every error and run it again until it exits
clean. A diagram never goes into the document before it passes.

If the render reports `skipped`, the syntax is **not verified** — say so to the user, never call
it validated. With `--keep-svg <dir>`, look at the SVGs: an arrow crossing the whole figure or a
cramped cluster means the layout needs a different direction or a split.

## 5. Insert and keep it in step

Put the ```` ```mermaid ```` block in the document, directly after the sentence that tells the
reader what to look at. The figure and the prose share one home per fact: the prose does not
narrate the figure step by step. When a change alters a drawn flow, the figure changes in the same
commit; a stale anchor fails the validator.

## 6. Report to the user

Tell the user, in the language of the conversation:

- where each figure went and which question it answers;
- the validator result, and whether the render ran or was skipped;
- each `inferred` node and why it could not be confirmed;
- what was left out to stay within budget, and whether a detail figure would help.
