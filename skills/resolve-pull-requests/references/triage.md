# Triage — what each piece of feedback asks, and what to do about it

Every item gets one decision, written in the triage table before any code changes. The table is
what the user approves at the plan gate and what the replies are written from.

## Contents

- The four places feedback lives
- The triage table
- Classifying a comment
- Deciding
- Checks
- Conflicts
- The issues the pull request closes

## The four places feedback lives

| Place | Has "resolved"? | How to answer |
|---|---|---|
| Inline review threads | Yes (`isResolved`) | Reply in the thread; resolve after CI passes |
| Inline comments outside any thread | No | Reply to the comment by its id (`references/replies.md`) |
| Review summaries (the body of a submitted review) | No | A conversation comment quoting the part answered |
| Conversation comments | No | A conversation comment, quoting or linking the one answered |

A review summary often holds the real request ("I'd like a different approach before merging"),
with the inline threads only as examples. Read it first. A summary with state
`CHANGES_REQUESTED` keeps the pull request blocked until that reviewer approves again.

Bot comments (Copilot, CodeRabbit, `github-actions`) get the same triage as a person's: they find
real defects, and they also produce noise — the decision is made on the code, not on the author.

## The triage table

```markdown
| # | Where | Who | Asks | Kind | Decision | Evidence |
|---|---|---|---|---|---|---|
| 1 | thread `src/cache.rs:31` | rev | release the slot on cancel | issue (blocking) | Fix | `src/cache.rs:31-40`: the guard is dropped before… |
| 2 | summary | rev | split `apply` in two | suggestion | Disagree | the split duplicates the lock; docs say… [F1] |
| 3 | check `CI / test` | — | `cache::evicts_lru` fails | check | Fix | reproduced: `cargo test -p cache evicts_lru` |
| 4 | issue #79 | — | criterion 2: a cancelled trial frees its slot | criterion | Fix | not covered by any test yet |
```

## Classifying a comment

Name what the comment is, with the Conventional Comments vocabulary, even when the reviewer did
not label it:

- **issue** — a defect: wrong behavior, a missing case, a broken contract. Blocking by default.
- **suggestion** / **polish** — a better way; blocking only if the reviewer says so.
- **nitpick** / **quibble** / **typo** — small and preference-based; fix it when it costs little.
- **question** — the reviewer wants to understand or to check a concern.
- **todo** / **chore** — a small, necessary task before merge.
- **praise** / **thought** / **note** — nothing to do; a short thanks where it fits.

A comment marked *(non-blocking)* or *(if-minor)* can be deferred without disagreeing.

## Deciding

Before deciding, open the code the item points to at the current `HEAD`, not the line it was left
on: an `isOutdated` thread moved with the code, and its point may still hold.

- **Fix** — valid and inside the scope. When the reviewer misread the code, fixing means making
  the code say it (a name, a type, a smaller function); a reply explaining the code leaves the
  next reader with the same confusion. Add a code comment only for what the code cannot say.
- **Already done** — a commit already addressed it: find that commit and verify it really does.
- **Answer** — a question with a factual answer; give the fact and its source.
- **Ask back** — you cannot tell what is wanted; ask one precise question, offering the two
  readings you see.
- **Defer** — valid, but it would grow the pull request beyond its purpose; propose a follow-up
  issue and say so in the reply.
- **Disagree** — the change would make the code wrong or worse. It needs a source (the
  documentation of the installed version, a test, a measurement, a precedent in the code), the
  trade-off in one sentence, and an opening: ask whether the reviewer sees a cost you missed. Never
  a flat "no".

## Checks

For each failing check, read the failed steps' log and decide whose failure it is before fixing:

1. **Caused by this pull request** — the failure touches code the pull request changed, or does not
   happen on the base branch. Reproduce it locally with the job's command, fix it, keep the test.
2. **Already failing on the base** — the same check fails on the latest base commit (`gh run list
   --branch <base> --workflow <name> -L 3`). Not this pull request's defect: say so at the plan
   gate; fixing it here grows the scope.
3. **Flaky or infrastructure** — a timeout, a network error, a runner problem, or a test that
   passes when run again locally. Re-running the job (`gh run rerun <run> --failed`) acts on GitHub:
   ask before doing it, and report the flake.

A check is never fixed by skipping, disabling, or loosening it.

## Conflicts

Merge the base into the branch (`git merge origin/<base>`), so the review history stays intact. For
each conflict, read both sides and the commits that made them (`git log --merge -p <file>`): keep
the base's change and the pull request's intent together. When the two cannot coexist — both
changed the same behavior differently — stop and ask at the plan gate. Run the full checks after
the merge, since a clean textual merge can still break the build.

Rebase only when the repository requires linear history, and push it with
`--force-with-lease --force-if-includes` after the user's yes: `--force-with-lease` refuses the push
if someone pushed to the branch since your last fetch, and `--force-if-includes` refuses it if that
push was fetched in the background but not integrated.

## The issues the pull request closes

Each issue in "Issues this pull request closes" is part of the contract: read its acceptance
criteria and check that the pull request meets every one, with the criteria table of the
resolve-issues skill (`references/verification.md`). A criterion the pull request does not meet is
an item of the table, like a review comment.
