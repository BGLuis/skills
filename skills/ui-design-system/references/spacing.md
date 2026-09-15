# Spacing and Sizing

## The 4px/8px base grid

**Tailwind CSS** derives its entire spacing scale from one variable: `--spacing: 0.25rem` (4px). Every numeric spacing utility (`p-1`, `gap-2`, `m-4`, ...) is `calc(var(--spacing) * N)` — multiples of 4px: `1=4px, 2=8px, 3=12px, 4=16px, 6=24px, 8=32px`, etc.
Source: https://tailwindcss.com/docs/theme , https://tailwindcss.com/docs/margin

**Material Design** aligns components to an **8dp baseline grid**, with a **4dp sub-grid** for finer/icon-level adjustments. Canonical steps: 8, 16, 24, 32, 40, 48, 56, 64 px. Touch targets: ≥48×48dp with ≥8dp spacing between adjacent targets.
Source: https://m1.material.io/layout/metrics-keylines.html

**Apple HIG** conventionally aligns spacing/padding/element sizing to **multiples of 8pt** (8, 16, 24, 32, 40, 48), with 4pt for fine adjustment. Minimum tappable target: **44×44pt**.
Source: https://developers.apple.com/design/human-interface-guidelines/foundations/layout/

**Why 8 is the near-universal default**: both Apple (44/48pt targets, 8pt increments) and Google (8dp grid, 48dp targets) converge on 8 because it divides evenly into common screen densities (1×, 1.5×, 2×, 3×) without producing fractional/blurry pixels, and 4px serves both systems as the sub-grid for icons/borders/fine spacing.

## Padding vs. gap (proximity heuristic)

Common convention: a component's **internal padding should be ≤ the gap between sibling components** — e.g. a card with 16px padding sitting in a grid with 24px gaps — so grouping stays legible: tighter space reads as "one thing," looser space reads as "separate things." This is a repeated heuristic across Tailwind-based design systems and *Refactoring UI*-derived guides, not a single numeric standard.
Source: https://medium.com/design-bootcamp/top-20-key-points-from-refactoring-ui-by-adam-wathan-steve-schoger-d81042ac9802

## Practical rule

Pick one base unit (4 or 8) for the whole project and only ever use multiples of it for padding, margin, gap, and fixed sizing. An arbitrary value like `13px` or `gap-[17px]` is a signal the layout wasn't systemized.
