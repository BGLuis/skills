# Replies and resolving threads

A reply is read by the reviewer, who decides from it whether to look again. It has to be true when
it is posted, short enough to read in a notification, and specific enough that the reviewer can
check it in one click.

## Contents

- Rules
- Reply shapes
- External contributors
- Posting
- Resolving

## Rules

- **The reviewer's language.** Reply in the language the comment was written in.
- **One reply per item**, in its own thread or quoting it; never one big comment answering
  everything at once, except for a final summary when the user asks for one.
- **The commit as a bare SHA**: `Fixed in 3f2a9c1.` — GitHub turns a SHA into a link to the
  commit. Do not put it, `#N`, or a URL in backticks; backticks are for paths, identifiers, and
  error text.
- **No "fixed" before the fix is pushed and verified.** Draft the reply after the push; post it
  after CI passes on that commit when the item was a fix.
- **Courtesy, no padding.** Thank the reviewer when a comment caught a real defect; no apologies,
  no flattery, no repeating the comment back.
- **No AI disclaimer.** The replies are posted in the user's name and the user approves each draft.

## Reply shapes

| Decision | en | pt-BR |
|---|---|---|
| Fix | Fixed in 3f2a9c1: the slot is now released in `Drop`, and `trial_cancel_frees_slot` covers it. | Corrigido em 3f2a9c1: o slot agora é liberado no `Drop`, e `trial_cancel_frees_slot` cobre o caso. |
| Already done | Addressed in 3f2a9c1 — `parse_effort` now rejects 5.5 (see the test). | Resolvido em 3f2a9c1 — `parse_effort` agora rejeita 5.5 (ver o teste). |
| Answer | It is reset in `Session::navigate` (`session/mod.rs:88`), so a stale result is dropped before `apply`. | Ele é zerado em `Session::navigate` (`session/mod.rs:88`), então um resultado antigo é descartado antes do `apply`. |
| Ask back | Do you mean moving the guard into `apply`, or splitting the message type? The first keeps one check; the second makes it a type error. | Você quer mover a guarda para o `apply` ou dividir o tipo da mensagem? A primeira mantém uma checagem; a segunda vira erro de tipo. |
| Defer | Agreed, but it changes the public `Cache` API, so I left it out of this PR: #131. Leaving this open for you to confirm. | Concordo, mas muda a API pública de `Cache`, então deixei fora deste PR: #131. Deixo aberto para você confirmar. |
| Disagree | I kept the single lock: splitting it lets `evict` run between the two halves, which the docs warn against [link]. Is there a cost of the single lock I'm missing? Leaving this open for you. | Mantive o lock único: dividi-lo deixa o `evict` rodar entre as duas metades, o que a documentação desaconselha [link]. Há algum custo do lock único que eu não esteja vendo? Deixo aberto para você. |

A reply that leaves its thread open ends by saying so and why, so nobody wonders whether it was
forgotten.

## External contributors

On a pull request from an outside contributor, open with thanks for the contribution, say plainly
what you changed in their code and why, one line per change, and credit what was kept. Show this
draft like any other before posting.

## Posting

After the user approves the drafts:

```bash
# Reply in a thread (the thread id printed by pr_context.py)
gh api graphql -f query='mutation($t: ID!, $b: String!) {
  addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: $t, body: $b}) { comment { url } } }' \
  -F t=<thread id> -F b=@reply.md

# Reply to an inline comment outside any thread (its numeric id)
gh api repos/<owner>/<repo>/pulls/<N>/comments/<comment id>/replies -F body=@reply.md

# Answer a review summary or a conversation comment
gh pr comment <N> --body-file reply.md
```

Write each body to a file outside the repository and pass it with `@file` or `--body-file`, so
quotes and backticks reach GitHub intact.

## Resolving

Only after the checks of the pushed commit pass, and only threads whose item was *Fix* or *Already
done* and verified:

```bash
gh api graphql -f query='mutation($t: ID!) {
  resolveReviewThread(input: {threadId: $t, resolutionReason: ADDRESSED}) { thread { isResolved } } }' \
  -F t=<thread id>
```

The schema also accepts `WONT_FIX` and `INVALID`; do not use them — closing a thread you disagreed
with takes the decision away from the reviewer. A thread with `viewerCanResolve` false stays open:
your reply is the answer, and someone with write access resolves it.
