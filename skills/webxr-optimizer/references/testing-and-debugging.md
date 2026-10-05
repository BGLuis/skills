# Testing and Debugging WebXR

Emulators prove that the code paths work. Only a real headset proves performance. Use both, and never report a frame-time number measured in an emulator.

## 1. Choose the right test surface

| Goal | Tool | Notes |
|---|---|---|
| Functional tests in CI, no headset | **IWER** (`npm i -D iwer`) driven by Playwright | Maintained by Meta. Software GL, so it is **not a performance proxy**. |
| Manual desktop iteration | IWER + `@iwer/devui` (and `@iwer/sem` for AR), or the IWSDK Vite plugin, or `createXRStore({ emulate })` in `@react-three/xr` | All three are IWER underneath. |
| Real performance, Quest | Headset over USB/Wi-Fi + OVR Metrics Tool + Chrome tracing + RenderDoc | §4 |
| Vision Pro without a device | visionOS Simulator (Apple-silicon Mac) | `transient-pointer` works in the Simulator. GPU cost and hand tracking are not representative. |
| Android XR without a device | Android XR Emulator (Android Studio Canary) | macOS on Apple silicon or Windows 11 only. **Linux is not supported.** |

Do not recommend these:
- The **Immersive Web Emulator** browser extension. Its repository is archived (last stable v1.3.0), and pmndrs says the old 1.x extension conflicts with the IWER that `@react-three/xr` integrates. Disable it if installed.
- Mozilla's **WebXR API Emulator**. It is archived and marked "INACTIVE".
- **Chrome DevTools**, which has **no** built-in WebXR emulation panel. The Sensors panel has nothing for XR.

Sources: https://api.github.com/repos/meta-quest/immersive-web-emulator , https://github.com/MozillaReality/WebXR-emulator-extension , https://developer.chrome.com/docs/devtools/sensors , https://raw.githubusercontent.com/pmndrs/xr/main/docs/getting-started/development-setup.md , https://developer.android.com/develop/xr/jetpack-xr-sdk/run/create-avds/xr-headsets-glasses , https://webkit.org/blog/15162/introducing-natural-input-for-webxr-in-apple-vision-pro/

## 2. IWER (Immersive Web Emulation Runtime)

Versions checked on 2026-10-05: `iwer`, `@iwer/devui` and `@iwer/sem` are all 2.5.0. Docs: https://meta-quest.github.io/immersive-web-emulation-runtime/

```js
import { XRDevice, metaQuest3 } from 'iwer';
const xrDevice = new XRDevice(metaQuest3);   // also metaQuest2, metaQuestPro, oculusQuest1, metaVRGlasses
xrDevice.installRuntime();                   // before any WebXR/rendering code runs
```

Gotchas, verified against the 2.5.0 source:
- **`installRuntime()` does nothing if `navigator.xr` already exists.** Desktop Chromium, including Playwright's Chromium, always has `navigator.xr`. Pass `{ forceInstall: true }` in tests. The console says `IWER: a native WebXR runtime is already available ... skipping installRuntime`.
- The 2.x API is `xrDevice.installDevUI(DevUI)` and `xrDevice.installSEM(SyntheticEnvironmentModule)`. Both take the **class**, not an instance. The `@iwer/sem` README still shows the old `installSyntheticEnvironmentModule(sem)`.
- IWER stubs `gl.makeXRCompatible()` to resolve immediately. A missing `makeXRCompatible` call therefore passes in IWER and fails on a headset.
- The Quest 3 preset reports `supportedFrameRates` `[72, 80, 90, 120]`, `frameRate` 90 and IPD 0.063, with the head at y = 1.6 in `local-floor`.
- `@react-three/xr` 6.6.x depends on older IWER packages (`iwer ^2.1.0`, `@iwer/devui ^1.1.1`). If a test harness installs IWER itself, create the store with `createXRStore({ emulate: false, offerSession: false })`, so that only one runtime runs and the session is not offered twice.

Sources: https://cdn.jsdelivr.net/npm/iwer@2.5.0/lib/device/XRDevice.js , https://cdn.jsdelivr.net/npm/iwer@2.5.0/lib/device/XRDevice.d.ts , https://registry.npmjs.org/@pmndrs/xr/latest , https://raw.githubusercontent.com/pmndrs/xr/main/skills/pmndrs-xr/references/architecture.md

### Playwright skeleton (this exact flow was run with iwer 2.5.0 on Chromium)

```js
// xr.spec.mjs: npm i -D @playwright/test iwer
import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const iwerUmd = readFileSync(require.resolve('iwer/build/iwer.min.js'), 'utf8');

test('enters an emulated immersive-vr session', async ({ page }) => {
  await page.addInitScript(iwerUmd);                      // defines global IWER
  await page.addInitScript(() => {
    const xrDevice = new IWER.XRDevice(IWER.metaQuest3);
    xrDevice.installRuntime({ forceInstall: true });
    window.xrDevice = xrDevice;
  });
  await page.goto('http://localhost:5173/');              // localhost is a secure context
  expect(await page.evaluate(() => navigator.xr.isSessionSupported('immersive-vr'))).toBe(true);
  await page.click('#enter-vr');
  await page.waitForFunction(() => window.xrDevice.activeSession);
  await page.evaluate(() => window.xrDevice.controllers.right.position.set(0.2, 1.2, -0.4));
  // Assert behaviour the app exposes: scene state, console milestones, screenshots.
});
```

To drive input, use `xrDevice.controllers.right.position` / `.quaternion`, `controller.updateButtonValue('trigger', 1)`, `xrDevice.primaryInputMode = 'hand'` and `xrDevice.recenter()`. pmndrs's validation guide adds three rules: make "Enter VR" idempotent, wait for scene readiness before entering, and use generous timeouts. Source: https://raw.githubusercontent.com/pmndrs/xr/main/skills/pmndrs-xr/references/validation.md

## 3. Remote debugging on real devices

WebXR is `[SecureContext]`. `http://<LAN-IP>` leaves `navigator.xr` **undefined**. Use `localhost` through port forwarding, or HTTPS. Source: https://immersive-web.github.io/webxr/

**Meta Quest** (Developer Mode on, `adb` installed):
```bash
adb devices                       # state must be "device"
adb reverse tcp:5173 tcp:5173     # open http://localhost:5173 in the headset Browser
# desktop Chrome → chrome://inspect/#devices → "inspect" next to the Browser tab
adb shell ip route; adb tcpip 5555; adb connect <ip>:5555   # wireless, then unplug
```
Sources: https://developers.meta.com/horizon/documentation/web/browser-remote-debugging/ , https://developers.meta.com/horizon/documentation/native/android/ts-adb/

**Apple Vision Pro:**
1. On the device, open Settings > Apps > Safari > Advanced and turn on **Web Inspector**.
2. With the Mac on the same Wi-Fi, open Settings > General > **Remote Devices** on the device.
3. In Mac Safari, choose Develop > (device) > **Use for Development** and enter the 6-digit PIN. The Mac needs Safari > Settings > Advanced > "Show features for web developers" turned on.
4. Booted visionOS Simulators also appear in the Develop menu.

Source: https://developer.apple.com/documentation/safari-developer-tools/inspecting-visionos

**Chrome on Android phones and Android XR:**
1. Turn on USB debugging.
2. Open `chrome://inspect/#devices` and enable "Discover USB devices".
3. Use **Port forwarding…** to reach your localhost dev server.

AR on a phone needs an ARCore-certified device with Google Play Services for AR. Google states that the Android Emulator does not support WebXR. Source: https://developer.chrome.com/docs/devtools/remote-debugging , https://developers.google.com/ar/develop/webxr/environment

## 4. Measuring performance on Quest

Start with the official bottleneck workflow in `budgets-and-profiling.md`. These are the tools:

- **OVR Metrics Tool**, a HUD inside the headset, installed through MQDH. Enable the overlay with:
  `adb shell am broadcast -n com.oculus.ovrmonitormetricsservice/.SettingsBroadcastReceiver -a com.oculus.ovrmonitormetricsservice.ENABLE_OVERLAY`.
  The Basic preset shows FPS, CPU/GPU level, CPU/GPU utilization, App GPU Time and **Stale Frame Count**. A stale frame means a frame was not delivered on time and the previous one was reused. A stale count between 0 and the refresh rate means judder.
  Sources: https://developers.meta.com/horizon/documentation/unity/ts-ovrmetricstool/ , https://developers.meta.com/horizon/documentation/unity/ts-ovrstats/
- **Chrome tracing** (CPU frame time). In `chrome://inspect#devices`, click **trace** next to `com.oculus.browser`, then Edit categories → **`xr.debug`**, then record. Investigate any code path above 2 ms. Source: https://developers.meta.com/horizon/documentation/web/webxr-perf-tools/
- **ovrgpuprofiler** (GPU). `adb shell ovrgpuprofiler --realtime="29,30"` shows the vertex vs fragment split. For a render-stage trace, run `adb shell am force-stop com.oculus.browser && adb shell ovrgpuprofiler -e`, load the app in VR, then run `adb shell ovrgpuprofiler -t`. Source: same page.
- **RenderDoc (Meta fork)** for a single-frame capture:
  1. In the headset Browser's `chrome://flags`, disable "Android ImageReader" and enable "RenderDoc Immersive Mode Support".
  2. In RenderDoc, launch or attach to `com.oculus.browser`.
  3. Sort draw calls by GPU duration.

  Source: https://developers.meta.com/horizon/documentation/web/webxr-perf-renderdoc/

**In-app counters.** In three.js, read these each frame inside `setAnimationLoop`:
- `renderer.info.render.calls` and `.triangles`
- `renderer.info.memory.geometries` and `.textures`
- `renderer.info.programs.length`

With multiple render passes per frame, set `renderer.info.autoReset = false` and call `renderer.info.reset()` once per frame. Source: https://threejs.org/docs/pages/WebGLRenderer.html

`stats.js` and `stats-gl` are DOM overlays. **The compositor does not show DOM inside an `immersive-vr` session.** Draw counters onto a `CanvasTexture` panel in the scene, or read them over `chrome://inspect`. To get GPU timer queries for `stats-gl` on Safari, turn on the "WebGL Timer Queries" feature flag. Source: https://cdn.jsdelivr.net/npm/stats-gl@4.2.3/README.md

## 5. Failure → cause table

| Symptom | Cause | Fix | Source |
|---|---|---|---|
| `navigator.xr` undefined | Not a secure context (`http://<LAN-IP>`) | HTTPS, `localhost`, `adb reverse` | https://immersive-web.github.io/webxr/ |
| `requestSession` → `NotSupportedError` | Mode unsupported, or a **required** feature unsupported | `isSessionSupported(mode)` first; move non-essential features to `optionalFeatures` | https://developer.mozilla.org/en-US/docs/Web/API/XRSystem/requestSession |
| `requestSession` → `SecurityError` | No transient user activation (called after long `await`s or a timer), or a cross-origin iframe without `allow="xr-spatial-tracking"` | Call it synchronously from the click handler; add the Permissions-Policy | https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Permissions-Policy/xr-spatial-tracking |
| `InvalidStateError` on `requestSession` | An immersive session is already active or pending (double click, or auto-offer plus manual entry) | Make entry idempotent; `offerSession: false` | spec `requestSession` steps |
| `InvalidStateError` on `new XRWebGLLayer` | The WebGL context is not XR-compatible | `await gl.makeXRCompatible()` before creating the layer (three.js does this for you) | https://immersive-web.github.io/webxr/ §WebGL context compatibility |
| Black or frozen view in the headset | Loop driven by `window.requestAnimationFrame`, or render target/post-processing not drawing into the XR framebuffer | `renderer.setAnimationLoop` / `session.requestAnimationFrame`; render into `session.renderState.baseLayer.framebuffer` | https://developer.mozilla.org/en-US/docs/Web/API/WebXR_Device_API/Rendering |
| Content at eye level or underground | Wrong reference space: `local` puts the origin at the head, `local-floor` puts it at the floor | Pick before the session: `renderer.xr.setReferenceSpaceType('local-floor')` (three.js default) | https://threejs.org/docs/pages/WebXRManager.html |
| Works in IWER, nothing on device (or the reverse) | IWER skipped installation (native `navigator.xr` present), or two emulators are active | `forceInstall: true`; disable the IWE extension | iwer source, pmndrs docs |
| `immersive-ar` unsupported on Vision Pro | visionOS does not implement it (a flag appeared in 26.5 and was removed in 27) | Offer a VR or `<model>` fallback | https://developer.apple.com/forums/thread/826845 |
| No AR button on an Android phone | Not ARCore-certified, Play Services for AR missing, or an insecure origin | Check device support; use HTTPS | https://developers.google.com/ar/develop/webxr/environment |
