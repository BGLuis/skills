---
name: review-pull-requests
description: Reviews a GitHub pull request someone opened against the user's project and judges whether it fits the project — its architecture, conventions, ADRs, and the issue it claims to close — and whether it is correct, tested, safe, and worth merging. Reads every changed line; checks its claims against the code; flags deprecated APIs, outdated, yanked, or vulnerable dependencies, and use against the docs of the installed version; runs checks and probes in an isolated worktree, reading an outside contributor's build and CI changes first; and drafts one review (summary of what was and was not run, labeled inline comments) that is validated against the live diff and posted only after the user approves it. Also re-reviews after the author pushes. Use when the user asks to review, check, evaluate, or critique a pull request, or whether it can be merged. Do NOT use to fix a pull request's feedback (that is resolve-pull-requests), to resolve an issue (resolve-issues), or for platforms other than GitHub.
---

# Review Pull Requests

A review answers one question: does merging this make the project better, as the project defines
better? The yardstick is the repository's own rules — `AGENTS.md`, the ADRs, the contribution
guide, the code around the change — and the issue the pull request says it closes, not personal
taste. Approve when the change clearly improves the code's health even if it is not perfect;
block only for what would make it worse, with the evidence that shows it.

This skill **depends on the technical-report skill** for its research method and on the
resolve-issues skill for reading issues (`scripts/issue_context.py`) and checking acceptance
criteria (`references/verification.md`). Load them; if one is missing, say what the review could
not check because of it.

Posting a review is public and permanent: **nothing is posted until the user approves the exact
draft**, in this session, for this pull request.

## 0. Preconditions

1. `gh auth status` succeeds and the project is a local clone of the pull request's repository.
2. Everything runs in a worktree of your own — `git worktree add --detach ../<repo>-review<N>
   origin/<base>`, then `gh pr checkout <N>` inside it — so the user's checkout is never touched.

## 1. Learn the yardstick

Before opening the diff, read what "fits the project" means here: `AGENTS.md`, `CLAUDE.md`,
`GEMINI.md`, `CONTRIBUTING*`, the ADR index and the ADRs of the area the change touches, the pull
request template, the lint and format configs, the CI workflows (which commands gate a merge),
and the roadmap or milestones when the change adds a feature. Note each rule you will check, with
its source. When the repository writes nothing about an aspect, the yardstick is the surrounding
code: the change should look like the code next to it.

## 2. Read the pull request

```bash
python3 <skill-directory>/scripts/review_context.py <PR number or URL> [-R owner/repo]
```

It prints the author and their association with the repository, the issues the pull request
closes, the checks, the size, every changed file classified (code, test, doc, lockfile, or a file
that **executes** at build, test, or install time), the reviews already left, the description,
and the **Flags**. Then:

- **Read what came before.** The issues it closes (`issue_context.py` of the resolve-issues skill),
  their discussion, and the earlier reviews: do not repeat a point someone already made; say
  whether it was addressed.
- **Find what asked for the change.** With no linked issue, look for the request (an issue, a
  roadmap item, a discussion). A change nobody asked for is not wrong, but whether the project
  wants it is the maintainer's call — raise it in the summary, before the line comments.
- **Too large to review well** (the script flags more than 1000 changed lines): say so, and either
  ask for a split or state which parts the review covers.

## 3. Run nothing untrusted unread

Code from a pull request runs on your machine when you build it, test it, or even install its
dependencies. When the author is outside the repository (the script flags it) and the pull request
changes a file that executes — a workflow, a build script, a test config, a manifest, a lockfile,
a git hook — read those files completely before running any command in the worktree, following
`references/safety.md`. If anything there does more than the change needs (network calls,
writing outside the project, reading credentials, obfuscated code), stop and tell the user: that
is the finding, and nothing runs.

## 4. Review every line

Read the whole diff, every line a person wrote, in the context of the full files, with
`references/checklist.md`. In order of weight:

1. **Fit:** the architecture, the layering, the conventions and ADRs of step 1 — each rule checked
   against the lines it governs.
2. **Purpose and design:** it does what its issue asks, the pieces belong where they are, and it is
   no more complex than the problem.
3. **Correctness:** edge cases, errors, concurrency, resource limits, compatibility of anything
   public.
4. **The claims:** every guarantee the description, a doc comment, or an ADR makes ("cannot be
   stored under another key", "no lock on the hot path") is checked against what the code
   enforces. An unenforced guarantee is a finding.
5. **Tests:** they exist for the new behavior, and they fail when the behavior breaks.
6. **Security, performance, dependencies, documentation**, and the smaller points: naming,
   comments, style the repository's tools do not already enforce.

Then run the four research checks of `references/research.md` — every review that touches code
does all four, with the sources in its order (the lockfile, Context7 through the find-docs skill
when installed, the official site and changelog, the registries and OSV, web search only as a
lead):

1. **Dependency versions:** `scripts/dependency_diff.py` lists every package the branch adds or
   changes, with the latest release, yanked or deprecated status, and OSV advisories.
2. **Deprecated APIs:** every library call the change adds, checked in the documentation and
   changelog of the installed version, and in the build's deprecation warnings.
3. **Use against the documentation:** each library feature the change relies on, compared with
   its documented contract — call order, thread-safety, cleanup, errors, limits, defaults.
4. **The project's own pins and rules:** the toolchain, where dependencies are declared, the
   pinning policy.

A finding that rests on a source links it, with the version. Behavior you did not check in this
session is not a finding — at most a `question`.

## 5. Run and probe

In the worktree, run the commands CI gates on, the tests of the area, and — to settle a doubt —
throwaway probes: a test that triggers the edge case you suspect, the change reverted to see
whether its tests fail. Probes are never committed. Keep the list of what ran, with results, and
of what did not run and why; the summary states both. A finding you reproduced says so; one from
reading only says that too.

## 6. Draft the review

Write it with `references/comments.md` into a draft file outside the repository
(`post_review.py` documents the format):

- **Inline comments**, one per finding, on the line it is about, each opening with its label and
  weight — `**issue (blocking):**`, `**suggestion (non-blocking):**`, `**question:**`,
  `**nitpick:**` — then the mechanism, the evidence (the repro, the doc, the rule and its source),
  and the direction of a fix, not necessarily the code.
- **The summary**: what the change does well, specifically; the main findings first, then the
  smaller ones; a **Dependencies** line with what the four research checks found; what was run and
  what was not; and the verdict. Never a blanket claim ("follows
  all the guidelines") — name what was checked.
- **The verdict**: `REQUEST_CHANGES` when any finding is blocking, `APPROVE` when none is and the
  change improves the project, `COMMENT` when the open points are questions or the review could
  not cover enough to approve. The language is the repository's, or the one the user asks for.

## 7. Preview and post — after the user's yes

Validate the draft against the live diff:

```bash
python3 <skill-directory>/scripts/post_review.py <draft.json> --dry-run
```

It refuses a comment on a line the diff does not show, a draft written on a head that has moved
since, and an approval or change request on the user's own pull request. Show the user the whole
review — the verdict, the summary, and each inline comment with its location — in one message.
**Post only after the user approves it**, with their edits; then run the same command without
`--dry-run`, which posts it in one call and records it so it is never posted twice.

## 8. Re-review after the author pushes

Run `review_context.py` again and read only what changed since the review's commit
(`git range-diff` or `git diff <reviewed commit>..<head>`), plus each thread's replies. For each
earlier finding, decide: addressed (how), answered (accept the explanation or say why not), or
still open. Approve with a summary that lists how each point was addressed, or comment with what
is still open. The same preview-and-post rule applies.

## 9. Report to the user

In the language of the conversation: the verdict and why; the findings by weight with their
locations; what was run, what was probed, and what was not; whether the review was posted (its
link) or is waiting for approval; and, for findings that are the project's own debt rather than the
pull request's, a follow-up offered to the technical-issues skill.
