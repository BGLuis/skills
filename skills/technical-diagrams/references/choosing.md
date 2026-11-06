# Choosing the diagram

Pick the type from the question the reader brings. One question per figure: a figure answering two
answers neither, and a figure that needs a legend of invented symbols is answering too many.

## Contents

- Question → type
- When not to draw
- Before and after
- Splitting

## Question → type

| The reader asks | Draw | Mermaid |
|---|---|---|
| What happens, in what order, with which decisions? | Process flow | `flowchart LR` (or `TD` for deep trees) |
| Who talks to whom, in what order, with what messages? | Sequence | `sequenceDiagram` |
| Which states can this thing be in, and what moves it? | State machine | `stateDiagram-v2` |
| What data exists and how does it relate? | Entity-relationship | `erDiagram` |
| What is this system, who uses it, what does it depend on? | System context | `flowchart LR` with subgraphs (`architecture.md`) |
| Which deployable pieces make up the system and how do they connect? | Containers | `flowchart LR` with lanes (`architecture.md`) |
| Which modules depend on which? | Dependency graph | `flowchart LR`, modules as nodes |

Draw behavior and structure at the level of systems, services, modules, roles, states, and
business objects. Classes and methods stay in the code — an IDE generates a fresher picture of
them than any committed one, and a figure at that level goes stale with the next refactor.
`classDiagram` is outside this skill for that reason.

Flowchart direction: `LR` for sequences of steps and pipelines; `TD` for hierarchies, deep trees,
or many siblings at one level. Pick once; never change direction inside a figure.

## When not to draw

- A linear flow of three or four steps: a numbered list says it with less.
- A list of things, or attributes compared before and after: a table.
- One shape with one arrow: a sentence.
- Numbers over time or across categories: a chart, not this skill.
- The figure would only restate the paragraph next to it.

## Before and after

When a change alters a flow — a pull request, a mode C report, a proposal in mode A — draw the same
scope twice with the same node ids and layout, so the eye finds the difference:

- the **before** with the nodes that disappear marked by `classDef removed`;
- the **after** with the nodes that appear or change marked by `classDef changed`;
- only the part of the flow the change touches, plus one node on each side for context.

If only attributes change (a timeout, a limit, a name), use a table instead: the topology is the
same, so a pair of identical figures teaches nothing.

## Splitting

Above 9 nodes or 12 edges, look for the seam: the place where the flow hands off to another
module, the boundary of a subgraph, or the point where a happy path and an error path diverge.
Draw an overview where that part is one node, and a detail figure for the inside of it. Reuse the
node id of the collapsed node as the detail figure's title so the two connect.
