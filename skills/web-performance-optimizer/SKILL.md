---
name: web-performance-optimizer
description: Audits and optimizes real-world website performance using sourced Core Web Vitals thresholds, public benchmarks (CrUX, HTTP Archive/Web Almanac, Lighthouse, WebPageTest), and per-browser/per-device debugging workflows -- HAR file export and analysis, the Firefox Profiler, and Safari/iOS-specific quirks. Use when the user asks to speed up a website, fix a Core Web Vital, debug a HAR file, diagnose a browser-specific (especially Firefox or Safari/iOS) performance or layout bug, choose an image format or lazy-loading strategy, or review page metadata/resource hints. Do NOT use for backend/API/database performance, native mobile app performance, or pure visual UI design (see ui-design-system for that).
---

# Web Performance Optimizer

Act as a web performance engineer: measure with real tools and real thresholds before changing anything, differentiate advice by browser and device class, and never hand-wave a fix without a numeric before/after.

## 0. Workflow

1. **Measure**: get field data (real users) and lab data (reproducible) before touching code. Read `references/core-web-vitals-and-benchmarks.md` for thresholds, tools (Lighthouse, PageSpeed Insights, CrUX, WebPageTest), and industry benchmarks (HTTP Archive/Web Almanac) to compare against.
2. **Debug per browser**: if the issue is browser-specific (classic case: fine in Chrome, slow or broken in Firefox or Safari), read `references/browser-debugging-and-har.md` for HAR export/analysis and the Firefox Profiler, and `references/safari-ios-quirks.md` for known Safari/iOS-only bugs before assuming a generic cause.
3. **Fix**: apply the concrete rules in `references/images-fonts-and-loading.md` and `references/metadata-and-resource-hints.md`.
4. **Verify**: re-measure with the same tool/device profile used in step 1, and report a before/after number, not an opinion.

## 1. Quick reference (most load-bearing values)

| Domain | Rule | Value |
|---|---|---|
| LCP | Good / Poor (p75) | ≤2.5s / >4.0s |
| INP | Good / Poor (p75) | ≤200ms / >500ms |
| CLS | Good / Poor (p75) | ≤0.1 / >0.25 |
| Lighthouse mobile throttling | RTT / throughput / CPU | 150ms / 1.6Mbps down / 4x slowdown |
| Lighthouse desktop throttling | RTT / throughput / CPU | 40ms / 10Mbps / no slowdown |
| `preconnect` budget | Max per page | 3-4 (each holds a socket) |
| LCP image | Never do this | `loading="lazy"` |
| iOS viewport height fix | Use instead of `100vh` | `100dvh` / `svh` / `lvh` |

Full detail and every source URL live in `references/`.

## 2. Measuring: Core Web Vitals and benchmarks

Read `references/core-web-vitals-and-benchmarks.md` before claiming a site is "slow" or "fast." Covers: official Core Web Vitals thresholds, the `web-vitals` library for field measurement, CrUX (real-user data), HTTP Archive/Web Almanac (industry-wide benchmarks to compare against), Lighthouse CLI/CI with `budgets.json`, PageSpeed Insights API, WebPageTest, and the exact mobile-vs-desktop throttling presets Lighthouse uses.

## 3. Debugging per browser: HAR files and the Firefox Profiler

Read `references/browser-debugging-and-har.md` before manually eyeballing a network panel. Covers: the HAR format and what each `timings` phase means, exporting HAR from Chrome/Firefox/Safari, tools that parse a HAR automatically instead of reading it by hand, the Firefox Profiler workflow, and documented Firefox-vs-Chrome behavioral gaps that cause browser-specific slowdowns.

## 4. Safari and iOS quirks

Read `references/safari-ios-quirks.md` before assuming a mobile bug is a generic responsive-design issue. Covers: WebP/AVIF support by Safari version, the `100vh` viewport bug and its fix, notch/home-indicator safe areas, obsolete momentum-scroll properties, touch-action/tap-delay history, and autoplay/Low Power Mode throttling.

## 5. Images, fonts, and loading strategy

Read `references/images-fonts-and-loading.md`. Covers: AVIF vs WebP, the `<picture>` fallback pattern, `srcset`/`sizes`, `loading="lazy"` and its LCP caveat, `fetchpriority`/`decoding`, `font-display`, font preloading, and subsetting/variable fonts.

## 6. Metadata and resource hints

Read `references/metadata-and-resource-hints.md`. Covers: `preconnect`/`dns-prefetch`/`preload`/`prefetch` and when each is appropriate, viewport/charset meta tags, Open Graph basics, modern favicons, and iOS/PWA metadata (`apple-touch-icon`, splash screens, web app manifest).

## 7. Reviewing an existing site

Read `references/review-checklist.md` for the full audit checklist, ordered by impact: field Core Web Vitals first, then browser/device-specific issues, then images/fonts, then metadata, then the accessibility rules that intersect with performance (`prefers-reduced-motion`, CLS harming low-vision/motor-impaired users, keeping lazy-loaded content accessible).

## 8. Examples

Read `examples/before-after.md` for four short before/after snippets: diagnosing a slow HAR entry, a correct `<picture>` element, resource-hint overuse, and the iOS `100vh` fix.

## 9. Reporting

Quantify every finding against its specific rule and source ("LCP image has `loading=\"lazy\"`, which delays it — see `references/images-fonts-and-loading.md`"), and prefer field data (CrUX) over lab data (Lighthouse alone) when they disagree, since field data reflects what real users on real devices actually experience.
