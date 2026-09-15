# Typography Scales

## Modular type-scale ratios

Named musical-interval ratios (used by tools like type-scale.com): Minor Second 1.067, Major Second 1.125, Minor Third 1.2, Major Third 1.25, Perfect Fourth 1.333, Augmented Fourth 1.414, Perfect Fifth 1.5, Golden Ratio 1.618.

Guidance: smaller ratios (1.067–1.125) suit dense/data-heavy UI with many small hierarchy jumps; mid ratios (1.2–1.333) suit typical app UI hierarchy; larger ratios (1.5+) suit marketing/editorial pages needing dramatic size jumps between heading and body.
Sources: https://creativemarket.com/blog/typographic-scale , https://cieden.com/book/sub-atomic/typography/different-type-scale-types

## Material Design 3 type scale (concrete px values)

| Category | Size |
|---|---|
| Display Large | 57px |
| Display Medium | 45px |
| Display Small | 36px |
| Headline Large | 32px |
| Headline Medium | 28px |
| Body Large | 16px |
| Body Medium | 14px |
| Body Small | 12px |
| Label Large | 14px (Medium weight) |
| Label Medium | 12px (Medium weight) |
| Label Small | 11px (Medium weight) |

Each token encodes size + line-height + weight + tracking together, not just a bare font-size.
Source: https://developer.android.com/develop/ui/compose/designsystems/material3 , https://material-web.dev/theming/typography/

## Tailwind font-size / line-height pairs (exact, from published theme defaults)

| Token | Font size | Line-height ratio |
|---|---|---|
| `text-xs` | 0.75rem (12px) | ≈1.33 |
| `text-sm` | 0.875rem (14px) | ≈1.43 |
| `text-base` | 1rem (16px) | 1.5 |
| `text-lg` | 1.125rem (18px) | ≈1.56 |
| `text-xl` | 1.25rem (20px) | 1.4 |
| `text-2xl` | 1.5rem (24px) | ≈1.33 |
| `text-3xl` | 1.875rem (30px) | 1.2 |
| `text-4xl` | 2.25rem (36px) | ≈1.11 |
| `text-5xl`–`text-9xl` | 3rem–8rem | 1 (tight, display sizes) |

Pattern: line-height shrinks as font-size grows — base body text sits at 1.5, and by `text-4xl`+ it collapses toward 1.0–1.1.
Source: https://tailwindcss.com/docs/theme

## Line-height bands by role (cross-source consensus)

- **Body text**: 1.4–1.6× (never below 1.2 for continuous reading text).
- **Headings/large display text**: 1.1–1.3×, tightening further at the largest sizes because large glyphs carry more built-in optical spacing.
Source: https://www.aleksandrhovhannisyan.com/blog/dont-use-a-fixed-line-height/

## Minimum readable body size

**16px is the de facto web convention minimum** for body copy — the default body size in every major browser, and the floor both Apple HIG and Material guidance converge on. Treat it as adjustable ±2px depending on the specific typeface's x-height (e.g. Garamond may need ~18px, Montserrat may work at ~14px), not as an absolute.
Sources: https://www.a11y-collective.com/blog/wcag-minimum-font-size/ , https://uxwest.com/fonts-should-be-16px-including-mobile-and-email/

## Font family / weight discipline

Limit a project to **1–2 font families** (one for UI/body, optionally a second for display/headings) and a **small, fixed set of weights** — commonly Regular 400, Medium 500, Semibold 600, Bold 700 (pick 2–4, not the full variable-font range) — to keep visual rhythm consistent.
