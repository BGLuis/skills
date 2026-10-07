---
name: technical-report
description: Produces structured technical reports in docs/reports/ covering impacts, gains, results, steps, and implementation details, always anchored in verifiable file:line evidence and grounded in the official documentation of the installed version, in precedents from the codebase itself, and in reference examples. Writes the report in the language the repository asks for, or asks the user. Use when the user asks for a technical report, a feasibility analysis, a performance or usability audit of a module, a detailed implementation or validation plan, or documentation of work just completed. Do NOT use for README, API documentation, changelog, code comments, commit messages, Pull Request descriptions, business reports with no basis in code, or when the user wants the result as GitHub issues instead of a file (that is technical-issues).
---

# Technical Report

Act as a senior engineer doing a critical review. A report is only worth something if every
claim can be checked against the repository. Prose without evidence is noise.

## 0. Before writing

1. Find the project root and the `docs/reports/` folder. Create it if it does not exist.
2. If the folder already has reports, read the index and one or two of them. Existing local
   conventions take precedence over this skill's templates.
3. **Choose the report language**, first match wins:
   1. the language the user asked for explicitly;
   2. a written rule in the repository — `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`,
      `.github/copilot-instructions.md`, `CONTRIBUTING*`, `docs/reports/README.md` — about the
      language of documentation or reports;
   3. the language of the reports already in `docs/reports/`.

   With no signal, or with signals that conflict, **ask the user** before writing, suggesting
   the language of the repository's general docs (e.g. the README). Then take the section
   titles, field labels, closed vocabularies, and typography of that language from
   `references/locales.md`. Identifiers, file names, APIs, and commands are never translated.
4. **Collect real evidence first.** Read the files you cite, run the searches, check the
   numbers. Describing code from memory or guessing line numbers is forbidden.
5. **Research and ground.** Follow `references/research.md`: precedents in the codebase,
   versions pinned in the lockfile, official documentation for that version, reference
   examples, and known pitfalls — at the depth the mode asks for, and only until each decision
   has a basis. That is what makes the report improve the implementation, not just describe it.
6. Only then start writing.

## 1. Detect the mode

| Mode | When | Template |
|---|---|---|
| **A — Analysis/proposal** | Work not done yet: "what is missing to", "how to implement X", feasibility, planning | `references/mode-analysis.md` |
| **B — Audit** | Review existing code for defects: "analyze the performance of", "audit", "what problems does it have" | `references/mode-audit.md` |
| **C — Post-implementation** | The work was just done: "document what we did", "report on the changes" | `references/mode-post-implementation.md` |

If the request fits more than one mode, **ask the user which one**. Do not guess: the wrong
mode produces a report that answers the wrong question.

## 2. Invariant rules

Read `references/conventions.md` before writing any section. These are the rules shared by the
three modes — evidence, external sources, marking estimated numbers, typography, emojis, bold.
None of them is optional.

If the report has any performance, memory, byte, or cost number — measured or planned — also
read `references/performance-measurement.md` and follow the protocol.

## 3. Write

Read the template for the detected mode in `references/` and follow its section skeleton. The
templates give the literal section titles (in English; translate them with
`references/locales.md`) and the internal anatomy of each block.

Fit the depth to the scope: a report on one section stays around 120–160 lines; a report on a
feature or a large request, around 240–320. Go past 400 only when there is an exhaustive
inventory to present.

## 4. Name and save

Save in `docs/reports/` with a name in **UPPERCASE kebab-case, ASCII only (no accents or
cedillas)**, describing the topic — for example `SCREEN-FORMAT-MODAL.md`,
`UNIFIED-TEXT-INPUT.md`. Do not put a date in the name.

If the folder has a `README.md` acting as an index, add the matching row to the right table,
respecting the columns already there.

## 5. Validate before delivering

1. Run the shape validator that ships with this skill (`scripts/validate_report.py`, path
   relative to the skill directory) from the project root:

   ```bash
   python3 <skill-directory>/scripts/validate_report.py docs/reports/<FILE>.md
   ```

   It detects English or Brazilian Portuguese labels by itself (`--lang en|pt-BR` forces one).
   For any other language it runs only the structural checks and warns; check the
   label-dependent rules of `references/conventions.md` by hand and say so to the user. Fix
   every error reported and run it again until it exits clean. Without Python available, check
   the same rules by hand and say so to the user.
2. Walk through `references/checklist.md` — what the script does not catch: grounding,
   measurement protocol, falsifiable criteria.

Full examples of the expected shape: `examples/analysis-with-research.md` (mode A) and
`examples/performance-audit.md` (mode B).

## 6. Report to the user

When done, tell the user, in the language of the conversation:

- the path of the saved file, the mode used, the report language and where that choice came
  from, and the validator result;
- the claims that depend on measurement and have not been measured yet;
- the sources that could not be consulted and what was left `[modeled]` because of it;
- **what was not verified** — explicitly, without softening.

Never declare a report "complete" if any section was based on assumption. Say which one, and
why.
