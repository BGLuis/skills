# Publishing to GitHub — duplicates, labels, hierarchy

Every command below runs from the repository root, so `gh` targets its GitHub remote; add
`-R owner/repo` when the manifest's `repo` differs. Commands checked against `gh` 2.102.0 and the
GitHub REST docs for sub-issues and issue dependencies (consulted 2026-10-17).

## Contents

- 1. Duplicates
- 2. Labels, milestones, and issue types
- 3. Security findings
- 4. Publish with the script
- 5. When something fails halfway
- 6. Without the script

## 1. Duplicates

For each draft, search open **and** closed issues with two or three distinctive terms — the symbol,
the file, the symptom — not the whole title:

```bash
gh issue list --state all --search "detectChanges scroll in:title,body" \
  --json number,title,state,url --limit 10
```

- An open issue about the same defect → probable duplicate: do not create; show it to the user and
  offer to add the new evidence as a comment instead (only after a yes).
- A closed issue about the same defect → it regressed or was closed without a fix: create, and
  link it in the body (`Regression of #123` / the translated sentence).
- Unrelated hits → ignore.

## 2. Labels, milestones, and issue types

```bash
gh label list --json name,description --limit 200
gh api repos/{owner}/{repo}/milestones --jq '.[].title'
```

Map each draft to labels **that already exist**: performance, accessibility, bug, enhancement,
priority or severity labels — whatever names the repository uses, and every family the profile
requires. A label the repository does not have is listed in the preview as "to create" and is
created only after the user says yes:

```bash
gh label create "performance" --description "Speed, memory, or cost" --color 1D76DB
```

Never invent a priority scheme the repository does not use: severity stays in the body, unless the
profile says it lives elsewhere. A milestone or issue type that does not exist makes
`gh issue create` fail: check them here, not halfway through publishing.

## 3. Security findings

On a public repository a security finding is never an issue (SKILL.md step 5). The validator
refuses `"security": true` with `"visibility": "public"`, and the publisher reads the live
visibility before creating anything and stops if it differs from the manifest — a repository made
public since the drafts were written gets its triage again.

## 4. Publish with the script

```bash
python3 <skill-directory>/scripts/publish_issues.py <drafts-dir> --dry-run   # the preview
python3 <skill-directory>/scripts/publish_issues.py <drafts-dir>             # after the yes
```

What it does, in order:

1. Runs the validator and stops on any error. Checks `gh` ≥ 2.94.0 (`--parent`) and the live
   visibility.
2. Creates each issue without a `number`, in manifest order, with `--label`, `--milestone`,
   `--parent`, `--type`, `--project`, and `--assignee` as the manifest says. It writes the new
   number and URL into `manifest.json` right after each one.
3. Replaces every sub-issue key with its `#N` in all bodies (outside code) and edits the bodies
   whose text on GitHub differs.
4. Creates each missing blocked-by link through the REST API. The API wants the blocker's
   database **id**, not its number:

   ```bash
   gh api repos/{owner}/{repo}/issues/141 --jq .id
   gh api -X POST repos/{owner}/{repo}/issues/142/dependencies/blocked_by -F issue_id=<id>
   ```

5. Reads every issue back — title, labels, milestone, parent, blockers — and exits with 1 on any
   mismatch, naming it.

`--project` needs the `project` scope on the `gh` token (`gh auth refresh -s project`).

## 5. When something fails halfway

The script prints what was created and stops. The numbers are already in `manifest.json`, so fix
the cause (a missing label, a network error, a token scope) and run the **same command** again:
issues with a number are skipped, bodies already resolved are left alone, and existing blocked-by
links are not created twice. Never create the remaining issues by hand and never delete the
`number` fields — both duplicate issues on the next run.

## 6. Without the script

Without Python, follow the same order by hand and keep the numbers in a list as you go.

**`gh` older than 2.94.0** — create the sub-issue without `--parent`, then link it through the REST
API. `sub_issue_id` is the issue's **id** (database identifier), not its number:

```bash
child_id=$(gh api repos/{owner}/{repo}/issues/141 --jq .id)
gh api repos/{owner}/{repo}/issues/140/sub_issues -F sub_issue_id="$child_id"
```

`gh api` fills `{owner}` and `{repo}` from the current repository; `-F` sends the id as a number.
The parent and the sub-issue must belong to the same repository owner.

**Sub-issues unavailable** (the API call fails, e.g. on an older GitHub Enterprise Server) — list
the sub-issues as a task list in the epic body, `- [ ] #141`, and tell the user the hierarchy is
not native.

After every issue exists, replace each key with its number in every body (`P-02` → `#141`) and
push each changed body with `gh issue edit <n> --body-file <file>`.
