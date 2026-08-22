# Workflow Patterns

## Baseline CI skeleton

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:

permissions: {}

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: .nvmrc
          cache: npm
      - run: npm ci
      - run: npm test
```

## Caching per ecosystem

| Stack | Preferred | Key derived from |
|---|---|---|
| Node | `setup-node` with `cache: npm\|yarn\|pnpm` | lockfile |
| Python | `setup-python` with `cache: pip\|poetry` | `requirements.txt` / `poetry.lock` |
| Go | `setup-go` (caches build + module cache by default) | `go.sum` |
| Rust | `Swatinem/rust-cache` | `Cargo.lock` + toolchain |
| Docker | `docker/build-push-action` with `cache-from/to: type=gha` | layer graph |

Manual `actions/cache` fallback:

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/thing
    key: ${{ runner.os }}-thing-${{ hashFiles('**/lockfile') }}
    restore-keys: ${{ runner.os }}-thing-
```

A cache key with no `hashFiles` is a stale-cache bug waiting to happen.

## Safe handling of untrusted input

```yaml
# WRONG — command injection
- run: echo "Title: ${{ github.event.pull_request.title }}"

# RIGHT
- env:
    TITLE: ${{ github.event.pull_request.title }}
  run: echo "Title: $TITLE"
```

## Matrix

```yaml
strategy:
  fail-fast: false
  matrix:
    node: [20, 22]
    os: [ubuntu-24.04, macos-14]
runs-on: ${{ matrix.os }}
```

Exclude combinations with `exclude:` rather than adding `if:` guards inside steps.

## Reusable workflow

Called with `uses: owner/repo/.github/workflows/ci.yml@sha`. Declare the contract explicitly:

```yaml
on:
  workflow_call:
    inputs:
      node-version: { required: true, type: string }
    secrets:
      NPM_TOKEN: { required: false }
```

Use a **composite action** instead when you are factoring out steps within one job; use a **reusable workflow** when you are factoring out whole jobs.

## Deploy with OIDC (no long-lived secrets)

```yaml
permissions:
  id-token: write
  contents: read
steps:
  - uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: arn:aws:iam::123456789012:role/deploy
      aws-region: eu-west-1
```

## Release on tag

```yaml
on:
  push:
    tags: ['v*']
jobs:
  release:
    permissions:
      contents: write
    environment: production
```
