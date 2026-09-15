# Color Scales and Tokens

## Numeric scales

**Tailwind CSS** — 11 steps per color family: `50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950` (50 lightest, 950 darkest). Tailwind doesn't hard-prescribe a tier→role mapping, but its own usage converges on:
- **50–100**: light surface/background tints
- **500**: default/brand mid-tone
- **600–700**: hover/active/focus states (darker than base)
- **800–900**: body text on light backgrounds
- **950**: highest-contrast text/near-black

Prefer layering semantic aliases on top (`--color-primary: var(--color-blue-600)`) rather than shipping raw `gray-500` names into components.
Source: https://tailwindcss.com/docs/colors

**Radix Colors** — 12-step scale with the clearest published tier→use mapping of any public system:
| Steps | Use |
|---|---|
| 1–2 | App background / subtle component background |
| 3 | Normal UI element background (non-interactive fill) |
| 4 | Hover state background |
| 5 | Pressed / selected state background |
| 6 | Subtle borders (dividers, cards) |
| 7 | Borders on interactive components (default state) |
| 8 | Stronger borders + focus rings on interactive components |
| 9 | Solid backgrounds — primary/highest-chroma fill (buttons) |
| 10 | Hover state of a step-9 solid |
| 11 | Low-contrast text (secondary/muted text) |
| 12 | High-contrast text (accessible against step 1/2 backgrounds) |

Rule of thumb: never use step 9/10 for text, never use step 11/12 for large fills.
Source: https://www.radix-ui.com/colors/docs/palette-composition/understanding-the-scale

**Material Design 3** — each tonal palette has 13 fixed tone stops: `0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99, 100` (0 = black, 100 = white). Semantic roles pick specific tones per theme mode, e.g. `primary` = tone 40 (light) / tone 80 (dark); `on-primary` = tone 100 (light) / tone 20 (dark). This tone-swap keeps contrast correct automatically when switching light/dark.
Source: https://m3.material.io/styles/color/system/overview , https://developer.android.com/develop/ui/compose/designsystems/material3

## Semantic naming (shadcn/ui convention)

Name tokens by role, not hue: `background`, `foreground`, `primary`/`primary-foreground`, `secondary`, `accent`, `muted`, `destructive`, `border`, `input`, `ring`.
- Every surface token has a paired `-foreground` token for text on it — use `bg-primary` + `text-primary-foreground`, never `bg-primary` + a raw color for text.
- `destructive` is reserved specifically for harmful/delete actions; `muted` is for deliberately reduced-prominence content.
Source: https://ui.shadcn.com/docs/theming , https://github.com/shadcn-ui/ui/discussions/4216

## 60-30-10 distribution rule

- **60%** dominant/neutral color → base backgrounds, sets overall mood, low saturation.
- **30%** secondary color → supporting regions: sidebars, modals, secondary sections/cards.
- **10%** accent color → CTAs, highlights, small emphasis (buttons, badges, links).

This is a guideline, not a hard constraint — treat large swings from it as a signal to double-check hierarchy, not an automatic failure.
Sources: https://blog.logrocket.com/ux-design/60-30-10-rule/ , https://uxplanet.org/the-60-30-10-rule-a-foolproof-way-to-choose-colors-for-your-ui-design-d15625e56d25

## WCAG contrast (2.1 §1.4.3 / §1.4.6, carried into 2.2)

| Level | Normal text | Large text |
|---|---|---|
| AA | ≥4.5:1 | ≥3:1 |
| AAA | ≥7:1 | ≥4.5:1 |

"Large text" = ≥18pt (≥24px) regular, or ≥14pt (≥18.67px) bold. Ratios are hard thresholds — 4.499:1 fails a 4.5:1 requirement.

**WCAG 2.2 addition (SC 2.5.8, AA)**: interactive targets must be ≥24×24 CSS px, unless spaced ≥24px from adjacent targets, inline in text, or covered by an essential/user-agent-controlled exception.
Sources: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html , https://www.w3.org/WAI/WCAG21/Understanding/contrast-enhanced.html , https://wcag22aa.org/new-criteria/target-size/
