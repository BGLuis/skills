# Before / After Examples

Four short, common violations next to their systemized fix. See `references/` for the rule and source behind each.

## 1. Color: hardcoded hex vs. semantic token

**Before** — arbitrary hex, no reuse, no guaranteed contrast:
```css
.delete-button {
  background: #e11d1d;
  color: #ffffff;
}
```

**After** — semantic token pair, contrast verified once at the token level:
```css
.delete-button {
  background: var(--destructive);
  color: var(--destructive-foreground);
}
```
See `references/colors.md` (semantic naming, WCAG contrast).

## 2. Spacing: arbitrary pixel value vs. grid multiple

**Before** — off-grid value, doesn't compose with anything else in the layout:
```css
.card { padding: 13px; }
.card-grid { gap: 17px; }
```

**After** — both values are multiples of the 4px base unit, and padding stays ≤ the inter-card gap:
```css
.card { padding: 16px; }      /* 4 * 4 */
.card-grid { gap: 24px; }     /* 4 * 6, looser than internal padding */
```
See `references/spacing.md`.

## 3. Border-radius: same radius everywhere vs. scaled + concentric

**Before** — a small icon button and a large modal share one fixed radius; a badge nested near the modal's edge also gets the same radius, so its corner bulges past the modal's curve:
```css
.icon-button, .modal, .badge { border-radius: 12px; }
```

**After** — radius scales with component size, and the nested badge's radius is reduced by its inset padding so it stays concentric with the modal:
```css
.icon-button { border-radius: 6px; }   /* small control: small radius */
.modal { border-radius: 24px; }        /* large surface: large radius */
.badge { border-radius: 16px; }        /* 24px modal radius − 8px inset padding */
```
See `references/border-radius.md`.

## 4. Typography: fixed line-height vs. size-appropriate line-height

**Before** — one line-height reused everywhere, too loose for a large heading and borderline-tight for body copy:
```css
h1 { font-size: 36px; line-height: 1.5; }
p  { font-size: 16px; line-height: 1.5; }
```

**After** — heading tightens toward the display range, body stays in the readable band:
```css
h1 { font-size: 36px; line-height: 1.15; }  /* 1.1-1.3x for large display text */
p  { font-size: 16px; line-height: 1.5; }   /* 1.4-1.6x for body text */
```
See `references/typography.md`.
