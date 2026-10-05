---
name: webxr-optimizer
description: Builds, reviews, optimizes, and debugs WebXR (VR/AR) websites made with three.js, React Three Fiber/@react-three/xr, or the raw WebXR API so they hold frame rate and work on Meta Quest Browser, Apple Vision Pro (Safari/visionOS), Android XR, and Chrome on ARCore phones. Use when the user reports low FPS, judder, or stutter in a headset, wants a WebXR scene faster, migrates off WebVR or deprecated three.js / @react-three/xr APIs, hits input that works on one device but not another (Vision Pro pinch, hands, phone taps), sees a session that will not start, asks which XR features a device supports, needs an AR fallback for iPhone, or wants to test WebXR without a headset. Do NOT use for 2D page-load speed or Core Web Vitals (that is web-performance-optimizer), native Unity/Unreal/visionOS/Android apps, A-Frame- or Babylon.js-specific APIs, or pure visual design.
---

# WebXR Optimizer

Act as a WebXR performance and compatibility engineer. A WebXR site has two failure modes, and this skill covers both:
- it **misses frames**, so the user sees judder;
- it **breaks on a device or library version**, because of deprecated APIs, unsupported features or input it does not handle.

Never call a fix done without a number measured on a headset, or an explicit statement that no headset was available.

## 0. Workflow

1. **Establish the target.** Read `package.json` and the lockfile for the `three`, `@react-three/xr` and `@react-three/fiber` versions. Find the renderer (`WebGLRenderer` or `WebGPURenderer`) and the target devices. If the devices are unknown, ask; the matrix in `references/devices-and-browsers.md` decides what is even possible.
2. **Scan for breakage.** Run `python3 scripts/scan_deprecated.py <src-dir>`. Gate every finding by the installed version, then fix with `references/deprecated-apis.md`.
3. **Measure before touching performance.** Get a frame time on the real device at its refresh rate. Classify the bottleneck as CPU, vertex or fragment with the workflow in `references/budgets-and-profiling.md`. Emulators and desktop FPS are not evidence.
4. **Fix by bottleneck** with `references/rendering-optimizations.md`. Make one change at a time.
5. **Check cross-device behavior** with `references/input-and-interaction.md` and `references/devices-and-browsers.md`.
6. **Verify.** Re-measure on the same device and rate. Add or update an IWER test for the session path (`references/testing-and-debugging.md`). Report before → after.

## 1. Quick reference

| Topic | Rule | Value / API |
|---|---|---|
| Frame budget | Per frame, CPU and GPU each | 72 Hz = 13.7 ms, 90 Hz = 11.1 ms, 120 Hz = 8.3 ms |
| Bottleneck test | Disable rendering → CPU vs GPU; scale 0.01 → vertex vs fragment | `renderer.xr.setFramebufferScaleFactor(0.01)` |
| Foveation | On; three's default is already max | `renderer.xr.setFoveation(1.0)` |
| Framebuffer scale | Only before the session | `setFramebufferScaleFactor` / `frameBufferScaling` |
| Frame rate | The rate the scene sustains; Quest only | `session.updateTargetFrameRate()` / `frameRate: 'mid'` |
| Render loop | Never window rAF | `renderer.setAnimationLoop` / `session.requestAnimationFrame` |
| Post-processing | Avoid; intermediate targets disable FFR | — |
| Textures | KTX2/Basis; set the transcoder path | `KTX2Loader().setTranscoderPath()` |
| Multiview | Only `WebGPURenderer({ multiview: true })` on the WebGL backend; `WebGLRenderer` has none | r186 |
| Features | Required = only essentials; then read what was granted | `session.enabledFeatures` |
| Input | Iterate all `inputSources`; three.js slots 0–3 | Vision Pro pinch = index 2–3 |
| Vision Pro | `immersive-vr` only; unknown required features reject the session | Safari 18+ |
| iPhone | No WebXR; fall back | `<model-viewer ar-modes="webxr scene-viewer quick-look">` |
| Testing | IWER in Playwright; native `navigator.xr` exists | `installRuntime({ forceInstall: true })` |

## 2. Deprecated APIs

Read `references/deprecated-apis.md`. Covers:
- WebVR → WebXR;
- 2018–2019 WebXR draft APIs that are still in tutorials;
- three.js removals by release (WebVR r112, encodings r162, WebGL1 r163, legacy lights r165 …);
- `@react-three/xr` v5 → v6 (removed vs deprecated-but-working);
- what is still current in r186 and must not be flagged.

`scripts/scan_deprecated.py` finds the mechanical cases. `--list-rules` prints every rule with its source.

## 3. Measuring

Read `references/budgets-and-profiling.md` before claiming a scene is slow or fast. Covers:
- budgets per refresh rate and the frame-rate API;
- Meta's CPU/vertex/fragment workflow;
- tools per device: OVR Metrics, Chrome tracing `xr.debug`, `ovrgpuprofiler`, RenderDoc, Safari Web Inspector;
- `renderer.info`, and what stale frames mean.

## 4. Optimizing

Read `references/rendering-optimizations.md`. Covers:
- session knobs: foveation, framebuffer scale, frame rate, clear color;
- WebXR Layers;
- multiview, and its real three.js support;
- draw calls (instancing, `BatchedMesh`, merging, LOD);
- materials, lights, shadows and overdraw;
- why post-processing hurts in XR;
- KTX2/Meshopt asset pipeline;
- shader and texture warm-up;
- render-loop correctness.

## 5. Devices and browsers

Read `references/devices-and-browsers.md` before assuming a feature exists. Covers:
- the device × feature matrix (Quest, visionOS, Android XR, ARCore phones, iOS);
- the source trap: MDN BCD omits visionOS, and aggregator sites are wrong;
- per-device quirks;
- secure context, user activation and Permissions-Policy;
- session lifecycle states that look like performance bugs.

## 6. Input

Read `references/input-and-interaction.md` when input works on one device and not another. Covers:
- target ray modes;
- the Vision Pro transient-pointer and the three.js controller-slot trap;
- hands (25 joints, three r162 opt-in);
- `xr-standard` gamepads;
- phone `screen` taps with DOM Overlay;
- UI that is invisible in the headset.

## 7. Stack setup

Read `references/threejs-and-r3f.md` for a correct `WebGLRenderer` / `WebGPURenderer` XR setup and a correct `createXRStore` configuration. To *build* R3F XR features in depth (interactions, teleport, uikit), the pmndrs team publishes its own `pmndrs-xr` skill in https://github.com/pmndrs/xr ; this skill covers performance and compatibility.

## 8. Testing without and with a headset

Read `references/testing-and-debugging.md`. Covers:
- IWER and its `forceInstall` gotcha;
- a Playwright skeleton that was verified to enter a session;
- which emulators are archived;
- remote debugging on Quest (`adb reverse`), Vision Pro (Web Inspector pairing) and Android;
- a symptom → cause table for sessions that fail to start or render black.

## 9. Reviewing

Use `references/review-checklist.md`, ordered by impact: breakage → cross-device → measured performance → tests. Before/after code for the six most common fixes is in `examples/before-after.md`.

## 10. Sources and reporting

- **Verify device support only in primary sources:**
  - webkit.org and developer.apple.com;
  - developers.meta.com and the Quest Browser release notes;
  - developer.android.com and chromestatus.com;
  - the immersive-web specs;
  - the library's own source and release notes.
- MDN BCD and caniuse do not track visionOS. "WebXR support in 2026" aggregator sites contain false claims.
- If a fact matters and the references may be stale, check the installed version's source. Facts here were checked on 2026-10-05.
- Report every finding with its rule and evidence (`file:line`, or device + refresh rate + metric before → after). Say which results came from a real headset and which from emulation.
