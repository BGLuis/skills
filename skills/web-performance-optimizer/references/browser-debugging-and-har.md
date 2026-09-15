# Browser Debugging: HAR Files and the Firefox Profiler

## The HAR format

HAR (HTTP Archive) is a JSON format for recorded network traffic. Top level is a `log` object containing `version`, `creator`, `browser`, `pages`, and `entries`. Each `entries[]` item records one request/response pair, including a `timings` breakdown (all values in ms; `-1` means not measured):

| Phase | Meaning |
|---|---|
| `blocked` | queued waiting for a free connection (pool limits, proxy negotiation) |
| `dns` | DNS resolution |
| `connect` | TCP connection setup |
| `ssl` | TLS handshake (also folded into `connect` for backward compatibility — don't double-count) |
| `send` | writing the request to the socket |
| `wait` | waiting for first byte of response (server think-time / TTFB) |
| `receive` | reading the full response body |

`time` (total) must equal the sum of the defined phases — a useful sanity check on a malformed HAR. Reading these fields tells you *which phase* is slow (DNS vs. TLS vs. server think-time vs. download) instead of guessing from a vague "request took 800ms."
Sources: http://www.softwareishard.com/blog/har-12-spec/ , https://w3c.github.io/web-performance/specs/HAR/Overview.html

## Exporting a HAR from each browser

- **Chrome**: Network panel → Export/download icon → "Export HAR (sanitized)…" (enable "Allow to generate HAR with sensitive data" under Settings → Preferences → Network first if you need auth headers/cookies included). HAR files can also be **imported** back into Chrome DevTools (drag-and-drop or "Import HAR") to visualize them in the familiar waterfall UI, even if captured elsewhere. Source: https://developer.chrome.com/docs/devtools/network/reference
- **Firefox**: Network Monitor → gear icon → enable "Persist Logs" (and optionally "Disable Cache") → reproduce the issue → gear icon → "Save All As HAR" (or "Copy All as HAR" for the clipboard). Source: https://firefox-source-docs.mozilla.org/devtools-user/network_monitor/toolbar/index.html
- **Safari**: enable the Develop menu (Settings → Advanced → "Show Develop menu"), Develop → Show Web Inspector → Network tab → record while reproducing → click Export (⌘S). If Export is greyed out, reload the page with Web Inspector already open. Source: https://webkit.org/web-inspector/network-tab/

## Analyze the HAR automatically — don't read it by hand

This is the single highest-value fix for manual HAR debugging:
- **Google's HAR Analyzer** (free web tool): flags large/slow requests, render-blocking resources, missing compression, without manually scanning bytes. https://toolbox.googleapps.com/apps/har_analyzer/
- **`harview`** (CLI): dumps a human-readable summary of a `.har` file straight to the console — good for long request chains. https://github.com/fboender/harview
- **`harhar`** (CLI, Go): record/replay/manipulate/analyze HAR from the command line. https://github.com/bobvanderlinden/harhar
- **Import into Chrome DevTools** (see above) to get the visual waterfall for a HAR captured in *any* browser, including Firefox or Safari.
- Lighthouse can emit a HAR alongside its own audit run, letting you pair an automated score with the raw HAR for the same load.

## Firefox Profiler (deeper than a HAR — CPU/JS profiling)

A HAR only records network activity; for CPU/JS bottlenecks in Firefox, use the dedicated **Firefox Profiler**:
1. Visit https://profiler.firefox.com/ once and enable the "Profiler Button" in the toolbar (or configure directly from `about:profiling`).
2. Pick a preset, click "Start Recording," reproduce the slow interaction, click "Capture Recording."
3. The profile can be uploaded (with privacy scrubbing) to get a shareable profiler.firefox.com link.

It samples call stacks (~every 1–2ms) per thread — this is what actually shows *which function* is slow, which a HAR cannot show since a HAR only covers network timing.
Sources: https://profiler.firefox.com/docs/ , https://github.com/firefox-devtools/profiler/blob/main/docs-user/guide-perf-profiling.md , https://hacks.mozilla.org/2022/03/performance-tool-in-firefox-devtools-reloaded/ (the DevTools "Performance" panel is built on the same engine)

## Documented Firefox-vs-Chrome gaps worth checking before assuming a generic cause

- **`font-display` + cache bug**: a known Firefox bug causes the `font-display` timeout to trigger even when the font is served from cache (Bugzilla #1486158) — check this specifically if a Firefox-only FOIT/FOUT flash doesn't match your `font-display` value. https://bugzilla.mozilla.org/show_bug.cgi?id=1486158
- **`content-visibility` support lag**: Chrome shipped it in Chrome 85; Firefox required an `about:config` flag (`layout.css.content-visibility.enabled`) until roughly Firefox 124–125; Safari added it in Safari 18. A below-the-fold render-skip optimization that works in Chrome may silently do nothing on an older Firefox/Safari. https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/content-visibility
- **HTTP cache invalidation differences**: Firefox invalidates cache entries on unknown HTTP methods and on `Location`/`Content-Location` URLs after unsafe methods, where Chrome/Safari/Edge do not — relevant if a resource unexpectedly re-fetches only in Firefox.
- **Content-sniffing stall**: Firefox's content-sniffer can stall a `fetch()` response for up to ~512 bytes if `Content-Type` isn't set on the response — a request that "hangs briefly only in Firefox" is a common symptom. Always set an explicit `Content-Type`.
