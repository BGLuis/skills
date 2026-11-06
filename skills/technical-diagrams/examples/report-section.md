<!-- Example: section 4 of a mode C (post-implementation) report written with the technical-report
skill, about commit ba7913c of this repository ("automate release creation on push to main"). Only
this section is shown. The figure answers "who calls whom, in what order", so it is a sequence
diagram; the anchors carry line numbers like every other claim in the report. -->

## 4. Implementation details

### 4.1 Release reuses the validation workflow instead of copying it

`release.yml` calls `validate-skills.yml` as a reusable workflow (`release.yml:21-25`), so a release
can only be cut from a commit that passes the same checks as a pull request. Packaging waits on
validation (`needs: validate`, `release.yml:29`) and publishing waits on packaging
(`needs: package`, `release.yml:51`).

The tag is chosen at the last step: a pushed version tag is released as is, any other push to
`main` gets a dated tag with a counter (`release.yml:68-80`).

```mermaid
sequenceDiagram
  accTitle: Release on push to main
  accDescr: The release workflow validates, packages, and then publishes under a dated or version tag.
  %% @maintainer: external
  %% @release: .github/workflows/release.yml:1-25
  %% @validate: .github/workflows/validate-skills.yml:26-38
  %% @package: .github/workflows/release.yml:27-47 + .github/scripts/package_skills.sh:12-28
  %% @github: external
  participant maintainer as Maintainer
  participant release as release.yml
  participant validate as validate-skills.yml
  participant package as Package job
  participant github as GitHub Releases
  maintainer->>release: push to main
  release->>validate: workflow_call
  validate-->>release: frontmatter and script tests pass
  release->>package: needs validate
  package-->>release: all-skills.zip, one zip per skill, SHA256SUMS
  release->>github: gh release create with the dated tag
  github-->>maintainer: release with the zips attached
```

A failing validation stops the run before `package`; no partial release is published, because
`release` depends on `package`, which depends on `validate`.
