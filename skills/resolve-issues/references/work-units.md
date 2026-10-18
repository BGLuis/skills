# Work units — grouping, branches, commits, parallel agents

A work unit is one branch: the issues that ship together. Getting the units right decides whether
the user reviews one coherent change or untangles two unrelated ones from the same diff.

## Contents

- Grouping
- Branches
- Commits
- Parallel agents in worktrees

## Grouping

Apply in order; the first rule that matches decides.

1. **An epic or a story with sub-issues** is one unit. Every open sub-issue goes in, in the work
   order `issue_context.py` printed (each one after the siblings that block it). A sub-issue that
   waits for an open issue outside the tree is left out and named in the report.
2. **Issues with the same root cause** are one unit. The test: fixing the cause of one makes the
   acceptance criteria of the other hold too. Sharing a file, a module, or a symptom is not enough
   — two slow screens can be slow for unrelated reasons.
3. **Everything else** is one unit per issue, even when the issues touch the same area. The report
   says which ones are related, and the user decides whether to merge them.

An issue found in step 2 of the skill (not given by the user) joins a unit only by rule 2, and the
plan says so; it is never resolved silently.

## Branches

Unless the repository says otherwise:

- name `<type>/<N>-<slug>`: `type` from the issue's type or `type:` label (`feat`, `fix`,
  `refactor`, `perf`, `docs`, `chore`, `test`), defaulting to `fix` for a defect and `feat` for new
  behavior; `N` is the epic for an epic, the lowest number for a same-cause group; `slug` is two to
  four words of the title, lower-case and hyphenated;
- start from the latest default branch: `git switch -c <branch> origin/<default>` after the
  `git fetch` of step 0;
- one branch per unit, never reused for another unit.

## Commits

Unless the repository says otherwise:

```text
type(scope): subject in the imperative (#N)

Why the change is needed and what it changes, in two to five lines: the root cause, the
decision and its source, what the user can observe now.

Closes #N
```

- **One issue:** one commit per logical change; the last one carries `Closes #N`, the earlier ones
  `Refs #N`.
- **Epic or story:** one commit per sub-issue, in work order, each with `Closes #<sub-issue>` and
  `Refs #<epic>`. The epic itself is closed (`Closes #<epic>` in the last commit) only when every
  sub-issue is in the branch and the epic's own Definition of Done holds; otherwise it stays
  `Refs`.
- **Same root cause:** one commit for the cause, with one `Closes` line per issue.

`Closes` closes the issue when the commit reaches the default branch, so it goes only on the commit
that finishes that issue. When the repository reserves closing keywords for the pull request body,
use `Refs` in every commit and list the `Closes` lines in the report for the pull request.

## Parallel agents in worktrees

When there are two or more independent units and the environment can run agents in parallel,
give each unit to its own agent. Each agent works in its own worktree, so no two agents share a
working tree, an index, or a checked-out branch:

```bash
git worktree add ../<repo>-<N> -b <branch> origin/<default>
```

Before delegating, predict the files each unit touches from the evidence of its issues. Two units
that share a file run one after the other, in the same agent or in sequence: in parallel they
produce conflicting branches.

A delegated agent cannot ask the user anything, so the plan gate stays with you:

1. You run steps 0 to 3 for every unit: rules, issue context, grouping.
2. Each agent runs steps 4 to 9 for its unit with this skill loaded, and gets in its brief: the
   unit's issues and work order, the branch and worktree path, the repository rules you found in
   step 1 (branch, commit, and check commands), and this instruction: *if any plan-gate condition
   of step 6 holds, stop after the plan and return it without writing code.*
3. You collect the reports, relay every returned plan to the user, and resume those units once the
   user answers.

Without parallel agents, work the units one after another in the same order. Leave the worktrees
in place for the user to review; the report names each path, and `git worktree remove <path>`
cleans one up after its branch is merged.
