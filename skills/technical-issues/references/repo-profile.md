# Repository profile — the issue rules a repository already has

Some repositories write down how an issue must look: the title format, the labels every issue
carries, a milestone per release, a parent for every story, the sections of the body, and where
effort and priority live. An issue that ignores those rules is moved, relabeled, or rewritten by
hand — or flagged by the repository's own checks. The profile captures those rules once, so the
drafts follow them and `validate_issues.py` enforces them.

The profile changes the **shape** (title, labels, sections, fields). It never relaxes the
**evidence**: `file:line`, the base commit, falsifiable acceptance criteria, `[Fn]`, and the
not-verified field stay, placed inside the repository's sections.

## Contents

- Where to look
- Deciding whether there is a profile
- Schema
- Mapping an issue form
- Example

## Where to look

Read, in this order, and note what each source says:

1. **Written rules:** `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING*`, `docs/**/issues*.md`,
   `.github/copilot-instructions.md`. Look for: hierarchy (epic, story, task), required labels,
   milestones, parent, title format, Definition of Done, and where Priority, Effort, Status, or
   severity are kept (body, label, or Project field).
2. **Issue forms and templates:** `.github/ISSUE_TEMPLATE/*.yml` and `*.md`, plus `config.yml`
   (`blank_issues_enabled`, `contact_links` — a security contact link is a security policy).
3. **Recent issues**, the ground truth for what reviewers accept:

   ```bash
   gh issue list --state all -L 10 --json number,title,labels,milestone,body
   ```

   Note the heading level the bodies use (a form renders its fields as `###`, but people often
   write `##`), the title pattern, and the labels present on every issue.
4. **What exists:** `gh label list`, `gh api repos/{owner}/{repo}/milestones`, and the issue types
   (`gh issue create --type` needs one that exists; organizations define them).

## Deciding whether there is a profile

- A written rule exists → profile, with every rule traced to it.
- No written rule, but the 10 recent issues agree (same title pattern, same label families,
  same sections) → profile from the pattern; say so in the preview.
- Neither → no profile; the default anatomy in `issue-anatomy.md` applies.
- A written rule and the recent issues disagree → **ask the user**. Do not blend them.

## Schema

`profile.json` lives in the drafts directory and the manifest names it (`"profile":
"profile.json"`). Every key is optional except `sources`; an unknown key is an error, so a typo
does not silently disable a rule.

| Key | Type | Meaning |
|---|---|---|
| `sources` | list of strings | Where each rule came from (`AGENTS.md section 10`, `fix.yml`, `recent issues`). Required. |
| `title_pattern` | regex | Every title must match (e.g. `^(feat\|fix\|chore): .+$`). |
| `epic_label` | string | The label that marks an epic. |
| `epic_title_pattern` | regex | Replaces `title_pattern` for issues that carry `epic_label`. |
| `title_max` | integer | Replaces the default 100-character limit. |
| `labels` | list of `{pattern, min, max}` | How many labels must match each regex (`^type:` exactly 1, `^area:` at least 1). |
| `require_milestone` | boolean | Every issue names a `milestone` in the manifest. |
| `require_parent` | boolean | Every issue without `epic_label` has a `parent` (manifest epic or `#N`). |
| `heading_level` | 2 or 3 | The level of the section headings. |
| `sections` | `{kind: [names]}` | Section headings each kind must have, in the repository's words. |
| `required_text` | `{kind: [strings]}` | Text that must appear verbatim — the default lines of a form field. |
| `forbidden_fields` | list of strings | Field labels that must not appear in the body (e.g. `**Effort:**` when effort lives in a Project). |
| `post_create` | list of strings | Manual steps after publishing; shown in the preview and the final report. |

`sections` and `required_text` are keyed by the manifest `kind` (`epic`, `finding`, `task`). The
manifest's `epic` is the issue that groups the others in this run: when the repository's hierarchy
makes that a story under an existing epic, write the story's sections under `epic`.

## Mapping an issue form

`gh issue create --body-file` does not fill a form; it posts free Markdown. Reproduce the form so
the issue reads as if it came from the web UI:

| Form element | Goes to |
|---|---|
| `title: "fix: "` | `title_pattern` (and the drafts' titles start with it) |
| `labels: [...]` | the manifest `labels` of the issues of that type |
| each `textarea`/`input` `label` | a heading in `sections`, at `heading_level`, in the form's order |
| `validations: required: true` | that heading is listed in `sections` |
| `value:` (default text) | `required_text` when it is a rule (a Definition of Done line), otherwise a starting point |
| `type: markdown` with instructions ("after filing, set…") | `post_create` |

Put the skill's labels inside the matching sections: evidence, mechanism, and reproduction under
the context or description heading; fix and acceptance criteria under scope or the steps to fix;
dependencies under a `Depends on` heading (`Depende de` in pt-BR) or, when the form names that
section differently, in a `**Depends on:**` field inside it — the validator reads only those two.

## Example

`examples/repo-rules-to-issues/profile.json` — a repository whose `AGENTS.md` asks for one `type:`
label and at least one `area:` label, a milestone and a parent on every issue, `##` sections from
the `fix` form, the form's Definition of Done line, and Priority and Effort only in the Project.
