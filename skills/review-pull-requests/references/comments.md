# Writing the review — labels, comments, summary, verdict

A review comment is read by someone who wrote the code and wants it merged. It has to say what is
wrong, why, how sure you are, and how much it matters — so the author can act on it without a
second round of questions.

## Contents

- Labels and weight
- An inline comment
- The summary
- The verdict
- The draft file
- Re-review

## Labels and weight

Every inline comment opens with a Conventional Comments label and, when it is not obvious, its
weight:

| Label | Use for | Weight |
|---|---|---|
| `issue` | A defect: wrong behavior, a broken rule, an unenforced guarantee | blocking unless said otherwise |
| `suggestion` | A better way, with why it is better | non-blocking unless said otherwise |
| `question` | A possible problem you are not sure of, or missing context | non-blocking |
| `nitpick` | Small and preference-based | non-blocking, always |
| `todo` / `chore` | A small necessary task before merge (a changelog line, a doc link) | blocking |
| `praise` | Something done well, specifically | — |

The weight is the real one: an unreachable stale value is a `suggestion`, not an `issue`, even if
it looks wrong. Overstating weight trains the author to ignore the labels.

## An inline comment

```markdown
**issue (blocking): completeness is judged before per-record admission, so a zero-TTL link still leaves a half-cached chain.**

`chain_is_complete` runs here, on the raw message, but `admit_answers` drops zero-TTL RRsets afterwards (`ZeroTtl`). A chain that looks complete can therefore be stored incomplete. Reproduced with a throwaway test against `Admission::evaluate` (qtype A, CNAME with TTL 0): the next hit serves the bare CNAME, the symptom of #77.

Judging completeness on the admitted set instead of the raw message would close it.
```

- **The first line is the whole point**, bold, after the label: a reader skimming the review should
  get every finding from the first lines alone.
- **Then the mechanism**: why it happens, with the code it involves.
- **Then the evidence**: reproduced (how), or found by reading; the rule and its source
  (`AGENTS.md`, ADR 0023, the documentation of the version in use, linked).
- **Then the direction of a fix.** The author owns the fix; propose code only when it is the
  clearest way to say it, as a GitHub suggestion block when it replaces the commented lines.
- **About the code, never the author.** "This lock is held across the await", not "you forgot".

## The summary

```markdown
Thanks for the thorough write-up and for flagging the API break up front. The direction is sound and the tests cover the matching rules well; my comments are mostly about whether the guarantees the PR and ADR 0023 claim are enforced.

**Main points**
- `AdmissionOutcome` has all-`pub` fields, so the "cannot be stored under another key" guarantee holds only for careful callers (inline on `admission_outcome.rs`).
- A response refused for its question is still relayed to the client: worth deciding (serve / SERVFAIL / drop) and recording in the ADR.

**Smaller**
- An un-rate-limited `warn!` with upstream-controlled data; an extra key clone on the hot path.

**Dependencies:** no package version changed (`dependency_diff.py`); the new `tokio::time::timeout` calls checked against the 1.40 docs (not deprecated, cancellation documented as used); toolchain pin respected.

Checked: the layering and error rules of `AGENTS.md`, ADR 0022/0023, every changed line. Ran `cargo test -p styx-resolution` (all pass) and a throwaway probe for a zero-TTL CNAME (reproduces the first point). Not run: `just gate` (rumdl and arch-lint are not installed here).
```

- Open with what is genuinely good, specifically — never generic praise.
- Main points first, smaller ones after, each pointing to its inline comment.
- The **Dependencies** line says what the four research checks found, or which could not run.
- **Checked / Ran / Not run** is mandatory: the author and the maintainer learn what the review
  covers. Never write a blanket claim ("fully coherent with all guidelines").

## The verdict

| Event | When |
|---|---|
| `REQUEST_CHANGES` | At least one blocking finding |
| `APPROVE` | No blocking finding, the change improves the project, and the review covered enough to say so |
| `COMMENT` | Only questions or non-blocking points, or the review could not cover enough to approve (a check that could not run, a part not reviewed) |

GitHub refuses `APPROVE` and `REQUEST_CHANGES` on your own pull request; there only `COMMENT`
exists.

## The draft file

```json
{
  "repo": "owner/name",
  "pr": 117,
  "commit_id": "<the head SHA the review was written on>",
  "event": "REQUEST_CHANGES",
  "body": "<the summary>",
  "comments": [
    {"path": "crates/a/src/outcome.rs", "line": 64, "body": "**issue (blocking): …**\n\n…"},
    {"path": "crates/a/src/outcome.rs", "start_line": 70, "line": 75, "body": "**suggestion (non-blocking): …**"},
    {"path": "crates/a/src/old.rs", "line": 12, "side": "LEFT", "body": "**question:** this removed check…"}
  ]
}
```

`line` is the line number in the file — the new file for `side: RIGHT` (the default), the old one
for `LEFT` on a removed line — and must be inside a hunk of the diff; a range uses `start_line`
in the same hunk. Write `commit_id` from `review_context.py`'s head when you start reviewing.

## Re-review

After the author pushes, the approval summary says how each point was addressed, one line each,
and what stays as a known gap with its tracking issue:

```markdown
All review threads are addressed. `AdmissionOutcome` now has private fields and is consumed by `admit()`, so an outcome cannot be rebound; untrusted replies map to SERVFAIL on both paths; the hot-path clone is gone. The remaining gap (pool health feedback on untrusted replies) is tracked in #118. Checks green; ran the stage integration tests locally.
```
