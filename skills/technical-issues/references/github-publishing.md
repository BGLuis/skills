# Publishing to GitHub — duplicates, labels, hierarchy

Every command below runs from the repository root, so `gh` targets its GitHub remote; add
`-R owner/repo` when the manifest's `repo` differs. Commands checked against `gh` 2.102.0 and the
GitHub REST docs for sub-issues (consulted 2026-10-06).

## Contents

- 1. Duplicates
- 2. Labels
- 3. Create the epic and the sub-issues
- 4. Fallbacks for sub-issues
- 5. Update the epic table
- 6. When something fails halfway

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

## 2. Labels

```bash
gh label list --json name,description --limit 200
```

Map each draft to labels **that already exist**: performance, accessibility, bug, enhancement,
priority or severity labels — whatever names the repository uses. A label the repository does not
have is listed in the preview as "to create" and is created only after the user says yes:

```bash
gh label create "performance" --description "Speed, memory, or cost" --color 1D76DB
```

Never invent a priority scheme the repository does not use: severity stays in the body.

## 3. Create the epic and the sub-issues

The order of `manifest.json` is the creation order. `gh issue create` prints the new issue's URL;
its last path segment is the number.

```bash
gh issue create --title "<epic title>" --body-file epic.md --label performance
# → https://github.com/acme/shop-api/issues/140

gh issue create --title "<sub-issue title>" --body-file p-02.md --label performance --parent 140
```

`--parent` (and `gh issue edit --add-sub-issue`) exist since `gh` 2.94.0. A single issue with no
epic is just the first command.

## 4. Fallbacks for sub-issues

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

## 5. Update the epic table

After every sub-issue exists, replace each key in the epic's table with its number (`P-02` →
`#141`), so the epic links to them, and push the new body:

```bash
gh issue edit 140 --body-file epic.md
```

## 6. When something fails halfway

Stop. List what was created in this run:

```bash
gh issue list --author "@me" --state all --search "created:>=2026-10-06" \
  --json number,title,url
```

Compare with the manifest, tell the user which issues exist and which do not, and continue only
from the first missing one. Never rerun the whole sequence: each rerun duplicates every issue that
had already been created.
