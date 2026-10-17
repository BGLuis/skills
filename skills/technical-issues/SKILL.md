---
name: technical-issues
description: Turns a technical analysis or audit of a codebase into GitHub issues instead of a report file — one issue, or an epic with sub-issues — each anchored in file:line evidence, grounded in the official docs of the installed version, and closed by a falsifiable acceptance criterion. Investigates with the method of the technical-report skill, writes drafts, validates them, checks for duplicates, shows a preview, and only creates the issues after the user confirms. Use when the user asks to open, create, or file issues for a feature, a plan, a refactor, an audit, a performance or accessibility problem, or to break a piece of work down into GitHub issues or sub-issues. Do NOT use for a report file in docs/reports/ (that is technical-report), for triaging, labeling, or closing existing issues, for Pull Requests, for issue trackers other than GitHub (GitLab, Jira, Linear), or for issue and PR templates of a repository (that is github-repo-setup).
---

# Technical Issues

Same investigation as a technical report, different delivery: the result becomes GitHub issues
someone can pick up and close. An issue is only worth opening if whoever takes it can reproduce
the problem, find the code, and know when it is done — without reading anything else — and if it
lands where the repository's own rules expect it.

This skill **depends on the technical-report skill**. Load it and follow its rules for research,
evidence, `[modeled]`, `[Fn]` citations, measurement, and labels per language. If it is not
installed or cannot be loaded, stop and tell the user: without it the issues lose their grounding.

## 0. Preconditions

1. The project is a git repository with a GitHub remote, and `gh auth status` succeeds (or a
   GitHub MCP server is available). Read `gh --version`: `publish_issues.py` needs `gh` ≥ 2.94.0
   for `--parent` (`references/github-publishing.md`).
2. Read the visibility with `gh repo view --json visibility` and the security policy
   (`SECURITY.md`, `.github/SECURITY.md`, or `docs/SECURITY.md`). Both decide where a security
   finding goes (step 5).
3. If any of this is missing, say so and offer to produce only the validated drafts, for the user
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

## 2. Read the repository's issue rules

Follow `references/repo-profile.md`: read the written rules about issues (`AGENTS.md`,
`CONTRIBUTING*`, the issue forms), the 10 most recent issues, and the labels, milestones, and
issue types that exist. When the repository states rules — title format, required labels,
milestone, parent, sections, where effort and priority live — write them to `profile.json` in the
drafts directory, each one traced to its source. The profile wins over this skill's default shape;
the evidence rules of step 3 never give way.

With no written rule and no consistent pattern in the recent issues, there is no profile: use the
default anatomy. When two sources contradict each other, ask the user which one holds.

## 3. Detect the mode

| Mode | When | Issues produced |
|---|---|---|
| **A — Proposal** | Work not done yet: a feature, a plan, a migration | One issue per task or plan step |
| **B — Audit** | Defects in existing code | One issue per prioritized backlog item |

Post-implementation work (technical-report mode C) does not produce issues — the work is done. Only
if the user asks, its "what was not verified" items become follow-up issues in mode A form.

If the request fits both modes, **ask the user which one**.

## 4. Investigate

Follow the technical-report skill for the detected mode: its `research.md` steps at the depth of
the mode, real `file:line` evidence opened in this session, zero-result searches for absences, the
measurement protocol for any number. Do not write a single draft before the evidence exists.

When the user points to a report that already exists (`docs/reports/*.md`), reuse its findings and
sources, but reopen every cited `file:line` at the current commit: a line that moved is updated,
and a finding whose code changed is checked again or left out, and the user is told which.

## 5. Triage security findings

A finding that an attacker could exploit — injection, an authorization bypass, an exposed secret, a
vulnerable dependency in use — is a security finding.

- **Public repository:** it is **never** an issue. Leave it out of the manifest, tell the user,
  and point to the channel in the security policy (private vulnerability reporting, a security
  advisory, an email). With no policy, recommend a private advisory and create nothing.
- **Private or internal repository:** it can be an issue only after the user says yes in the
  preview; mark it `"security": true` in the manifest, and keep exploit payloads out of the body.

The validator and the publisher both refuse a security issue on a public repository.

## 6. Decide the granularity

- **One issue** when the result is a single actionable item.
- **An epic with sub-issues** otherwise: one sub-issue per task (A) or per backlog item (B).
  Coupled findings that must be fixed together (`P-01 + P-02`) are **one** sub-issue, and its body
  says why. One level of nesting inside the manifest.
- **Under an existing issue** when the repository's hierarchy asks for it (an epic of the current
  milestone, a story being split): `"parent": "#98"` on the issue, or on the manifest epic.

Each sub-issue must be closable on its own by one person in one Pull Request. If it is not, split
it; if two sub-issues always ship together, merge them. When one must land before another, record
it in `blocked_by` and mirror it under Depends on.

## 7. Write and validate the drafts

Write the drafts in a temporary directory **outside the repository** (never commit them): one
Markdown body per issue plus `manifest.json`, and `profile.json` when step 2 produced one, in the
format of `references/issue-anatomy.md`.

Run the validator that ships with this skill (path relative to the skill directory):

```bash
python3 <skill-directory>/scripts/validate_issues.py <drafts-dir>
```

Fix every error and run it again until it exits clean; read the warnings and fix the ones that
apply. Without Python, check the same rules by hand from `references/issue-anatomy.md` and say so
to the user.

Full examples of the expected drafts, in `examples/`:

- `audit-to-issues/` — mode B, a new epic with two sub-issues, one blocked by the other;
- `proposal-to-issues-pt-br/` — mode A in Brazilian Portuguese, tasks with a dependency;
- `repo-rules-to-issues/` — a repository with written issue rules: a profile, findings under an
  existing epic, sections and labels from the issue form.

## 8. Check duplicates and labels

Follow `references/github-publishing.md`: search open and closed issues for each draft, and read
the repository's existing labels and milestones. A probable duplicate is **not** created — it is
shown to the user with its link. Labels that do not exist are proposed, never created without a
yes.

## 9. Preview and confirm

Creating issues is visible to everyone watching the repository and cannot be fully undone. Run
`publish_issues.py <drafts-dir> --dry-run` and show the user, in one message: the target repository
and its visibility, each title with its labels, milestone, parent, and blockers, the probable
duplicates skipped, the labels to be created, the security findings routed elsewhere, and the
manual steps the profile lists in `post_create`. **Create nothing until the user confirms.** If the
user edits the list, update the drafts and validate again.

## 10. Publish

```bash
python3 <skill-directory>/scripts/publish_issues.py <drafts-dir>
```

It creates the issues in manifest order, writes each number into `manifest.json` as soon as it
exists, turns every key into `#N`, creates the native blocked-by links, and reads everything back.
If it fails halfway, fix the cause and run the same command again: the issues that already have a
number are skipped. Never create the issues by hand after a partial run — that duplicates them.

## 11. Report to the user

In the language of the conversation:

- the URL of every issue created, with the hierarchy and the blocked-by links;
- duplicates skipped, labels created or proposed, and security findings routed elsewhere;
- the issue language and the profile, with where each choice came from, and the validator and
  read-back results;
- the manual steps still to do (`post_create`);
- **what was not verified** — the claims left `[modeled]`, the sources that could not be consulted,
  the measurements still pending — explicitly, without softening.
