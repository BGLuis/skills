# Delivery checklist

Go through it in order, after running `scripts/validate_report.py`. The script checks the shape;
this list checks what only a critical reading catches. An item that fails goes back into the
text — not into the limits section.

## 1. Grounding
- [ ] Did the research follow the depth of the mode (`research.md`): full in A, medium in B,
      minimal in C?
- [ ] Does each decision or fix have a level 1 to 3 basis — `file:line` precedent, official doc,
      or maintainer example — or is it marked `[modeled]` with the reason?
- [ ] Were internal precedents searched by pattern and by symptom, not just by module name?
- [ ] Does every divergence from a precedent have a written justification?
- [ ] Was the version of each dependency read from the lockfile, and is the doc consulted for
      that version?
- [ ] Does no claim about an external API come from the model's memory?

## 2. Evidence
- [ ] Does every claim about code have `file:line`, and were those lines opened in this session?
- [ ] Does every absence have the zero-result search with the command?
- [ ] Is every number measured (with origin) or marked `[modeled]`?
- [ ] Does every performance number declare environment, tool, n, statistic, and limiting
      resource (`performance-measurement.md`)?
- [ ] Were before and after measured with the same protocol?

## 3. Actionability
- [ ] Is every acceptance criterion falsifiable — a command, an assertion, a trace observation?
- [ ] Does every mode B finding have a `**Reproduction:**` someone else can follow?
- [ ] Does each mode A verification item point to the decision or source it validates?
- [ ] Does no section end in a summary?
- [ ] Are the non-goals (mode A) and the deviations from the plan (mode C) written, not implied?

## 4. Honesty
- [ ] Does the not-verified section list everything left as assumption, including sources that
      could not be consulted?
- [ ] Is no checkbox marked `[x]` without having run in this session?
- [ ] Are refuted hypotheses still on record?

## 5. Language
- [ ] Was the report language chosen by the rule in `SKILL.md` §0, and is it used consistently —
      section titles, labels, and typography from `locales.md`?

## On delivery
State the path, the mode, the report language and where it came from, the validator result, the
sources that could not be consulted, and what was left unverified — without softening.
