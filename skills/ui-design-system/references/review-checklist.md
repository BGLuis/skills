# UI Consistency Review Checklist

Work through in order. Section 1 affects real users the most (accessibility) — report it first.

## 1. Contrast and accessibility
- [ ] Text-on-background pairs meet WCAG AA (≥4.5:1 normal text, ≥3:1 large text)? Flag any pair that doesn't, with the actual computed ratio.
- [ ] Interactive targets (buttons, icon buttons, checkboxes) ≥24×24px (WCAG 2.2 floor) — ideally ≥44×44pt / 48×48dp?
- [ ] Any text set directly on a Radix step 9/10 solid fill, or a large fill using step 11/12 (text-only tiers)?

## 2. Color
- [ ] Are colors pulled from a defined scale/token set, or are there raw one-off hex values in component code?
- [ ] Does every background token (`bg-*`) have a paired, legible foreground token, rather than a hardcoded text color?
- [ ] Is `destructive`/error color reserved for actually harmful/destructive actions, not reused for generic emphasis?
- [ ] Rough color distribution in the ballpark of 60% dominant / 30% secondary / 10% accent, or is accent color overused to the point nothing stands out?

## 3. Spacing
- [ ] Every padding/margin/gap value a multiple of the project's base unit (4px or 8px)? Flag arbitrary values (`13px`, `gap-[17px]`).
- [ ] Is internal component padding ≤ the gap between sibling components (proximity/grouping still legible)?
- [ ] Touch targets have enough surrounding space from adjacent targets (≥8dp/≥24px)?

## 4. Border-radius
- [ ] Is radius picked from a defined scale, or arbitrary per component?
- [ ] Does radius scale with component size (small controls get small radius, large surfaces get large radius) rather than one fixed value everywhere?
- [ ] Where a rounded element is nested inside another rounded element, does the inner radius equal outer radius minus padding (concentric), rather than matching the outer radius exactly?

## 5. Typography
- [ ] Font sizes drawn from a defined type scale, not arbitrary values?
- [ ] Body text ≥~16px, with 1.4–1.6× line-height?
- [ ] Headings/display text with tighter 1.1–1.3× line-height, not inheriting the body ratio unchanged?
- [ ] Project uses at most 1–2 font families and a small, consistent set of weights?

## Reporting

Quantify every finding against the specific rule and its source ("gap uses `gap-[13px]`, not a 4px-grid multiple — see `references/spacing.md`"), never a vague aesthetic opinion. Close with the single highest-impact fix.
