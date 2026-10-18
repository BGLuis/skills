---
name: resolve-issues
description: Resolves GitHub issues end to end — one issue, several, or an epic with its sub-issues. Reads each issue with its comments, parent, sub-issues, blockers, and closing pull requests; groups the work by root cause; researches with the technical-report method (code precedents, installed version, docs via Context7 or the official site, changelog, web search only as a lead); turns the acceptance criteria into checks before coding; implements the minimum change; verifies every criterion; and commits locally, one branch per work unit and one commit per issue, without pushing. Use when the user asks to resolve, fix, implement, work on, or close an issue or a list of issues, or to plan an issue's implementation. Do NOT use to create or file issues (that is technical-issues), to write a report file (technical-report), to triage or close issues without code, to fix the review comments, CI, or conflicts of an open pull request (resolve-pull-requests), or for trackers other than GitHub.
---

# Resolve Issues

An issue is resolved when every acceptance criterion holds and was checked in this session, the
change follows what the installed version of each dependency documents, and the work sits in
local commits the user can review before anything leaves the machine. Nothing here is pushed,
opened, or commented on GitHub unless the user asks for it.

This skill **depends on the technical-report skill** for its research method
(`references/research.md` there) and its measurement protocol
(`references/performance-measurement.md`). Load them. If that skill is not installed, follow
`references/research-sources.md` here alone and tell the user the research is lighter.

## 0. Preconditions

1. The project is a git repository with a GitHub remote, and `gh auth status` succeeds.
2. No tracked file has uncommitted changes (`git status --porcelain --untracked-files=no` prints
   nothing). If one has, stop and ask: never stash, reset, or commit the user's changes to make
   room. Untracked files are left alone and never committed: stage files by path, never with
   `git add -A`.
3. `git fetch` the default branch, so every branch starts from its latest commit.

## 1. Read the repository's rules

Before reading the issue, read how the repository wants work delivered: `AGENTS.md`, `CLAUDE.md`,
`GEMINI.md`, `CONTRIBUTING*`, `.github/pull_request_template.md`, and the CI workflows. Note:

- the branch name pattern, the commit title format, and the closing keywords (`Closes #N` for the
  issue a commit finishes, `Refs #N` for a parent — some repositories reserve `Closes` for the
  last commit of the branch);
- the commands that must pass (lint, type check, tests, a `just check` or `make check`), taken
  from the docs and from what CI runs;
- gates before work starts (an analysis appended to the issue, a status in a Project).

The repository's rules replace the defaults of this skill. When they say nothing, use the defaults
in `references/work-units.md`.

## 2. Read the issues

Run the script that ships with this skill (path relative to the skill directory), with every issue
the user named:

```bash
python3 <skill-directory>/scripts/issue_context.py <N> [<N> ...] [-R owner/repo]
```

It prints, per issue, the body, the comments, the parent, the blockers, the pull requests that
close it, the sub-issues in the order they can be worked, and the **Flags**. Read all of it — the
comments often change the scope. Then:

- **A flag is a stop.** A closed issue, an open blocker, an open pull request that already closes
  the issue, or a blocked-by cycle: tell the user what the flag says and ask before going on.
- **Re-read the issue against the code.** Open every `file:line` it cites at `HEAD`. A line that
  moved is followed to where it went; code that changed since the issue's base commit is read
  again. If the defect no longer reproduces or the feature already exists, report it with the
  evidence and write no code.
- **Look for related open issues.** Search open issues by the symbols, files, and symptom of each
  issue (`gh issue list --state open --search "<terms>"`). Record each hit as *same root cause*,
  *same area, different cause*, or *unrelated*.

## 3. Define the work units

Follow `references/work-units.md`:

| What the user gave | Branches | Commits |
|---|---|---|
| One issue | One | One per logical change, the last one closing the issue |
| An epic or a story with sub-issues | One for the whole tree | One per sub-issue, in the work order the script printed |
| Issues with the same root cause (given or found in step 2) | One | One fixing the cause, closing all of them |
| Unrelated issues | One per issue | Each as "one issue" above |

Related issues found in step 2 join a unit only when they share the root cause; the others are
listed in the final report. When there are several independent units and the environment can run
agents in parallel, give each unit to its own agent in its own `git worktree`, as
`references/work-units.md` describes; otherwise work them one after another. Two units that touch
the same files never run in parallel.

## 4. Research each decision

Follow the technical-report research method at the depth of its mode A, for each decision the
change makes — which API, which pattern, which configuration — with the sources in this order
(`references/research-sources.md`):

1. **The repository:** internal precedents to reuse, with `file:line`; the installed versions from
   the lockfile.
2. **Context7** for the documentation of the installed version (the find-docs skill, when
   installed).
3. **The official site and the changelog** of that version: the feature's page, the documented
   limits, the release notes and the migration guide when the installed version is not the
   latest.
4. **Web search**, only as a lead to a source of levels 1 to 3. It never supports a decision on its
   own.

Check the issue's own proposal against these sources: an issue can be wrong or written for another
version. When the documentation contradicts the issue, the documentation wins, and the divergence
goes to the plan gate (step 6). Behavior not checked in this session is `[modeled]`, never stated
as fact.

## 5. Turn the acceptance criteria into checks

Before writing code, list every acceptance criterion and Definition of Done item of each issue and
pair it with the check that proves it: a test to write, a command to run, a measurement with its
protocol. Follow `references/verification.md`:

- **A bug is reproduced first.** Write the test or the command that shows the defect, run it, and
  see it fail for the reason the issue gives. A fix without a failing reproduction proves nothing.
- **A vague or missing criterion is derived** with the rules in `references/verification.md`: a
  named check, a threshold with a baseline, no vague term. A derived criterion is shown at the
  plan gate.
- **Every scope item has a criterion.** A step of the issue with no criterion gets one, or is
  left out and said so.

## 6. Plan gate

Stop and show the plan — work units, the decision per step with its source, and the criteria with
their checks — and **wait for the user's answer** when any of these holds:

- the user asked for a plan only;
- a criterion was missing or vague and you derived it, or the issue has unanswered open questions;
- the issue's proposal contradicts the code or the documentation (⚠️ with both sources);
- the change is destructive or one-way: a migration that drops or rewrites data, a deletion, a
  public API or file format change, a new dependency;
- the work spans more than one module, or the issue's estimate is large (by the repository's own
  scale, or more than about a day of work);
- the grouping of step 3 depends on a judgment the user may not share.

Otherwise state the plan in one short message and continue without waiting.

## 7. Implement

On the unit's branch (`references/work-units.md`, Branches), make the minimum change that meets
the criteria: reuse the precedents of step 4, follow the repository's conventions, touch nothing
the issue does not need. Anything worth doing that the issue does not ask for goes to the
follow-ups of the final report — offer to file them with the technical-issues skill.

## 8. Verify

Run every check of step 5 and the repository's full set of commands from step 1. A criterion is
met only when its check ran in this session and passed; a check that could not run (no device, no
credentials, no production data) makes that criterion **not verified**, never met. Performance
criteria follow the technical-report measurement protocol, before and after, same conditions.

If a check fails, fix and run it again. If it cannot pass without leaving the issue's scope, stop
and tell the user.

## 9. Commit

Commit on the unit's branch with the format of step 1, or the defaults in
`references/work-units.md`: one commit per issue (per sub-issue in an epic, in work order), each
titled `type(scope): subject (#N)`, its body saying why, and the closing keyword the repository
uses. Never commit scratch files, logs, or drafts. **Do not push, open a pull request, or comment
on the issue** unless the user asks.

## 10. Report to the user

In the language of the conversation, per work unit, following `references/verification.md`
(Report):

- the branch, its worktree path when there is one, and its commits;
- each criterion with the check that ran and its result: ✅ met, ❌ failed, or not verified, with why;
- the sources consulted with their version, and each divergence between the issue and the docs;
- related issues found and not handled, and the follow-ups;
- what is left for the user: the review, the push, the pull request.
