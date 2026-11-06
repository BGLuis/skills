# Architecture

<!-- Example: the opening of an ARCHITECTURE.md for this repository (BGLuis/skills). Anchors
point at directories and symbols, not lines, because this file is updated rarely. Validate with:
python3 skills/technical-diagrams/scripts/validate_diagrams.py --repo-root . --render \
  skills/technical-diagrams/examples/architecture-md.md -->

## Bird's-eye view

The repository is a collection of Agent Skills: each folder under `skills/` is one skill, a
`SKILL.md` plus its references and scripts. Nothing here runs as a service. A skill reaches an
agent in one of three ways, and every push to `main` validates the skills and publishes them as a
GitHub release.

The figure shows those three paths, from the developer to the folder the agent reads.

```mermaid
flowchart LR
  accTitle: How a skill reaches an agent
  accDescr: A developer installs skills with npx skills, with install.sh, or from the release zips; all three end in the skills folder of each agent.
  %% @developer: external
  %% @npxSkills: external
  %% @installer: install.sh#install_to_agent
  %% @zips: .github/scripts/package_skills.sh
  %% @source: skills/
  %% @hub: install.sh#DEFAULT_HUB_DIR
  %% @agentDirs: install.sh#TARGETS
  developer([Developer]) -->|"npx skills add BGLuis/skills"| npxSkills{{skills CLI}}
  developer -->|"./install.sh"| installer[install.sh]
  developer -->|"unzip"| zips[Release zips]
  subgraph repo ["This repository"]
    source[skills folder]
  end
  npxSkills --> source
  installer --> source
  installer -->|"clone when run outside a checkout"| hub[("~/.agents hub")]
  installer -->|"symlink or copy"| agentDirs[Agent skill folders]
  npxSkills --> agentDirs
  zips --> agentDirs
```

## Codemap

- `skills/<name>/` — one skill. `SKILL.md` is the entry point; long material lives in
  `references/`, deterministic checks in `scripts/` with their tests in `scripts/tests/`.
- `install.sh` — the installer: picks the source folder, resolves `skill_deps`, and links each skill
  into every agent folder it finds (`install_to_agent`).
- `.github/workflows/` — `validate-skills.yml` checks every skill; `release.yml` reuses it, then
  packages and publishes.

The release pipeline, which only maintainers touch. A version tag publishes a release under that
tag; any other push to `main` gets a dated tag, with a counter when the date is already taken.

```mermaid
flowchart LR
  accTitle: Release pipeline
  accDescr: Every push validates and packages the skills; a version tag releases under that tag, a push to main under a dated tag.
  %% @push: external
  %% @validate: .github/workflows/validate-skills.yml
  %% @package: .github/workflows/release.yml#Package + .github/scripts/package_skills.sh
  %% @isTag: .github/workflows/release.yml#ref_type
  %% @tagRelease: .github/workflows/release.yml#--verify-tag
  %% @datedRelease: .github/workflows/release.yml#BASE_TAG
  push([Push to main or a v tag]) --> validate[Validate skills]
  validate -->|"passes"| package[Package zips]
  package --> isTag{Version tag?}
  isTag -->|"yes"| tagRelease[Release under that tag]
  isTag -->|"no"| datedRelease["Release under vYYYY.MM.DD"]
```

## Invariants

- A skill's folder name equals the `name` in its `SKILL.md`; `validate_skills.py` fails otherwise.
- `skill_deps` is not transitive: a skill that needs another lists every skill it reaches.
