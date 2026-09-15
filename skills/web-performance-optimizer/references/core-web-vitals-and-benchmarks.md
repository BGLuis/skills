# Core Web Vitals and Public Benchmarks

## Core Web Vitals thresholds (measured at the 75th percentile, segmented by mobile vs. desktop)

| Metric | Good | Needs Improvement | Poor |
|---|---|---|---|
| LCP (Largest Contentful Paint) | ≤2.5s | 2.5s–4.0s | >4.0s |
| INP (Interaction to Next Paint) | ≤200ms | 200ms–500ms | >500ms |
| CLS (Cumulative Layout Shift) | ≤0.1 | 0.1–0.25 | >0.25 |

INP officially replaced FID (First Input Delay) as a Core Web Vital on **March 12, 2024**. Supporting (non-Core) metrics: FCP good ≤1.8s / poor >3.0s; TTFB good ≤0.8s / poor >1.8s.
Sources: https://web.dev/articles/vitals , https://web.dev/articles/lcp , https://web.dev/articles/inp , https://web.dev/articles/cls , https://web.dev/articles/fcp , https://web.dev/articles/ttfb , https://web.dev/blog/inp-cwv-march-12

Always segment by device class — the thresholds are the same, but real-world distributions differ sharply between mobile and desktop, so an aggregate "average" number hides which device class is actually failing.

## Measuring field data: the `web-vitals` library

Google's official library reports the same `good`/`needs-improvement`/`poor` rating computed against the thresholds above:
```js
import {onCLS, onFCP, onINP, onLCP, onTTFB} from 'web-vitals';
onLCP((metric) => console.log(metric.name, metric.value, metric.rating));
```
A diagnostic build (`web-vitals/attribution`) and per-metric tree-shakeable imports are also available.
Source: `web-vitals` docs (Context7 `/googlechrome/web-vitals`)

## Chrome UX Report (CrUX) — real-user field data

CrUX aggregates real, opted-in Chrome user experiences and is the field-data signal behind Google's page-experience ranking. It supports both **origin-level** and **URL-level** granularity (URL-level requires enough traffic to be statistically eligible; otherwise only the origin aggregate is available). Query it via the CrUX API, the BigQuery public dataset (full granularity), or PageSpeed Insights (which surfaces it automatically).
Sources: https://developer.chrome.com/docs/crux , https://developer.chrome.com/docs/crux/methodology

## HTTP Archive and the Web Almanac — industry benchmarks

HTTP Archive crawls millions of URLs monthly, recording HAR + Lighthouse data; its annual **Web Almanac** report is a legitimate "how does my site compare to the industry" benchmark. 2024 edition figures (~17M sites):
- Median total page weight: ~2,652 KB desktop / ~2,311 KB mobile
- Median JS payload: ~620 KB desktop / ~570 KB mobile
- HTTP/2+ adoption: ~78–79% of home pages
- Image format share: JPEG 32.4%, PNG 28.4%, GIF 16.8%, WebP ~12%, AVIF ~1.0% (AVIF up 386% YoY but still niche)

Use these as a sanity check for whether your page is heavier/lighter than the median site, not as a target to hit exactly.
Sources: https://almanac.httparchive.org/en/2024/page-weight , https://almanac.httparchive.org/en/2024/http , https://almanac.httparchive.org/en/2024/media

## Lighthouse: CLI, CI, and performance budgets

- CLI: `lighthouse <url>`. Score buckets: 90–100 Good, 50–89 Needs Improvement, 0–49 Poor.
- CI: `npm install -g @lhci/cli`, then `lhci autorun` (collect + assert + upload); `lhci assert --preset=lighthouse:recommended` or `--budgetsFile=./budgets.json` fails the build on regression.
- `budgets.json` format enforces numeric ceilings (sizes in KB, timings in ms):
```json
[{
  "path": "/*",
  "timings": [{ "metric": "interactive", "budget": 3000 }],
  "resourceSizes": [
    { "resourceType": "script", "budget": 125 },
    { "resourceType": "total", "budget": 300 }
  ],
  "resourceCounts": [{ "resourceType": "third-party", "budget": 10 }]
}]
```
There's no single universal "official" byte ceiling — set budget values per project, calibrated against the Web Almanac medians above rather than an arbitrary number.
Sources: https://github.com/GoogleChrome/lighthouse-ci , https://web.dev/articles/use-lighthouse-for-performance-budgets

## PageSpeed Insights API and WebPageTest

- **PageSpeed Insights API**: free, returns lab data (Lighthouse) + field data (CrUX) for a URL in one response. Source: https://developers.google.com/speed/docs/insights/v5/get-started
- **WebPageTest.org**: tests on real browsers and real/emulated devices from real global network locations — including actual Firefox and Safari, not just Chromium — with configurable network throttling and waterfall/filmstrip views. The distinct advantage over Lighthouse alone: you get a genuine non-Chromium result instead of a Chromium approximation. Source: https://www.webpagetest.org/

## Lighthouse mobile vs. desktop throttling presets (exact values)

| | RTT | Throughput | CPU slowdown | Viewport |
|---|---|---|---|---|
| Mobile (`mobileSlow4G`) | 150ms | 1.6 Mbps down / 750 Kbps up | 4x | 412×823, DPR 1.75 |
| Desktop | 40ms | 10 Mbps | 1x (none) | 1350×940, DPR 1 |

Network throttling targets a fixed, device-independent condition; the CPU multiplier is relative to whatever machine runs the audit, so "4x slowdown" means something different on a fast CI runner than on a laptop — treat absolute Lighthouse CPU numbers as directional, not portable across environments.
Sources: https://github.com/GoogleChrome/lighthouse/blob/main/docs/throttling.md , https://github.com/GoogleChrome/lighthouse/blob/main/core/config/constants.js
