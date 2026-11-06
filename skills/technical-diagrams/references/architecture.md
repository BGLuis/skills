# Architecture views

For the figures in `ARCHITECTURE.md`, design docs, and the architecture section of a report: what
the system is, who uses it, and which deployable pieces it is made of.

## Contents

- Two levels
- One process: modules instead of containers
- Lanes
- Rules
- Granularity
- ARCHITECTURE.md

## Two levels

Two levels of the C4 model cover what most readers need:

1. **System context** — the system as one node, the people who use it, and the external systems it
   depends on. Answers "what is this and what does it touch?". Every `ARCHITECTURE.md` starts here.
2. **Containers** — the separately deployable or runnable pieces (web app, API, worker, database,
   queue, CLI) and how they talk. Answers "what runs, and where do requests go?".

Draw a component view (the modules inside one container) only when it changes how someone works
on the code — and then as a dependency graph of modules, not of classes. Both levels are drawn as
`flowchart LR` with subgraphs; Mermaid's C4 syntax does not render reliably on GitHub.

## One process: modules instead of containers

A CLI, a desktop app, a library, or a monolith runs as one process, so its container view is a
single box — skip it. Draw the system context, then a **module dependency graph** in its place:
the packages or directories that own a responsibility (the entry point, the job runner, the
plugin factory, the pipeline, the storage layer) as nodes, anchored to their directories, with the
calls between them as edges. Leave out utility modules every other module imports; an edge from
everything to `utils/` says nothing.

When a run of the program is the thing a newcomer needs to understand (what happens between
`main` and the output files), add a **sequence diagram of one representative run** under a "How a
run works" section, after the codemap. Its participants are the same modules as the dependency
graph, with the same ids, so the reader can move between the two figures.

## Lanes

Place nodes in subgraphs by role, left to right in the order a request travels:

| Subgraph id | Holds |
|---|---|
| `client` | browsers, mobile and desktop apps, CLIs, people |
| `gateway` | CDN, load balancer, API gateway, reverse proxy |
| `service` | APIs, monoliths, workers, cron jobs, serverless functions |
| `datastore` | databases, caches, object storage, search indexes |
| `async` | message brokers and queues: Kafka, RabbitMQ, SQS, Redis streams |
| `external` | third-party APIs and SaaS: payments, auth, email, monitoring |

Use the display label for the human title: `subgraph service ["Core services"]`. Omit lanes the
system does not have.

These lanes describe a networked system. For a local program, keep only the roles that exist and
give them local names: the user and the interfaces they use (`subgraph client ["You"]`), the
program itself as one node, what it reads and writes on disk (`subgraph datastore ["On disk"]` —
input folders, a SQLite file, a cache), and the remote services it calls (`external`). Anchor each
remote service to the adapter in the repository that calls it, not to `external`, when there is
one.

## Rules

- Requests flow `client → gateway → service → datastore`. A client does not reach a datastore, and
  a gateway does not reach a queue or an external API: a service mediates.
- Edges to or from `async` and `external` nodes are dotted (`-.->`): they leave the request path.
- Two datastores, two queues, or a datastore and a queue are never connected directly; the service
  that moves the data between them is a node.
- Label each edge with the protocol or the purpose: `|"HTTPS"|`, `|"enqueue order.created"|`,
  `|"Stripe: charges"|`.
- One edge per pair; a callback in the opposite direction gets its own labeled edge only when it is
  a distinct interaction.

## Granularity

One node is one independently deployable or runnable unit. A test: can it be deployed, scaled, or
restarted on its own? If not, it is part of the node next to it. Modules inside a service belong in
a component view, not in the container view.

## ARCHITECTURE.md

The file is a map for someone new to the code: the bird's-eye view, then a codemap of where things
live, then the invariants that are not visible in any single file. Figures support it like this:

- the system context figure under the overview, the container figure under the codemap;
- anchors to directories and symbols (`src/billing/`, `src/api/router.ts#createRouter`), not line
  numbers — the file is updated rarely and line numbers would rot between updates;
- names that a reader can search for: a node called `Billing worker` anchored to `src/billing/`
  lets them jump from the figure to the code;
- nothing that changes every sprint. If a figure would need an update for most pull requests, it is
  drawn at too low a level.
