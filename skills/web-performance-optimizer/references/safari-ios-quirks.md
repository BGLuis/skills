# Safari and iOS Quirks

Safari/WebKit historically lags other engines on new features and has iOS-only behaviors that cause bugs invisible on desktop Chrome/Firefox testing.

## Modern image format support

- **WebP**: Safari added support in **Safari 14 / iOS 14** (September 2020) — Safari was the last major holdout.
- **AVIF**: baseline support landed in **Safari 16** (iOS 16 / macOS Ventura, September 2022); animated AVIF followed in **Safari 16.4** (March 2023) — Safari was again the last major engine to ship it.

Always provide a WebP or JPEG fallback via `<picture>` (see `images-fonts-and-loading.md`) if you need to support Safari <16 for AVIF or <14 for WebP.

## The `100vh` mobile viewport bug

`100vh` is defined against the *largest possible* viewport (browser chrome fully collapsed), which does not match what's actually visible when Safari's toolbar is showing — causing content to be cut off or the page to overscroll on load.

Fix: use the modern viewport-relative units, supported across current major browsers including Safari:
- `svh` — small viewport height (toolbar fully shown; the smallest value)
- `lvh` — large viewport height (toolbar fully hidden; the largest value)
- `dvh` — dynamic viewport height (updates live as the toolbar shows/hides)

Prefer `100dvh` for anything that must always fill the visible viewport correctly on mobile Safari.
Source: https://developer.mozilla.org/en-US/docs/Web/CSS/length#dvh

## Notch and home-indicator safe areas

WebKit introduced `viewport-fit=cover` in iOS 11 for the iPhone X notch:
```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
```
```css
.footer {
  padding-bottom: env(safe-area-inset-bottom, 0px);
}
```
Without `viewport-fit=cover` (or on non-notched devices) the `env()` inset values resolve to `0px` — always supply a fallback as the second argument to `env()`.
Sources: https://webkit.org/blog/7929/designing-websites-for-iphone-x/ , https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/env

## Obsolete momentum-scroll property

`-webkit-overflow-scrolling: touch` was required for momentum/inertial scrolling on iOS 5–12. As of **iOS 13**, momentum scrolling is the default for all scrollable elements — the property is now a no-op (it still parses, so `CSS.supports()` returns true, but does nothing). Safe to delete unless you must still support iOS ≤12.

## Touch handling

- **`touch-action`**: iOS Safari has historically supported only `auto` and `manipulation` reliably; fine-grained values (`pan-x`/`pan-y`/`none`) have had inconsistent/late support — check https://caniuse.com/css-touch-action before relying on them.
- **300ms tap delay**: mostly a solved historical problem. Chrome removed it when `width=device-width` is set; Safari's fix landed around **iOS 9.3** (2016), tied to the same viewport meta tag. Caveat: `touch-action: manipulation` (the modern cross-browser fix elsewhere) is not reliably honored by Safari for delay removal — the dependable fix on Safari specifically remains the `width=device-width` viewport meta tag.

## Autoplay and Low Power Mode throttling

WebKit blocks autoplay of media *with sound* by default and suppresses autoplay entirely for media in a background tab or off-screen. It also throttles `requestAnimationFrame` to 30fps inside cross-origin iframes without user interaction, and throttles rAF/CSS animations under iOS **Low Power Mode** — a demo or animation that runs smoothly in Chrome can silently drop to 30fps or stall entirely on an iPhone in Low Power Mode. Always test with Low Power Mode on.
Sources: https://webkit.org/blog/7734/auto-play-policy-changes-for-macos/ , https://webkit.org/blog/6784/new-video-policies-for-ios/
