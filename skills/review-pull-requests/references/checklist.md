# Review checklist — what to look for, in order of weight

The order follows Google's engineering practices ("What to look for in a code review"): design
first, style last, and every line read. Each item is a question to answer for this pull request,
with the evidence that answers it.

## Contents

- Fit with the project
- Purpose and design
- Correctness
- The claims
- Tests
- Security
- Performance
- Dependencies
- Documentation
- Naming, comments, style

## Fit with the project

The rules of step 1, checked against the lines they govern — this is what "consistent with the
project" means, and it is the first thing the user asked for.

- Does each new file sit in the layer and module the architecture prescribes? Does any import
  cross a boundary an ADR or a lint config forbids?
- Does it follow the written conventions (error types, logging, no panics, generics over dynamic
  dispatch — whatever `AGENTS.md` lists), each rule cited when it is broken?
- Does it contradict an accepted ADR? A change that does needs a new ADR that supersedes it, not
  an edit of the old one.
- Where the repository says nothing, does it look like the code next to it — the same patterns,
  the same shape of tests, the same naming?
- Does it reinvent something the repository already has? Name the precedent with `file:line`.

## Purpose and design

- Does it do what its issue asks — every acceptance criterion — and nothing the issue did not ask
  for? Extra scope is a separate pull request.
- Do the pieces belong where they are? Would the next feature in this area fit, or fight it?
- Is it more complex than the problem: an abstraction with one user, a configuration nobody needs,
  generality "for later"?

## Correctness

- Edge cases: empty, one, many, the maximum; invalid input; the error path of every call.
- Concurrency: shared state, ordering, cancellation, a task that outlives its caller.
- Resources: unbounded growth, a missing timeout, a leak on the error path.
- Compatibility: a public type, function, file format, config key, or wire format that changes
  shape breaks its users — is that intended, and said?

## The claims

Every guarantee written in the description, a doc comment, a commit message, or an ADR is a
promise. Check that the code enforces it, rather than relying on callers behaving: a "cannot"
that holds only while every caller is careful is a "should not". An unenforced guarantee is a
finding even when today's callers behave.

## Tests

- Is there a test for each new behavior and each fixed defect?
- Would the test fail if the code were broken? Revert the change (or the key line) in the
  worktree and run it: a test that still passes protects nothing.
- Do the tests check behavior a user would notice, not the implementation's internals?
- Are they deterministic: no sleeps, no order dependence, no real network or clock?

## Security

- Input from outside (network, files, users, upstream services) is validated before use.
- No secret, token, or credential in the code, the tests, or the fixtures.
- Injection: queries, commands, paths, and templates built from input.
- A workflow change that runs code from a fork with secrets (`pull_request_target` plus a checkout
  of the head) is a vulnerability, not a style point.
- A security defect in a public repository is reported privately (the repository's security
  policy), not in a public review comment.

## Performance

- Allocation, copying, or I/O added to a hot path; work repeated inside a loop.
- A claim of improvement comes with a measurement and its protocol, or is `[modeled]`.

## Dependencies

The four research checks of `references/research.md` are mandatory; these are the questions they
answer, plus the ones only judgment covers.

- Is the new dependency needed, or does the standard library or an existing one cover it?
- Is each added or changed version current, not yanked or deprecated, and free of applicable
  advisories (`scripts/dependency_diff.py`)?
- Does any changed line call an API that is deprecated in the installed version, or removed or
  replaced in the next one?
- Does the code use each library the way its documentation for that version says — call order,
  thread-safety, cleanup, errors, limits, defaults?
- Its license, its maintenance (last release, open issues on the feature used), and whether it is
  declared and pinned the way the repository does it.
- A lockfile change that updates more than the pull request needs.

## Documentation

- Behavior, configuration, or a public API that changed has its docs, changelog, example config,
  and ADR updated with it.
- The description says what changed, why, how it was tested, and the risks.

## Naming, comments, style

- Names say what things are, without abbreviations the repository avoids.
- Comments say why, not what; a comment that explains confusing code is a sign the code should be
  clearer.
- Style that a formatter or linter in the repository already enforces is not a review comment.
  Style it does not enforce is a `nitpick`, never blocking.
