# Destinations

Where the figure goes decides its scope, its anchors, and what surrounds it.

## Contents

- Technical report
- Pull request description
- ARCHITECTURE.md
- Design doc and ADR

## Technical report

A report written with the technical-report skill keeps its own rules; the figure is one more
claim held to them. The report's validator skips code blocks, so a Mermaid block does not affect
its shape checks — run this skill's validator on the report file too.

| Report mode | Figure | Where |
|---|---|---|
| A — analysis/proposal | current flow, then the proposed flow, same ids | the current-state section and the proposal section |
| B — audit | the flow where the defect happens, the faulty step highlighted | inside the finding, before the reproduction |
| C — post-implementation | before and after of the flow that changed | the section describing what changed |

Anchors carry line numbers, like every other `file:line` in the report. A node marked `inferred`
also goes into the report's not-verified section. The figure's language follows the report's
language; ids stay in English or in the code's own words.

## Pull request description

Draw only when the change alters a flow, a sequence of calls, a state machine, or the connections
between pieces — not for every pull request.

- Scope: only the part the change touches, plus one node on each side for context; at most 9 nodes.
- Before and after with the same ids (`choosing.md`), or one figure with `classDef changed` on the
  nodes this pull request adds or modifies when the before is obvious.
- Anchors point at the lines on the pull request's branch, so a reviewer can open them in the diff.
- One sentence before the figure says what to look at: "The token refresh now goes through the
  cache before calling the auth server."
- Put the figure under the summary, before the list of changes. A reviewer reads the picture first
  and the diff second.

Validate the description text as a Markdown file before pasting it into the pull request.

## ARCHITECTURE.md

See `architecture.md`. Context figure first, container figure next, anchors to directories and
symbols rather than lines, and nothing that would change with most pull requests.

## Design doc and ADR

- Design doc: the proposed flow or architecture, and — when it replaces something — the current one
  beside it. Mark proposed nodes that do not exist yet as `inferred` only if their place in the code
  is unknown; otherwise anchor them to where they will live and say so in the text.
- ADR: at most one figure, showing the shape of the decision (the options as two small flows, or the
  chosen structure). The ADR is a record: once accepted, its figure is not updated — a later ADR
  supersedes it.
