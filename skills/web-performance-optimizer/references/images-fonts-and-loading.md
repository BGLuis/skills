# Images, Fonts, and Loading Strategy

## AVIF vs. WebP vs. JPEG/PNG

AVIF is ~20–30% smaller than WebP at equivalent quality, and 40–55% smaller than JPEG for photographic content, at the cost of 5–10x slower encoding (a build-time cost, not a page-load cost). Both AVIF and WebP now have broad browser support (~95%+); always ship a fallback for the remainder.
Source: https://caniuse.com/avif

## The `<picture>` fallback pattern

```html
<picture>
  <source srcset="image.avif" type="image/avif">
  <source srcset="image.webp" type="image/webp">
  <img src="image.jpg" alt="Description" width="300" height="200">
</picture>
```
The browser evaluates `<source>` elements top-to-bottom and uses the first `type` it supports, falling through to `<img>` if none match. Always set explicit `width`/`height` (or `aspect-ratio`) to reserve layout space and avoid CLS.
Source: https://web.dev/learn/design/picture-element

Combine with responsive `srcset`/`sizes` on each `<source>` (width-descriptor `srcset` plus a `sizes` matching the actual CSS layout — a mismatched `sizes` is a common, easy-to-miss bug).

## Lazy loading — and its critical LCP caveat

`loading="lazy"` on `<img>` defers offscreen image loads. Caveats:
- Always set explicit `width`/`height` on lazy images — an unloaded image has 0×0 dimensions, causing layout shift when it finally loads.
- Lazy loading only activates with JS enabled.
- **Never lazy-load the LCP image.** web.dev is explicit: "Never lazy-load your LCP image ... that will always lead to unnecessary resource load delay." Omit `loading="lazy"` from hero/above-the-fold images entirely.
Sources: https://web.dev/articles/lcp-lazy-loading , https://web.dev/articles/browser-level-image-lazy-loading

## Prioritizing the LCP image

For the LCP image specifically, use `fetchpriority="high"` plus `decoding="async"` (and leave `loading` at its default `eager`):
```html
<img src="hero.avif" alt="…" width="1200" height="600" fetchpriority="high" decoding="async">
```
`fetchpriority="high"` boosts the resource to High priority immediately during HTML parsing instead of waiting for layout-based viewport detection. Google's own Flights case study measured LCP improving from 2.6s to 1.9s from this alone. Reserve `fetchpriority="high"` for one or two truly critical resources per page — overuse defeats the purpose.
Sources: https://web.dev/articles/fetch-priority , https://web.dev/articles/optimize-lcp

## Fonts: `font-display`

| Value | Behavior |
|---|---|
| `block` | ~3s invisible text (FOIT), then swap |
| `swap` | text renders immediately in fallback (FOUT), swaps when ready — good default for body copy |
| `fallback` | ~100ms invisible, then fallback text if not ready, short swap window |
| `optional` | browser may never swap in the webfont if it's not ready in time — best for performance, worst for brand consistency |

`swap` can itself cause layout shift when the fallback font's metrics differ from the webfont's — mitigate with the `size-adjust`/`ascent-override`/`descent-override`/`line-gap-override` `@font-face` descriptors.
Source: https://developer.mozilla.org/en-US/docs/Web/CSS/@font-face/font-display

## Preloading a critical font

```html
<link rel="preload" href="/assets/Inter-Bold.woff2" as="font" type="font/woff2" crossorigin>
```
`crossorigin` is mandatory even for same-origin fonts — fonts always fetch anonymously, so omitting it triggers a second, non-matching request and wastes the preload.
Source: https://web.dev/articles/codelab-preload-web-fonts

## Subsetting and variable fonts

Subsetting strips unused glyph ranges and OpenType features/tables — usually the single biggest font-payload win for a single-language site. A variable font can replace multiple static weight/style files via font "axes"; only use it when the subsetted variable file is smaller than the combined static files it would replace.
Source: https://web.dev/articles/reduce-webfont-size

## Real build-time implementations

- **`sharp`** (Node): `sharp(input).avif({ quality: 50 })` / `sharp(input).webp({ quality: 80 })` to generate AVIF/WebP at build time.
- **`next/image`** (Next.js): `images: { formats: ['image/avif', 'image/webp'] }` in `next.config.js` negotiates format via the `Accept` header; the component's `preload` prop (replacing the deprecated `priority` prop as of Next.js 16) emits the LCP-image `<link rel="preload">` automatically.
