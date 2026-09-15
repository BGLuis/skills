# Border-Radius Proportions

## Nested-radius / concentricity rule

Formula: **parent radius = child radius + padding**, equivalently **child radius = parent radius − padding**.

Rationale: if a parent and a nested child share the *same* radius value, the inner shape's corner arc doesn't match the outer shape's arc at the padding offset — the inner corner visually bulges outward relative to the outer curve, breaking the appearance of concentricity.

**Caveat**: this simple subtraction holds for true circular arcs. Squircles/superellipses (iOS-style "continuous corners") don't offset predictably the way a circle does — a squircle offset by padding doesn't produce a smaller squircle, so tools approximate rather than use pure subtraction for that style.
Sources: https://www.figma.com/community/plugin/1518516680095681018/corner-radius-balancer , https://www.ui-skills.com/playbook/use-concentric-border-radius

## Radius scale steps

**Tailwind CSS** (exact values from published theme defaults):

| Token | Value |
|---|---|
| `rounded-xs` | 0.125rem (2px) |
| `rounded-sm` | 0.25rem (4px) |
| `rounded-md` | 0.375rem (6px) |
| `rounded-lg` | 0.5rem (8px) |
| `rounded-xl` | 0.75rem (12px) |
| `rounded-2xl` | 1rem (16px) |
| `rounded-3xl` | 1.5rem (24px) |
| `rounded-4xl` | 2rem (32px) |
| `rounded-full` | fully round |

Source: https://tailwindcss.com/docs/border-radius

**Material Design 3** shape scale: Extra small 4dp, Small 8dp, Medium 12dp, Large 16dp, Extra-large ~24–32dp (varies slightly by component set).
Source: https://m3.material.io/styles/shape/corner-radius-scale , https://developer.android.com/develop/ui/compose/designsystems/material3

## Radius scales with component size

Rule of thumb from Material 3's shape system, widely echoed elsewhere: **larger/more prominent components use larger radii** — full-screen sheets/dialogs get large/extra-large radius, small chips/buttons get small/extra-small radius. Radius is not a single global constant; it should scale with the physical size and prominence of the element it's applied to.
