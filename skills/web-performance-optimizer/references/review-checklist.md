# Web Performance Review Checklist

Work through in order. Field data (section 1) reflects real users — weight it above lab scores.

## 1. Core Web Vitals (field data first)
- [ ] Checked CrUX/PageSpeed Insights field data, not just a single Lighthouse lab run?
- [ ] LCP, INP, CLS at p75 within "Good" thresholds (≤2.5s / ≤200ms / ≤0.1), split by mobile and desktop?
- [ ] If only lab data is available, was it captured with the correct throttling profile for the device class being evaluated (see `core-web-vitals-and-benchmarks.md` for exact presets)?
- [ ] Page weight/JS payload compared against Web Almanac medians, not just "does it feel fast to me"?

## 2. Browser and device-specific issues
- [ ] Tested in actual Firefox and actual Safari (WebPageTest or real devices), not just Chromium DevTools device emulation?
- [ ] If a bug is Firefox-only: checked the `font-display`/cache bug and `content-visibility` support gap before assuming a generic cause (`browser-debugging-and-har.md`)?
- [ ] If a bug is Safari/iOS-only: checked `100vh`, safe-area insets, AVIF/WebP version support, and Low Power Mode throttling before assuming a generic responsive bug (`safari-ios-quirks.md`)?
- [ ] For a hard-to-diagnose network issue, was a HAR captured and run through an automated analyzer (Google HAR Analyzer, `harview`) instead of read by hand?
- [ ] For a CPU/JS bottleneck in Firefox specifically, was the Firefox Profiler used rather than just a HAR (which only covers network)?

## 3. Images and fonts
- [ ] Images served as AVIF/WebP with a `<picture>` fallback, not raw JPEG/PNG only?
- [ ] LCP image free of `loading="lazy"`, and marked `fetchpriority="high"` + `decoding="async"`?
- [ ] Non-critical images below the fold using `loading="lazy"` with explicit `width`/`height`?
- [ ] `font-display: swap` (or `optional`) set, and critical fonts preloaded with `crossorigin`?
- [ ] Font files subsetted, and weight count kept small?

## 4. Metadata and resource hints
- [ ] `preconnect` used sparingly (≤3–4 origins), not scattered across every third-party domain?
- [ ] Viewport and charset meta tags present and correctly ordered?
- [ ] If installable as a home-screen app: manifest, `apple-touch-icon` set, and iOS splash-screen tags present?

## 5. Accessibility ties to performance
- [ ] Heavy animation/autoplay/parallax gated behind `@media (prefers-reduced-motion: reduce)`?
- [ ] CLS kept low specifically because it causes mis-clicks for low-vision/motor-impaired users, not just as an SEO metric?
- [ ] Lazy-loaded or infinite-scroll content stays reachable and announced to assistive tech — a visible "Load More" alternative or `aria-live="polite"` region, not content silently removed from the accessibility tree?

## Reporting
Quantify every finding against its specific rule ("LCP is 3.8s on mobile field data, image has `loading=\"lazy\"` — remove it, see `images-fonts-and-loading.md`"), and close with the single highest-impact fix.
