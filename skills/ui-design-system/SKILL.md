---
name: ui-design-system
description: Provides sourced, numeric rules for UI visual consistency -- color scales and semantic tokens, spacing/sizing grids, border-radius proportions, and typography scales. Use when generating or reviewing UI code (CSS, Tailwind classes, design tokens, component styles) and the user asks to make an interface consistent, choose a color palette, fix spacing, size border-radius, set up a type scale, or audit an existing UI for visual inconsistency or contrast issues. Do NOT use for backend logic, framework build/config setup (e.g. tailwind.config.js internals), brand/logo identity design, or full visual mockups in a design tool.
---

# UI Design System Rules

Act as a design-systems engineer: never pick a color, spacing value, radius, or font size by eye. Every value below traces to a named source (Tailwind CSS, Radix Colors, Material Design 3, W3C WCAG, Apple HIG, or the *Refactoring UI* book) — cite the relevant rule when you apply or flag one.

## 0. Workflow

- **Generating new UI**: before writing any CSS/class, decide the four scales up front (color tokens, spacing unit, radius steps, type scale) using the quick reference below and the matching `references/*.md` file. Never introduce a one-off pixel value that isn't a multiple of the chosen base unit.
- **Reviewing/auditing existing UI**: work through `references/review-checklist.md` and report violations with concrete values ("gap is 13px, not a multiple of the 4px grid" beats "spacing looks inconsistent").

## 1. Quick reference (most load-bearing values)

| Domain | Rule | Value |
|---|---|---|
| Spacing base unit | Grid | 4px (Tailwind) / 8px (Material, Apple HIG) |
| Touch target minimum | Size | 44×44pt (Apple) / 48×48dp (Material) / 24×24px (WCAG 2.2 floor) |
| Color contrast | WCAG AA | ≥4.5:1 normal text, ≥3:1 large text (≥24px or ≥18.67px bold) |
| Color contrast | WCAG AAA | ≥7:1 normal text, ≥4.5:1 large text |
| Color distribution | 60-30-10 rule | 60% dominant, 30% secondary, 10% accent |
| Border-radius | Nested/concentric | child radius = parent radius − padding |
| Body font size | Minimum | ~16px (browser default, Apple HIG, Material converge here) |
| Line-height | Body text | 1.4–1.6× |
| Line-height | Headings/display | 1.1–1.3× |
| Font families | Discipline | 1–2 families, 2–4 weights (e.g. 400/500/600/700) |

Full scales, step-by-step tier meanings, and every source URL live in `references/`.

## 2. Color

Read `references/colors.md` before choosing or reviewing any color. Covers: numeric color scales (Tailwind 50–950, Radix 12-step with tier→use mapping), Material 3 tonal palettes, semantic token naming (`primary`/`primary-foreground`, `destructive`, `muted`), the 60-30-10 distribution rule, and WCAG contrast thresholds.

## 3. Spacing and sizing

Read `references/spacing.md`. Covers: the 4px/8px base grid, why 8 is the near-universal default, minimum touch targets, and the padding-vs-gap proximity heuristic.

## 4. Border-radius

Read `references/border-radius.md`. Covers: the nested-radius/concentricity formula, standard radius scales (Tailwind, Material 3), and the rule that radius should scale with component size rather than being one fixed global value.

## 5. Typography

Read `references/typography.md`. Covers: modular type-scale ratios, the Material 3 type scale, Tailwind's paired font-size/line-height table, line-height bands by text role, minimum body size, and font-family/weight discipline.

## 6. Reviewing existing UI

Read `references/review-checklist.md` for the full audit checklist (one section per domain above, ordered by user-facing impact: contrast/accessibility first, then consistency).

## 7. Examples

Read `examples/before-after.md` for four short before/after snippets (color, spacing, radius, typography) showing a common violation next to its systemized fix.

## 8. Reporting

When auditing, quantify every finding against the specific rule and source ("gap uses `gap-[13px]`, not a 4px-grid multiple — see `references/spacing.md`"), not vague aesthetic opinions. When generating, briefly state which scale/tokens you used so the choice is traceable, not accidental.
