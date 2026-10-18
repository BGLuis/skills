# Research sources — what to consult, in which order

The full method lives in the technical-report skill (`references/research.md`): this file fixes
which sources this skill consults and how far to go when resolving an issue. Research supports a
decision of the change, or it is not done.

## Contents

- Order
- Evidence hierarchy
- Budget
- Recording the sources

## Order

Do them in this order, and do not jump ahead:

1. **The repository.**
   - Precedents: code that already solves something similar — the same library in another module,
     the same pattern, a sibling feature, its tests. Search by API name, pattern, and symptom.
     Record each with `file:line` and decide to **reuse** it or **diverge**, saying why.
   - Versions: read the lockfile (`package-lock.json`, `pnpm-lock.yaml`, `poetry.lock`, `uv.lock`,
     `go.sum`, `Cargo.lock`, `Gemfile.lock`…) and note the installed version of every dependency
     the change uses. Every lookup below is made against that version.
2. **Context7** — the documentation of the installed version, through the find-docs skill or the
   Context7 tools when the environment has them. Ask for the feature's page, its documented limits,
   and its error behavior.
3. **The official site and the changelog** — when Context7 does not have the library or the
   version, and always for the release notes between the installed version and the latest: a fix
   that the latest version makes trivial may not exist in the installed one, and an API the issue
   suggests may be deprecated.
4. **Web search** — to find a page of levels 1 to 3 that steps 2 and 3 missed: a migration guide, a
   maintainer's example, a known bug. A blog post or a forum answer is a lead, never the support of
   a decision.

## Evidence hierarchy

When two sources disagree, the higher one wins and the disagreement goes into the report as ⚠️:

1. The repository's code and what you ran in this session.
2. The official documentation of the installed version.
3. Examples maintained by the library's authors.
4. Mature third-party projects.
5. Articles, answers, posts — leads only.

The issue itself is not on this list: it is a claim to check, not a source. Behavior you did not
check in this session is `[modeled]`, and the model's memory is never a source.

## Budget

Stop when each decision has a level 1 to 3 basis. Per decision, as a guide:

| Source | Limit |
|---|---|
| Precedents | up to 3 places, the most similar |
| Context7 / official docs | 2 to 4 pages |
| Changelog | the versions between the installed one and the latest |
| Web search | 1 or 2 searches, only when 2 and 3 left a gap |

A source that cannot be consulted (no network, a private package, an undocumented version) is said
in the report, and the claims that depended on it are `[modeled]`.

## Recording the sources

Keep a table as you go; it goes into the final report, not into the code:

```markdown
| # | Source | Type | Version | Consulted on | Supports |
|---|---|---|---|---|---|
| F1 | [`pg-query-stream` — README](https://github.com/brianc/node-postgres/tree/master/packages/pg-query-stream) | Official doc | 4.7.0 | 2026-10-18 | stream the rows (#142) |
| F2 | `src/api/audit/stream.ts:15-48` | Precedent | — | 2026-10-18 | reused cursor + CSV transform |
```

A commit message cites a source only when it explains a choice that would look wrong without it
(a workaround for a library bug, a documented limit).
