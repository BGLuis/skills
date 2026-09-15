# Before / After Examples

Four short, common fixes. See `references/` for the rule and source behind each.

## 1. Diagnosing a slow HAR entry instead of reading it by hand

**Before**: opening the exported `.har` in a text editor and scrolling through raw JSON to guess which request is slow.

**After**: run the HAR through an automated analyzer and read the phase breakdown directly:
```
$ harview capture.har
GET https://example.com/api/products   total: 1840ms
  blocked: 5ms  dns: 2ms  connect: 0ms  ssl: 0ms
  send: 1ms     wait: 1790ms   receive: 42ms
```
The `wait` phase (server think-time) dominates — the fix is server-side, not a front-end asset problem. See `references/browser-debugging-and-har.md`.

## 2. Image delivery: raw JPEG vs. `<picture>` with modern formats

**Before** — one heavy JPEG, no format negotiation, loads eagerly at full priority even though it's below the fold:
```html
<img src="hero.jpg" alt="Product hero">
```

**After** — AVIF/WebP with JPEG fallback, sized to prevent CLS, and prioritized because it's the LCP element:
```html
<picture>
  <source srcset="hero.avif" type="image/avif">
  <source srcset="hero.webp" type="image/webp">
  <img src="hero.jpg" alt="Product hero" width="1200" height="600"
       fetchpriority="high" decoding="async">
</picture>
```
See `references/images-fonts-and-loading.md`.

## 3. Resource hints: over-preconnecting vs. targeted use

**Before** — `preconnect` scattered across every third-party domain the page might ever touch, exhausting the connection pool:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://analytics.example.com">
<link rel="preconnect" href="https://ads.example.com">
<link rel="preconnect" href="https://chat-widget.example.com">
<link rel="preconnect" href="https://cdn.example.com">
```

**After** — `preconnect` reserved for the 1-2 origins on the critical rendering path; everything else downgraded to the cheaper `dns-prefetch`:
```html
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="dns-prefetch" href="https://analytics.example.com">
<link rel="dns-prefetch" href="https://ads.example.com">
```
See `references/metadata-and-resource-hints.md`.

## 4. iOS viewport height bug

**Before** — content cut off or overscrolling on iOS Safari because `100vh` is measured against the toolbar-collapsed viewport:
```css
.full-screen-modal { height: 100vh; }
```

**After** — dynamic viewport unit tracks the toolbar, plus safe-area padding for notched devices:
```css
.full-screen-modal {
  height: 100dvh;
  padding-bottom: env(safe-area-inset-bottom, 0px);
}
```
See `references/safari-ios-quirks.md`.
