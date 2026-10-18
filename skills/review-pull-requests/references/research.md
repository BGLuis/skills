# Research — checking the change against its dependencies and their documentation

A pull request can be well written and still wrong for the project: it calls an API its own
library deprecated, pins a version that was yanked or has a known vulnerability, adds a library a
breaking release behind, or uses a feature against what the documentation of the installed version
says. None of that shows in the diff; each is found only by looking it up. The method is the
technical-report skill's (`references/research.md` there); this file fixes what a review must look
up and how far to go.

## Contents

- Sources, in order
- The four mandatory checks
- Budget
- Recording it in the review

## Sources, in order

1. **The repository**: the lockfile for the installed version of every dependency the change
   touches; the precedents — how the rest of the code already uses the same library.
2. **Context7** for the documentation of that version (the find-docs skill, when installed).
3. **The official site, the changelog, and the release notes** of that version and of every
   version between it and the latest.
4. **The registry and OSV**, through `scripts/dependency_diff.py`, for versions, yanked and
   deprecated releases, and advisories.
5. **Web search**, only as a lead to a source of levels 1 to 4 — a migration guide, a maintainer's
   issue about the API. A blog post never supports a finding on its own.

The model's memory is never a source: an API's behavior or deprecation not checked in this session
is not a finding, or is labeled `question` with what you could not confirm.

## The four mandatory checks

Run all four on every review that touches code; say in the summary which were done.

### 1. Dependency versions

```bash
python3 <skill-directory>/scripts/dependency_diff.py --repo <worktree> \
  --base origin/<base> --head HEAD
```

It reads the lockfiles of base and head and prints each package added, upgraded, downgraded, or
removed, with the latest release, whether this version is yanked or deprecated, and the OSV
advisories against it. For each flag, decide:

- **An advisory** on a version the change adds or keeps: read it — does the vulnerable code path
  apply to how the project uses the package? Applicable → `issue (blocking)`, with the advisory id
  and the fixed version. In a public repository, a vulnerability the pull request *introduces* is
  still a normal review point (the advisory is public); one you discover in the project's own code
  is not (`references/safety.md`).
- **Yanked or deprecated**: `issue (blocking)` unless the change has a stated reason.
- **Added a breaking release behind the latest**: `question` — is something pinning it? If not,
  `suggestion` to take the current release, with what changed between them.
- **Downgraded**: `question`, always — a downgrade is rarely deliberate.
- **A lockfile it could not parse, or a manifest changed with no lockfile change**: read them by
  hand; a dependency added to a manifest without the lockfile means CI resolves a version nobody
  reviewed.

### 2. Deprecated APIs

For every API of a dependency that the change calls for the first time, or calls in a new way:

- read its entry in the documentation of the **installed** version, and the changelog up to the
  latest release: is it deprecated, slated for removal, or replaced?
- build the branch and read the warnings: a compiler or runtime deprecation warning on a changed
  line is direct evidence (`cargo build`, `tsc`, `python -W error::DeprecationWarning`, `go vet`).

A deprecated call in the installed version → `issue` (the replacement exists today). Deprecated
only in a newer version → `suggestion`, noting the version, so the code is ready for the upgrade.

### 3. Use against the documentation

For each library feature the change relies on, compare the code with the documented contract of
the installed version: required call order, thread-safety, cancellation and cleanup, error and
timeout behavior, documented limits (sizes, rates, concurrency), the configuration's defaults. A
mismatch is an `issue` that quotes or links the documentation; a recommended practice the code
skips is a `suggestion`.

### 4. The project's own versions and conventions

The repository pins its own toolchain and dependency rules (`rust-toolchain.toml`, `.nvmrc`,
`engines`, `[workspace.dependencies]`, Renovate or Dependabot configs, an ADR on dependencies). A
change that uses a language feature newer than the pinned toolchain, declares a dependency outside
the place the project declares them, or bypasses its pinning policy breaks the project's rules —
`issue`, citing the rule.

## Budget

Stop when every finding and every "checked" line in the summary has a level 1 to 4 basis. As a
guide, per library the change touches: its lockfile entry, 1 to 3 documentation pages, the
changelog between the installed and the latest version. A source you could not reach (no network,
a private registry) is named in the summary, and what depended on it is not claimed.

## Recording it in the review

- A finding that rests on a source links it inline, with the version: "deprecated since 0.24
  ([changelog](…))".
- The summary has a **Dependencies** line: what `dependency_diff.py` found (or "no dependency
  changed"), and which of checks 2 to 4 were done.
