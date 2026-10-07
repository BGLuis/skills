---
name: technical-issues
description: Turns a technical analysis or audit of a codebase into GitHub issues instead of a report file — one issue, or an epic with sub-issues — each anchored in file:line evidence, grounded in the official docs of the installed version, and closed by a falsifiable acceptance criterion. Investigates with the method of the technical-report skill, writes drafts, validates them, checks for duplicates, shows a preview, and only creates the issues after the user confirms. Use when the user asks to open, create, or file issues for a feature, a plan, a refactor, an audit, a performance or accessibility problem, or to break a piece of work down into GitHub issues or sub-issues. Do NOT use for a report file in docs/reports/ (that is technical-report), for triaging, labeling, or closing existing issues, for Pull Requests, for issue trackers other than GitHub (GitLab, Jira, Linear), or for issue and PR templates of a repository (that is github-repo-setup).
---

# Technical Issues

Same investigation as a technical report, different delivery: the result becomes GitHub issues
someone can pick up and close. An issue is only worth opening if whoever takes it can reproduce
the problem, find the code, and know when it is done — without reading anything else.

This skill **depends on the technical-report skill**. Load it and follow its rules for research,
evidence, `[modeled]`, `[Fn]` citations, measurement, and labels per language. If it is not
installed or cannot be loaded, stop and tell the user: without it the issues lose their grounding.

## 0. Preconditions

1. The project is a git repository with a GitHub remote, and `gh auth status` succeeds (or a
   GitHub MCP server is available). Read `gh --version`: native sub-issue flags need
   `gh` ≥ 2.94.0 (`references/github-publishing.md`).
2. If any of this is missing, say so and offer to produce only the validated drafts, for the user
   to create by hand. Never fall back to another tracker.

## 1. Choose the issue language

First match wins:

1. the language the user asked for explicitly;
2. a written rule in the repository — `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`,
   `.github/copilot-instructions.md`, `CONTRIBUTING*`, `.github/ISSUE_TEMPLATE/*` — about the
   language of issues or documentation;
3. the language of the most recent issues in the repository (`gh issue list --state all -L 10`).

With no signal, or with signals that conflict, **ask the user** before writing. Labels and
typography come from the technical-report's `references/locales.md` and from
`references/issue-anatomy.md` here.

## 2. Detect the mode

| Mode | When | Issues produced |
|---|---|---|
| **A — Proposal** | Work not done yet: a feature, a plan, a migration | One issue per task or plan step |
| **B — Audit** | Defects in existing code | One issue per prioritized backlog item |

Post-implementation work (technical-report mode C) does not produce issues — the work is done. Only
if the user asks, its "what was not verified" items become follow-up issues in mode A form.

If the request fits both modes, **ask the user which one**.

## 3. Investigate

Follow the technical-report skill for the detected mode: its `research.md` steps at the depth of
the mode, real `file:line` evidence opened in this session, zero-result searches for absences, the
measurement protocol for any number. Do not write a single draft before the evidence exists.

## 4. Decide the granularity

- **One issue** when the result is a single actionable item.
- **An epic with sub-issues** otherwise: one sub-issue per task (A) or per backlog item (B).
  Coupled findings that must be fixed together (`P-01 + P-02`) are **one** sub-issue, and its body
  says why. One level of nesting only.

Each sub-issue must be closable on its own by one person in one Pull Request. If it is not, split
it; if two sub-issues always ship together, merge them.

## 5. Write and validate the drafts

Write the drafts in a temporary directory **outside the repository** (never commit them): one
Markdown body per issue plus `manifest.json`, in the format of `references/issue-anatomy.md`. If the
repository has `.github/ISSUE_TEMPLATE/`, follow the template that fits (bug, feature) inside that
anatomy — see `references/issue-anatomy.md`.

Run the validator that ships with this skill (path relative to the skill directory):

```bash
python3 <skill-directory>/scripts/validate_issues.py <drafts-dir>
```

Fix every error and run it again until it exits clean. Without Python, check the same rules by
hand from `references/issue-anatomy.md` and say so to the user.

Full example of the expected drafts: `examples/audit-to-issues/` (mode B, an epic with two
sub-issues).

## 6. Check duplicates and labels

Follow `references/github-publishing.md`: search open and closed issues for each draft, and read
the repository's existing labels. A probable duplicate is **not** created — it is shown to the user
with its link. Labels that do not exist are proposed, never created without a yes.

## 7. Preview and confirm

Creating issues is visible to everyone watching the repository and cannot be fully undone. Show the
user, in one message: the target repository, each title with its labels and parent, the probable
duplicates skipped, and the labels to be created. **Create nothing until the user confirms.** If
the user edits the list, update the drafts and validate again.

## 8. Publish

Follow `references/github-publishing.md`: the epic first, then the sub-issues linked to it, then
the epic's table updated with the real issue numbers. If a command fails halfway, stop, list what
was created, and check before retrying — a blind retry creates duplicates.

## 9. Report to the user

In the language of the conversation:

- the URL of every issue created, with the hierarchy;
- duplicates skipped and labels created or proposed;
- the issue language and where that choice came from, and the validator result;
- **what was not verified** — the claims left `[modeled]`, the sources that could not be consulted,
  the measurements still pending — explicitly, without softening.
