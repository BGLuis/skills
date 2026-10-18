# Safety — reviewing code you did not write

Reviewing a pull request means checking out code from someone else and, usually, running it.
Building, testing, and installing all execute code the branch controls: a build script, a test
fixture, a `postinstall` hook, a git hook, a dependency it pins. GitHub's guidance on
`pull_request_target` names the same chain for CI — a checkout of the head is harmless, the next
step that builds or tests it runs the attacker's commands — and it applies on your machine too.

## Contents

- Who is trusted
- What executes
- Before running anything
- While running
- What to report

## Who is trusted

`review_context.py` prints the author's association with the repository. `OWNER`, `MEMBER`, and
`COLLABORATOR` already have write access: their branch can run on your machine the way `main`
can. `CONTRIBUTOR`, `FIRST_TIME_CONTRIBUTOR`, `FIRST_TIMER`, and `NONE` do not — their changes to
files that execute are read before anything runs.

## What executes

The script marks these as `executes` or `lockfile`:

- CI and automation: `.github/workflows/`, `.github/actions/`, `.devcontainer/`, git hooks
  (`.husky/`, `lefthook.yml`, `.pre-commit-config.yaml`).
- Build and task runners: `Makefile`, `justfile`, `build.rs`, `Dockerfile`, compose files, shell
  scripts, `.cargo/config.toml`, tool version files (`mise.toml`, `.tool-versions`, `.envrc`).
- Manifests whose scripts run on install: `package.json` (`preinstall`, `postinstall`,
  `prepare`), `setup.py`, `pyproject.toml` build backends, `conftest.py`, `noxfile.py`.
- Tool configs that are code: `vite.config.*`, `webpack.config.*`, `jest.config.*`, and the like.
- Lockfiles and dependency changes: a new or repointed dependency runs its own install and build
  scripts.

Test files run too: a test can do anything the language can. Read the tests of an outside
contributor before running them, like any other code.

## Before running anything

For an outside author whose pull request changes any of the above:

1. Read each of those files completely in the diff and in the checkout — not only the hunks.
2. Look for anything the change does not need: network calls, downloads, writing outside the
   project, reading `~/.ssh`, `~/.config`, tokens or environment variables, encoded or obfuscated
   strings, a dependency from an unexpected registry or a git URL.
3. For a new or changed dependency: its name (typosquatting), its source, its install scripts.

If any of it is suspicious, stop: tell the user what you found, run nothing, and do not post a
review until the user decides. If it is clean, say so in the plan and run the checks.

## While running

- Only in the review worktree, never in the user's checkout.
- Without credentials in the environment: no `GH_TOKEN`, cloud keys, or registry tokens exported
  to the build. Commands that need the network for dependencies are fine; commands that would push,
  publish, or deploy never run during a review.
- When the repository offers an isolated way to build (a dev container, a `docker` target), prefer
  it for an outside author.

## What to report

A suspicious file is the main finding of the review, reported to the user, not in a public
comment until the user decides — it may be a security matter for the repository's policy rather
than a review. A security defect in a public repository is reported through the security policy
(`SECURITY.md`), never in a public review comment.
