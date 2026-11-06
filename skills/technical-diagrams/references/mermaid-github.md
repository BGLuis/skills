# Mermaid that GitHub renders

GitHub renders ```` ```mermaid ```` blocks in Markdown files, pull requests, issues, and comments,
in light and dark mode. This is the subset that renders reliably there and reads well.

## Contents

- Types
- Ids and labels
- Shapes
- Edges
- Subgraphs
- Highlighting
- Accessibility
- What breaks

## Types

Use `flowchart`, `sequenceDiagram`, `stateDiagram-v2`, and `erDiagram`. Beta and experimental
types (`architecture-beta`, `block-beta`, `C4Context`, `C4Container`, and anything ending in
`-beta`) render inconsistently across viewers and versions — model those views as a `flowchart`
with subgraphs (`architecture.md`). The validator rejects them.

## Ids and labels

- Ids are short camelCase words: `authApi`, `ordersDb`. No spaces. Never `end`, `graph`, or
  `subgraph` as an id — they are keywords.
- The label is the reader's name for the thing: `authApi[Auth API]`. Quote any label holding
  brackets, parentheses, braces, colons, or quotes: `job["Retry (3x)"]`, `-->|"O(1) lookup"|`.
- No literal `\n`; use `<br>` when a line break is unavoidable. No other HTML. No emoji.
- Keep labels to a few words. The detail lives in the prose and the anchor, not in the box.

## Shapes

Use shape for meaning, and only the few that carry it. All-rectangles is often right.

| Syntax | Means |
|---|---|
| `a[Text]` | step, service, module (default) |
| `a([Text])` | start or end of a flow, or an actor outside the system |
| `a{Text}` | decision — label it as the question: `a{Token valid?}` |
| `a[(Text)]` | datastore: database, cache, bucket, queue storage |
| `a[[Text]]` | a sub-process drawn in another figure |
| `a{{Text}}` | external system or third party |

The shape carries the kind; do not repeat it in the label (`db[(PostgreSQL)]`, not
`db[(Database: PostgreSQL)]`).

## Edges

| Syntax | Means |
|---|---|
| `a --> b` | call, data, or control flow (default) |
| `a -.-> b` | asynchronous, optional, "happens later", or out to another process or machine |
| `a ==> b` | the path the figure is about — at most one |
| `a -->|"label"| b` | the event or condition, in the domain's words |

Label the edges that leave a decision (`|yes|` / `|no|`, or the condition). One edge per pair of
nodes: merge two relationships into one label instead of drawing two arrows.

## Subgraphs

Group nodes that share a boundary — a deployable unit, a layer, a trust zone:
`subgraph api ["Public API"] ... end`. Connect edges to nodes inside the subgraph, not to the
subgraph id — the validator rejects an edge to a subgraph. Subgraphs do not need anchors; their
nodes do.

## Highlighting

Highlight one or two nodes at most — the ones the figure is about, or the ones a change touches.
Declare classes once and keep the colors legible on both themes:

```text
classDef changed stroke:#d97706,stroke-width:3px
classDef removed stroke:#dc2626,stroke-dasharray:4 4
class authApi,tokenCache changed
```

Prefer `stroke` over `fill`: a light fill with GitHub's dark theme hides the label. Never let color
be the only signal — say in the prose what the highlight marks.

## Accessibility

Start every figure with `accTitle: <what it shows>`; add `accDescr: <one sentence>` when the title
is not enough. Screen readers announce them; the validator requires `accTitle`.

## What breaks

- Frontmatter (`---` / `config:`) or `%%{init: ...}%%` theme overrides: they fix colors that then
  clash with the reader's theme. Leave theming to GitHub.
- `click` handlers and links inside nodes: GitHub renders diagrams in a sandbox where they may not
  work, and the anchor comment already points at the code. The validator rejects them.
- Notes in sequence diagrams are fine; long notes push the figure wide — keep them short.
- A parse error renders as an error box in the pull request. The validator's `--render` catches
  it before anyone else sees it.
