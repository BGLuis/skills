# Contributing to {{PROJECT_TITLE}}

Thanks for your interest in contributing! This guide explains how to propose changes.

## Code of conduct

<!-- TEMPLATE: only if CODE_OF_CONDUCT.md is generated or already exists; otherwise delete the section. -->
By participating, you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Reporting bugs and suggesting improvements

- Search the [issues](https://github.com/{{OWNER}}/{{REPO}}/issues) to see if the topic is already open.
- If not, open an issue using the matching template (bug or feature).
<!-- TEMPLATE: only if SECURITY.md is generated or already exists; otherwise delete the item below. -->
- Security vulnerabilities must **not** be opened as issues: see the [Security Policy](SECURITY.md).

## Setting up the environment

Follow the "Getting Started" section of the [README](../README.md) to install and run the project.

## Contribution workflow

1. Fork the repository and create a branch from `{{DEFAULT_BRANCH}}`.
2. Make your changes in small commits with clear messages.
3. Run the checks below before opening the Pull Request.
4. Open the Pull Request against `{{DEFAULT_BRANCH}}` and fill in the template.

<!-- TEMPLATE: keep if there is Conventional Commits configuration (commitlint, commit-check.toml, cz). If only the commit history follows the format, ask the user. Otherwise delete the section. -->
## Commit convention

This project uses [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/): `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.

<!-- TEMPLATE: only commands that exist in the project (package.json scripts, Makefile, justfile, pyproject etc.). Delete lines with no command found; with none at all, delete the section. -->
## Checks

```sh
{{LINT_COMMAND}}
{{TEST_COMMAND}}
```
