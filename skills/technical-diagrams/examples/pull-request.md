<!-- Example: a pull request description with a before/after figure. It retells commit 95134d7
of this repository ("install technical-report with technical-issues"); the anchors point at the
lines on the branch, so a reviewer can open them in the diff. The before figure has no "deps" node,
so it needs no anchor for code that no longer exists. -->

## Summary

`./install.sh --skill technical-issues` installed only `technical-issues`, which stops at its first
step without `technical-report`. A single-skill install now also installs the skills it depends on.

The change is the dependency lookup between choosing the skill and linking it; the rest of the
install is untouched.

**Before**

```mermaid
flowchart LR
  accTitle: Single-skill install before this change
  %% @flag: install.sh:145
  %% @chosen: install.sh:146-147
  %% @link: install.sh#install_to_agent
  flag(["--skill technical-issues"]) --> chosen[Install the chosen skill]
  chosen --> link[Link into agent folders]
```

**After**

```mermaid
flowchart LR
  accTitle: Single-skill install after this change
  accDescr: The chosen skill's dependencies are looked up in skill_deps and installed with it.
  %% @flag: install.sh:145
  %% @chosen: install.sh:146-147
  %% @deps: install.sh:40-48 + install.sh:148-151
  %% @link: install.sh#install_to_agent
  flag(["--skill technical-issues"]) --> chosen[Install the chosen skill]
  chosen --> deps[Add its dependencies]
  deps -->|"technical-report"| link[Link into agent folders]
  classDef changed stroke:#d97706,stroke-width:3px
  class deps changed
```

The highlighted step is new. `skill_deps` is a `case` statement rather than an associative array
because macOS ships bash 3.2, which has no `declare -A`.

## Changes

- `install.sh`: `skill_deps` maps a skill to the skills it loads at run time; the single-skill
  branch appends them to `SKILLS_TO_INSTALL`.
- `README.md`: a note that `technical-issues` needs `technical-report` when installing from zips.

## How to verify

- `./install.sh --skill technical-issues --hub-dir "$(mktemp -d)"` lists both skills and links both.
- `bash -n install.sh`.
