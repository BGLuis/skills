---
name: resolve-pull-requests
description: Fixes an open GitHub pull request until it is ready to merge — addresses every piece of review feedback (inline threads, inline comments, review summaries, conversation comments), the failing checks, and the merge conflicts, and confirms it still meets the issues it closes. Triages each item against the code and the official docs of the installed version, fixes in new commits on the pull request's branch, verifies locally, and asks before pushing; drafts every reply for the user to approve, and resolves a thread only after CI passes on the fix. Use when the user asks to fix, address, or answer the review comments of a pull request, to fix its CI or its conflicts, or to check whether earlier comments were addressed. Do NOT use to review or critique a pull request (that is review-pull-requests), to open a new pull request, to resolve an issue that has no pull request yet (that is resolve-issues), or for platforms other than GitHub.
---

# Resolve Pull Requests

A pull request is fixed when every piece of feedback has an answer — a commit that addresses it, a
reply that explains why not, or a question back — the checks pass, it merges without conflicts,
and it still does what its issues ask. Reviewers read the answers, so each one has to be true:
"fixed" means the fix is pushed and CI passed on it.

This skill **depends on the technical-report skill** for its research method
(`references/research.md` there). Load it. If it is not installed, follow the source order in step
4 alone and tell the user the research is lighter.

Three actions leave the machine: the push, the replies, and resolving threads. **Each waits for
the user's yes**, given in this session for this pull request.

## 0. Preconditions

1. The project is a git repository with a GitHub remote, and `gh auth status` succeeds.
2. Work in a worktree of your own, so the user's checkout — its branch, its changes, its untracked
   files — is never touched: `git worktree add --detach ../<repo>-pr<N> origin/<base>`, then run
   `gh pr checkout <N>` inside it (it handles forks). Never stash, reset, or commit the user's
   changes, and stage files by path, never with `git add -A`.

## 1. Read the repository's rules

Read `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `CONTRIBUTING*`, the pull request template, and the
CI workflows. Note the commit format, the commands that must pass (and the exact commands each CI
job runs), and how the repository merges: a rule for linear history or "rebase, never merge"
changes step 6. The repository's rules replace this skill's defaults.

## 2. Read the pull request

Run the script that ships with this skill (path relative to the skill directory):

```bash
python3 <skill-directory>/scripts/pr_context.py <PR number or URL> [-R owner/repo]
```

It prints the merge state, the issues the pull request closes, the failing and pending checks with
the command for each log, every unresolved thread with its whole conversation, the inline comments
no thread returned, the review summaries, the conversation comments, what is **new since the last
commit**, and the **Flags**. Then:

- **A closed or merged pull request is a stop.** Ask before touching it.
- **A fork without "Allow edits from maintainers" cannot receive your push.** Say so before fixing
  anything, and offer: ask the author to enable it, or prepare the changes for the author.
- **A pending check is not judged yet.** Wait for it (`gh pr checks <N> --watch`) or come back to
  it after the other items.
- **Someone else's pull request** (an outside contributor): your commits land on their branch. Say
  so in the plan, and keep their code and their intent unless a comment asks otherwise.

Check out the branch in the worktree of step 0 and confirm `HEAD` is the `headRefOid` the script
printed.

- **Your own review comments.** When the open threads are yours (you reviewed someone else's pull
  request), the replies would answer yourself: confirm with the user who should reply, and whether
  to fix the author's branch at all, before drafting anything.

## 3. Triage every item

Build one table with every item: each unresolved thread, each inline comment outside a thread,
each review summary and conversation comment that asks for something, each failing check, the
conflicts, and each issue the pull request closes. Follow `references/triage.md` to classify each
one and decide what to do with it:

| Decision | When |
|---|---|
| **Fix** | The point is valid and inside the pull request's scope |
| **Already done** | A later commit addressed it: name the commit |
| **Answer** | A question, or a misunderstanding that clearer code cannot remove |
| **Ask back** | You cannot tell what the reviewer wants |
| **Defer** | Valid but outside the scope: a follow-up issue |
| **Disagree** | The change would be wrong — with the source that shows it |

Read the code each item points to and check the item against it: a reviewer can be wrong, a
comment can be outdated, and an `isOutdated` thread may still be unaddressed. When the reviewer did
not understand the code, prefer making the code clearer over explaining it in a reply.

## 4. Research what the fixes rely on

For each fix that uses an API, a pattern, or a configuration, and for each disagreement, follow the
technical-report research method with the sources in this order: precedents in the repository,
the installed versions from the lockfile, the documentation of that version through Context7 (the
find-docs skill when installed), the official site and the changelog, and web search only as a
lead to one of those. A disagreement without a source is an opinion: find the source or fix it the
reviewer's way.

## 5. Plan gate

Show the triage table and **wait for the user's answer** when any item is *Disagree*, *Defer*, or
*Ask back*; when a fix goes beyond the pull request's scope or changes a public API, a data format,
or a dependency; when a conflict needs a choice between two behaviors; or when a failing check is
not caused by this pull request (`references/triage.md`, Checks). Otherwise state the plan in one
short message and continue.

## 6. Fix

- **New commits, no rewriting.** Add commits on top of the branch; do not amend, squash, or rebase.
  Rewriting the history breaks the reviewers' "changes since your last review" and moves their
  comments. One commit per item or per group of items that are the same change, in the format of
  step 1, each saying which feedback it addresses.
- **Conflicts:** `git fetch` and `git merge origin/<base>` into the branch. Resolve each conflict by
  reading what both sides meant, never by picking a side wholesale, and run the full checks after.
  Only when the repository requires linear history: rebase, and push later with
  `--force-with-lease --force-if-includes`, after the user's yes.
- **Failing checks:** read the log (`gh run view <run> --log-failed`), reproduce the failure locally
  with the command the job runs, then fix the cause. Never skip, disable, or loosen a test, a lint
  rule, or a check to make it pass.
- Touch nothing no item asks for; anything else worth doing is a follow-up.

## 7. Verify

Run the repository's full set of commands from step 1, the reproduction of each failing check, and
the acceptance criteria of each issue the pull request closes (the resolve-issues skill's
`references/verification.md` describes the criteria table). An item is fixed only when its check
ran in this session and passed. A command that cannot run here (a pinned tool not installed,
no credentials) is run piece by piece where possible, and what still did not run is reported as not
verified — CI will run it after the push, which is why threads are resolved only after CI.

## 8. Push — after the user's yes

Show the commits, each with the items it addresses, and the verification results. **Ask before
pushing.** On a yes, `git push origin HEAD:<headRefName>` — the local branch name may differ from the
pull request's — or, after a rebase the user approved, the same with
`--force-with-lease --force-if-includes`. Then watch the checks: `gh pr checks <N> --watch`.

## 9. Replies — drafted here, posted after the user's yes

Draft one reply per item with `references/replies.md`: in the reviewer's language, short, with the
commit that addresses it as a bare SHA. Show all the drafts in one message. **Post only after the
user approves them**, editing what the user changes.

## 10. Resolve threads — after CI passes

When the checks of the pushed commit pass, resolve each thread whose item was **Fixed** or
**Already done** and verified, with the reason `ADDRESSED` (`references/replies.md`, Resolving).
Leave open every thread that was *Disagree*, *Ask back*, or *Defer*, and every thread you cannot
resolve (`viewerCanResolve` is false); the reply says why it stays open. If CI fails, go back to
step 6 and resolve nothing.

## 11. Report to the user

In the language of the conversation: the triage table with each item's outcome; the commits and
whether they were pushed; the checks after the push; the replies posted and the threads resolved
or left open, with why; follow-ups, offered to the technical-issues skill; and what is left — a new
review request (offer it, do not send it unasked), items waiting for the reviewer, anything not
verified.
