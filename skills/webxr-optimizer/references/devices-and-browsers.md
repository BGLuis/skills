# Devices and Browsers

A WebXR site runs on several different runtimes: Quest Browser (Chromium), Safari on visionOS (WebKit), Chrome on Android XR and Chrome on ARCore phones. Plain iOS Safari has no WebXR at all. Detect features at runtime, and keep every non-essential feature optional.

## 1. Source trap: how to verify device support

- **MDN browser-compat-data (and caniuse) list Safari as `false` for `navigator.xr`.** For iOS that is correct. For **visionOS it is wrong by omission**, because BCD does not track visionOS. BCD's Quest column (`oculus`) also stops at Quest Browser 42.0.
- **Aggregator sites** (vr.org, testmuai, abratabia, threejsresources and similar "WebXR support in 2026" pages) state false things. One example is "Safari 18 on iOS supports immersive-ar".
- Trust only primary sources:
  - Apple: webkit.org release posts and developer.apple.com.
  - Meta: developers.meta.com and the Meta Quest Browser release notes.
  - Google: developer.android.com, developers.google.com/ar and chromestatus.com.
  - The immersive-web specifications.
  - The library's own source and release notes.

## 2. Matrix (checked 2026-10-05)

| Feature | Quest Browser | visionOS Safari | Android XR Chrome | Chrome Android phone (ARCore) | iOS / iPadOS Safari |
|---|---|---|---|---|---|
| `navigator.xr` | Yes | Yes, on by default since visionOS 2 / Safari 18 | Yes | Yes (Chrome 79+) | **No** |
| `immersive-vr` | Yes | Yes, **the only immersive mode** | Not documented | Not verified | No |
| `immersive-ar` | Yes (passthrough; clear to transparent) | **No** | Yes | Yes (Chrome 81+) | No |
| `hit-test` | Yes | No | Yes | Yes (81) | No |
| `anchors` | Yes (max 8 persistent per site) | No | Yes | Yes (85) | No |
| `plane-detection` / `mesh-detection` | Yes / Yes | No | Unknown | Plane 147 / No | No |
| `depth-sensing` | Yes | No | Yes (stereo, two depth maps) | Yes (90) | No |
| `light-estimation` | Yes (BCD only) | No | Yes | Yes (90) | No |
| `dom-overlay` | Unknown | No | Unknown | Yes (83) | No |
| `hand-tracking` | Yes | Yes, with a permission prompt | Yes, **primary input** | No hand source | No |
| Controllers (`xr-standard`) | Yes | No controllers | Gamepads module | n/a (touch = `screen`) | No |
| `transient-pointer` | Unknown | Yes, **primary input** (gaze + pinch) | Unknown | No | No |
| `layers` | Yes, default on; Media Layers too | Texture-array projection layers in Safari 27.0; 26.x default unconfirmed | Unknown (Chrome 147) | Yes (147) | No |
| WebGPU in WebXR | Experimental (Browser 146+) | Yes (Safari 26.2) | Unknown | No | No |
| Frame-rate API / `fixedFoveation` | Yes / Yes | Unknown / Unknown | No / No | No / No | No |
| 3D fallback | n/a | `<model>` (Safari 26.0), Quick Look | `<model-viewer>` | `<model-viewer>` (`scene-viewer`) | `<model-viewer>` `quick-look`, `<a rel="ar">`, `<model>` from Safari 27.0 |

Sources:
- **Quest:** https://developers.meta.com/horizon/release-notes/web/ , https://developers.meta.com/horizon/documentation/web/webxr-mixed-reality/ , https://developers.meta.com/vr/documentation/web/webxr-hands/
- **visionOS:** https://webkit.org/blog/15865/webkit-features-in-safari-18-0/ , https://webkit.org/blog/15162/introducing-natural-input-for-webxr-in-apple-vision-pro/ , https://webkit.org/blog/17640/webkit-features-for-safari-26-2/ , https://webkit.org/blog/18325/webkit-features-for-safari-27-0/ , https://developer.apple.com/forums/thread/756850
- **Android XR:** https://developer.android.com/develop/xr/develop-with-webxr
- **Chrome phones:** chromestatus entries for each feature (for example https://chromestatus.com/feature/5450241148977152 for the AR module) and https://developers.google.com/ar/develop/webxr/requirements
- **iOS:** WebKit's `PlatformEnableCocoa.h` enables WebXR only for `PLATFORM(VISION)`, and the Safari 26–27 release posts announce no iOS WebXR.

Rows marked "Unknown" are not documented by the vendor. Feature-detect them and never require them.

## 3. Per-device notes

### Meta Quest Browser
- The version scheme jumped from 42.x to the Chromium milestone (144, 146, 149, 150 in 2026). **Version-compare logic written against `OculusBrowser/3x–4x` is now wrong.**
- The UA contains `Linux`, `Chrome` and `Quest 3`, so Android/Chrome sniffing misclassifies it. Meta says not to use the UA for feature detection.
- The 2D window defaults to 1280×670 and is resizable. Jank on the 2D page before `requestSession` reads as "slow to enter".
- In `immersive-ar` (passthrough) the page has no pixel access to the camera, and you must render on a transparent clear.
- The release notes through 150.1 document **no WebXR removals**. New items are WebGPU depth projection (146), WebGPU space-warp layers (149.1) and WebGPU foveation (150.1, experimental).

Sources: https://developers.meta.com/horizon/documentation/web/browser-specs/ , https://developers.meta.com/horizon/release-notes/web/

### Apple Vision Pro (Safari on visionOS)
- Only `immersive-vr`. `isSessionSupported('immersive-ar')` is false. An "AR Module" flag appeared in visionOS 26.5 without working, and was removed in 27.
- **Feature descriptors WebKit recognizes:** `viewer`, `local`, `local-floor`, `bounded-floor`, `unbounded`, `hand-tracking`, `webgpu`, `layers` (`hit-test` exists but is off). **Any other descriptor in `requiredFeatures` rejects the session.** That includes `anchors`, `depth-sensing`, `dom-overlay`, `plane-detection` and `light-estimation`. In `optionalFeatures` they are ignored.
- `hand-tracking` always shows a consent prompt.
  - three.js stopped requesting it by default in r161/r162, because the extra prompts annoyed visionOS users.
  - In the visionOS Simulator, `requiredFeatures: ['hand-tracking']` fails with "XR Not Allowed". Keep it optional.
- Users can always leave through a system gesture (Digital Crown). Handle the session `end` event and provide in-page exit UI too.
- **Lockdown Mode disables WebXR.**
- Don't UA-sniff for visionOS. Its UA looks like iPad/Mac Safari. Feature-detect `navigator.xr` + `isSessionSupported('immersive-vr')`.
- WebGPU in WebXR: Safari 26.2. Request the `webgpu` feature, then create `new XRGPUBinding(session, device)`.

Sources: https://developer.apple.com/forums/thread/826845 , https://raw.githubusercontent.com/WebKit/WebKit/main/Source/WebCore/platform/xr/PlatformXR.h , https://github.com/mrdoob/three.js/issues/27698 , https://webkit.org/blog/17640/webkit-features-for-safari-26-2/

### Android XR (Chrome)
- Hand input is the **default input**. Design hand-first and fall back to gamepads on controller devices.
- `pose.views` returns two views, and depth sensing is stereo: `frame.getDepthInformation(view)` per eye. A valid viewer pose is required before depth data is available.
- Permissions are asked **one at a time, per feature, and cached per domain**. Switching domains prompts again. Always handle denial.
- The only documented session mode is `immersive-ar`. Don't assume `immersive-vr` without `isSessionSupported`.

Source: https://developer.android.com/develop/xr/develop-with-webxr

### Chrome on ARCore phones (handheld AR)
- Requirements: an ARCore-certified device, **Google Play Services for AR**, and a secure context. The Android Emulator is not supported.
- Touch input arrives as short-lived input sources with `targetRayMode: 'screen'`. Listen for `select*` events. Don't wait for persistent controllers.
- DOM Overlay (`optionalFeatures: ['dom-overlay'], domOverlay: { root }`) is the way to show HTML UI in phone AR. Call `preventDefault()` on `beforexrselect` so that tapping a button does not also place an object.
- Not shipped in Chrome: the frame-rate API and `fixedFoveation`.

Sources: https://developers.google.com/ar/develop/webxr/requirements , https://immersive-web.github.io/dom-overlays/

### iOS / iPadOS Safari
- There is **no WebXR**. Chrome and Firefox on iOS use WebKit as well, so they don't have it either. Don't show an "Enter AR" button that relies on WebXR.
- Fallbacks, from least to most code:
  1. `<a rel="ar" href="model.usdz"><img …></a>` for AR Quick Look.
  2. `<model-viewer src="m.glb" ios-src="m.usdz" ar ar-modes="webxr scene-viewer quick-look">`, one tag for every platform. Supply `ios-src` for animated models, because the on-the-fly USDZ conversion drops animation.
  3. `<model>` on Safari 27.0+, for iOS, iPadOS and macOS (visionOS since 26.0).

Sources: https://developer.apple.com/augmented-reality/quick-look/ , https://modelviewer.dev/docs/index.html , https://webkit.org/blog/18325/webkit-features-for-safari-27-0/

## 4. Detection and session setup (all devices)

- WebXR is `[SecureContext]`. It needs HTTPS or `localhost`.
- `requestSession` needs **transient user activation**. Call it synchronously inside the click handler.
- A cross-origin iframe needs `allow="xr-spatial-tracking"`. When the policy blocks it, `isSessionSupported` and `requestSession` reject with `SecurityError`.
- Put **only** what the experience cannot run without in `requiredFeatures`, usually nothing beyond the reference space. An unsupported or unrecognized required feature rejects the session. Unsupported optional ones are ignored.
- After the session starts, read `session.enabledFeatures` (Chrome 111+, Quest 31.2+, WebKit) to see what was granted. Don't probe objects.
- Request `local-floor` as optional and fall back to `local`. `requestReferenceSpace` only works for spaces granted at creation.
- Treat `isSessionSupported` as advisory. Wrap it in try/catch.

```js
export async function pickMode() {
  if (!('xr' in navigator)) return null;                 // iOS, insecure context
  for (const mode of ['immersive-ar', 'immersive-vr']) {
    try { if (await navigator.xr.isSessionSupported(mode)) return mode; }
    catch { /* SecurityError: blocked by Permissions-Policy */ }
  }
  return null;                                           // show the <model-viewer> fallback
}

// Call synchronously from the click handler.
export async function enter(mode) {
  const session = await navigator.xr.requestSession(mode, {
    optionalFeatures: ['local-floor', 'hand-tracking', 'layers', 'hit-test', 'anchors'],
  });
  const granted = new Set(session.enabledFeatures ?? []);
  const space = await session.requestReferenceSpace(granted.has('local-floor') ? 'local-floor' : 'local');
  return { session, space, granted };
}
```

Sources: https://immersive-web.github.io/webxr/ (`isSessionSupported`, `requiredFeatures`, `enabledFeatures`), https://developer.mozilla.org/en-US/docs/Web/API/XRSystem/requestSession , https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Permissions-Policy/xr-spatial-tracking

## 5. Session lifecycle states that look like performance bugs

- **`visibilityState`**:
  - `visible-blurred` happens when system UI is over the scene. rAF may be throttled and input is **not** processed, so a held "select" looks stuck.
  - `hidden` means no rAF at all.

  Listen to `visibilitychange`, pause audio and heavy logic, and reset interaction state when it returns to `visible`.
- **`reset` event on `XRReferenceSpace`**: the origin jumped (recalibration, tracking recovery, new bounds). Re-place content, or it visibly jumps.
- **Recentering**: a page cannot trigger a system recenter. Implement an app-level offset with `refSpace.getOffsetReferenceSpace(new XRRigidTransform(...))`.
- **`unbounded`** spaces drift. Keep content within about 15 m of the origin for `local` / `local-floor`.

Sources: https://www.w3.org/TR/webxr/#xrvisibilitystate-enum , https://immersive-web.github.io/webxr/ (reference spaces, `reset`)
