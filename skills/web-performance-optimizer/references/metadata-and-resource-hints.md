# Metadata and Resource Hints

## Resource hints — what each one costs

| Hint | What it does | Cost |
|---|---|---|
| `dns-prefetch` | resolves DNS only | cheapest — fine to use liberally for domains you might touch later |
| `preconnect` | DNS + TCP handshake + TLS negotiation | expensive per-origin — **no more than 3–4 per page**; each holds a socket, and over-preconnecting exhausts the connection pool and can make the page *slower* than no hints at all |
| `preload` | fetches a high-priority resource needed for *this* page load ASAP | use for the hero image, critical font, or critical CSS/JS |
| `prefetch` | fetches a resource likely needed for a *future* navigation, at low priority | use for the next likely page, not the current one |
Sources: https://web.dev/articles/preconnect-and-dns-prefetch , https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/dns-prefetch

## Essential meta tags

- **Viewport**: `<meta name="viewport" content="width=device-width, initial-scale=1">`. `initial-scale=1` is no longer strictly required to prevent unintended zoom in modern browsers, but is still conventional and needed for custom-scale/fixed-layout cases.
- **Charset**: `<meta charset="UTF-8">` must be the first element inside `<head>`, within the first 1024 bytes of the document.
Source: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/meta/name/viewport

## Open Graph

Required: `og:title`, `og:type`, `og:image`, `og:url`. Recommended: `og:description`, `og:site_name`, `og:locale`. Recommended `og:image` size: **1200×630px** (1.91:1), minimum 600×315.

## Favicon

Modern baseline: an SVG favicon plus a multi-size ICO fallback for legacy browsers:
```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/x-icon" href="/favicon.ico">
```
A square raster at a multiple of 48px (96×96 is a solid baseline) covers most remaining cases.

## iOS / PWA metadata

```html
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="apple-mobile-web-app-title" content="AppTitle">
<link rel="apple-touch-icon" sizes="180x180" href="touch-icon-iphone-retina.png">
<link rel="apple-touch-icon" sizes="152x152" href="touch-icon-ipad.png">
<link rel="apple-touch-startup-image" href="/launch.png"
      media="(device-width: 375px) and (device-height: 812px) and (-webkit-device-pixel-ratio: 3)">
```
Common `apple-touch-icon` sizes: 57, 72, 76, 114, 120, 144, 152, 167, 180 (px, square). iOS splash screens require per-device `apple-touch-startup-image` links matched by `media` query on width/height/pixel-ratio — there is no automatic scaling like manifest icons get.
Source: https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/SafariWebContent/ConfiguringWebApplications/ConfiguringWebApplications.html

## Web app manifest

For Chromium installability the manifest needs: `name` (or `short_name`), `start_url`, an `icons` array with at least one 192×192 and one 512×512 PNG, `display` set to `standalone`/`fullscreen`/`minimal-ui` (not `browser`), served over HTTPS with a registered service worker that has a fetch handler. `start_url` should point directly into the app experience, not a marketing landing page.
Source: https://web.dev/articles/add-manifest
