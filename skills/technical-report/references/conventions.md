# Conventions — rules shared by the three modes

Labels and examples below are in English. For a report in another language, use the
translations in `locales.md`; the rules themselves do not change.

## Contents

- The seven hard rules
- Shape
- Typography
- Emojis
- Bold
- Tone

## The seven hard rules

1. **Every claim about code carries `file:line`.** Accepted forms:
   - full: `chapters.component.ts:293-330`
   - several places: `item-book.component.ts:136-147` + `download.service.ts:58-76`
   - loose lines: `vr_player_app.cpp:1109-1114,1637`
   - short, when the file was already named in the paragraph: `:347-353`
   - symbol + file: `MediaMetadataReader.parse` (`filebrowser/MediaMetadataReader.kt:70`)

2. **Every absence is proven by a zero-result search**, showing the command:

   ```bash
   grep -rn "xrCreateHandTrackerEXT\|XR_HAND_JOINT" native/
   # → 0 results
   ```

   Never write "does not exist" without the proof. An unproven absence is a guess.

3. **Measured is not the same as estimated.** Every number that was not measured carries the
   literal marker `[modeled]` — as a column label (`| Impact [modeled] |`), inline
   (`**Cost [modeled]:** 20 cycles per second`), or opening the paragraph. Measured numbers
   state their origin: real build, bundle search, trace, test.

4. **No section ends in a summary.** It ends in a recommendation or a consequence. If the last
   paragraph only repeats what came above, delete it.

5. **A mandatory section for what was NOT verified.** Where it goes depends on the mode: in A it
   is section 5 (Verification, all in `- [ ]`) plus the closing blockquote; in B, section 7
   (Risks and what remains to verify); in C, section 7 (What was not verified). Refuted
   hypotheses stay on record, not deleted — so they are not raised again:
   > **There is no duplication** — the hypothesis is refuted and is recorded here so it is not
   > raised again.

6. **Closing blockquote**, after a `---`, stating what did not run in a real environment or on
   real hardware:
   > No item in this report was executed on the Quest 3. The whole analysis comes from reading
   > the code on branch `develop` (commit `e0e7406`); headset validation is listed in section 5
   > as pending.

7. **Every claim about external behavior carries `[Fn]`.** What a library, API, tool, or
   platform does — limits, defaults, costs, deprecations — is cited with the source consulted in
   this session, for the installed version. Sources go in the last numbered section,
   `## N. Sources consulted`, right before the closing blockquote (format in `research.md`).
   External behavior without a source is `[modeled]`.

## Shape

- No YAML frontmatter. The first line is the H1.
- A single H1. H2s **always numbered**: `## 1.`, `## 2.`, contiguous.
- H3s numbered in dot notation (`### 2.1 …`) or thematic (`### What does not exist`).
- **Never use H4.**
- `---` between every H2 section (and between findings, in audit mode). Never between H3s.
- Prose hard-wrapped at ~100 columns. Tables stay on a single line.
- A table is the default instrument for metrics. No charts, no ASCII bars, no badges.

## Typography

Follow the typography row of `locales.md` for the report language: decimal and thousands
separators, spacing before `%`, italics for foreign terms. Shared by every language:
`·` as separator · `—` for asides · `×` for versus · `→` for flow · `↔` for bidirectional ·
`–` en-dash in ranges (`5–7 dev-days`, `1.75–3`) · `≤ ≥ ≈ ~` as real symbols.

Identifiers, file names, APIs, and commands stay in their original form, inside backticks,
**never translated**.

A percentage is always approximate and qualified: `~35% (3 of 8 tasks)`.

Effort as a range of dev-days (`5–7 dev-days`), shortened to `d` inside tables.

Dates in ISO (`2026-09-23`). Times always with a time zone (`14:05 UTC`, `11:05 BRT`).

## Emojis

A **closed, semantic** set, never decorative:

✅ Done · 🟡 Partial · ❌ Not started · ⚠️ Divergence or risk

Used in the status column of tables, in the metadata table, and in titles that flag a finding
(`### ⚠️ Structural cost: two renderers`).

**No 🚀, 📊, 🎯, 💡.** Arrows and math symbols do not count as emojis.

## Bold

Three roles, and only these:

1. Field labels: `**Status**`, `**Fix:**`, `**Acceptance criteria:**`, `**Verdict:**`,
   `**Cost [modeled]:**`, `**Where:**`.
2. Identifiers: `**T1.1**`, `**F0**`, `**N2**`, `**P-01**`, `**High**`, `**new**`.
3. The word that carries the judgment in prose — 1 to 3 per paragraph, no more:
   `There is **not a single** line of code`, `**doubles** the cost`, `**truncates silently**`.

Italics are reserved for foreign terms, in languages that italicize them.

## Tone

Analytical, assertive, no hedging. State the mechanism before the impact. Recommend explicitly
and own the cost of the recommendation. Correct the request when the request is wrong, and say
why. Record pre-existing defects that are in the way, marking that they were not caused by the
current scope.

Be frank about what you do not know: *"it is an estimate that cannot be verified today"* is worth
more than an invented number with two decimal places.

Performance numbers follow the protocol in `performance-measurement.md` — environment, n,
statistic, and limiting resource declared. Without that, the number is `[modeled]`, even if it
was run.
