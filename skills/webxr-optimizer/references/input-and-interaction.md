# Input and Interaction Across Devices

Most "it works on Quest but not on Vision Pro or my phone" bugs come from input. Each device delivers input through a different `targetRayMode`, and code that assumes two persistent controllers at indices 0 and 1 breaks everywhere except Quest.

## 1. Target ray modes

| `targetRayMode` | Device | Lifetime | Ray origin |
|---|---|---|---|
| `tracked-pointer` | Quest controllers, tracked hands (Quest, Android XR, Vision Pro with `hand-tracking`) | Persistent while tracked | Controller tip / outstretched index finger |
| `transient-pointer` | **Vision Pro** gaze + pinch | **Exists only during the pinch** | Gaze at pinch start, then moved by the hand |
| `screen` | Phone touch in handheld AR | Exists only during the touch | Camera through the touch point |
| `gaze` | Headsets with no other input | Persistent | Head forward |

Source: https://immersive-web.github.io/webxr/#xrtargetraymode-enum

Rules that work on every device:
1. **Iterate over all of `session.inputSources` every frame.** Never hard-code indices, and never cache an `XRInputSource` across frames. Key state by the object itself, for example in a `Map`.
2. **Drive actions from `selectstart` / `select` / `selectend`** (and `squeeze*`) on the session. Don't poll gamepad buttons only, because transient and screen inputs have no `gamepad`.
3. **Raycast with `targetRaySpace`. Attach held or dragged objects to `gripSpace`.** On Vision Pro, `targetRaySpace` starts between the eyes. An object attached to it lands on the user's face.
4. **Reset smoothing on `inputsourceschange`.** Each pinch or touch is a *new* input source. Interpolating from the previous ray causes visible lag.
5. **Handle `visible-blurred`**: input is not processed, so cancel drags when it happens.

## 2. Apple Vision Pro: transient-pointer

- `inputSources` is **empty** until the user pinches. The pinch fires `inputsourceschange` (added), then `selectstart`. Release fires `select`, `selectend`, then `inputsourceschange` (removed).
- If `hand-tracking` was requested and granted, **indices 0 and 1 are the two hands** (`tracked-pointer`, joint data only, **no select events**). **The pinch pointers then sit at indices 2 and 3.**
- Gaze is revealed only at the moment of the pinch, and the hand position only while pinching, unless hand tracking was granted.

Source: https://webkit.org/blog/15162/introducing-natural-input-for-webxr-in-apple-vision-pro/

**three.js trap (verified in `WebXRManager.js`, r186/dev):**
- three.js has no `transient-pointer` handling.
- It assigns an input source only to controller slots the app already created with `getController(i)` / `getControllerGrip(i)`, and it **drops `select*` events from input sources without a slot**.
- So an app that creates only controllers 0 and 1 **ignores every pinch** on Vision Pro once hand tracking is granted.

Fix it by creating four slots, or by listening to the session directly:

```js
for (let i = 0; i < 4; i++) {
  const ray = renderer.xr.getController(i);       // targetRaySpace
  ray.addEventListener('selectstart', onSelectStart);
  ray.addEventListener('selectend', onSelectEnd);
  scene.add(ray, renderer.xr.getControllerGrip(i)); // gripSpace: attach held objects here
}
```

Source: https://raw.githubusercontent.com/mrdoob/three.js/dev/src/renderers/webxr/WebXRManager.js

**`@react-three/xr` v6** handles this for you:
- It maps `transient-pointer` → `transientPointer`, `screen` → `screenInput`, plus gaze, controller and hand inputs.
- Each can be configured or disabled in `createXRStore({ controller, hand, transientPointer, gaze, screenInput })`.
- Its default session init leaves `hand-tracking` **off** on Apple Vision Pro. It detects the device with `userAgent.includes('Macintosh') && navigator.xr`, a heuristic that also matches desktop Chrome on macOS.

Source: `@pmndrs/xr` 6.6.31 `dist/init.js`, `dist/input.js`, `dist/misc.js`

## 3. Hands (Quest, Android XR, Vision Pro)

- `inputSource.hand` is an `XRHand` with **25 joints**. It is `null` unless `hand-tracking` was granted.
- Access joints by name with `hand.get('index-finger-tip')`. The old numeric constants (`XRHand.INDEX_FINGER_TIP`, `hand[XRHand.WRIST]`) were removed from the spec.
- Per frame, use `frame.fillPoses(spaces, baseSpace, float32Array)` and `frame.fillJointRadii(...)`. Bulk calls are cheaper than 50 separate `getJointPose` calls.
- **three.js r162+** no longer requests hand tracking by default. Opt in with `VRButton.createButton(renderer, { optionalFeatures: ['hand-tracking'] })`.
- **Quest**: palm pinch on both hands is reserved by the system. Left palm pinch opens the menu and **exits the WebXR session**.
- **Android XR**: hands are the default input, so build pinch and poke affordances first.

Sources: https://immersive-web.github.io/webxr-hand-input/ , https://github.com/mrdoob/three.js/wiki/Migration-Guide , https://developers.meta.com/vr/documentation/web/webxr-hands/ , https://developer.android.com/develop/xr/develop-with-webxr

## 4. Controllers (Quest) and gamepad mapping

- `gamepad.mapping === 'xr-standard'` requires a `tracked-pointer` with a `gripSpace`.
  - Buttons: `buttons[0]` trigger, `[1]` squeeze, `[2]` touchpad, `[3]` thumbstick.
  - Axes: `axes[0..1]` touchpad, `axes[2..3]` thumbstick.
  - Missing inputs keep their index.
- `gamepad.id` is intentionally empty. Identify the controller through `inputSource.profiles` (WebXR Input Profiles).
- `XRControllerModelFactory` (three.js) and `@react-three/xr` load controller and hand models **from jsDelivr at runtime** (`@webxr-input-profiles/assets@1.0`). For offline or restricted networks, self-host them: use `setPath` on the factory, or `createXRStore({ baseAssetPath })`.

Sources: https://immersive-web.github.io/webxr-gamepads-module/ , three.js r186 `examples/jsm/webxr/XRControllerModelFactory.js`

## 5. Phones: screen input and DOM Overlay

- A tap creates a short-lived `screen` input source. Hit-test from its `targetRaySpace` on `select`.
- For HTML UI in phone AR, use `dom-overlay`.
- Call `preventDefault()` on the overlay's `beforexrselect` event, so that tapping a button does not also fire `select` into the scene.

Source: https://immersive-web.github.io/dom-overlays/

## 6. UI inside the headset

- DOM is **not** visible inside headset sessions. This includes drei `<Html>`, `stats.js` and HTML menus.
- Build in-scene UI instead: `@react-three/uikit` (pmndrs, maintained), a `CanvasTexture` panel, or a WebXR quad layer for crisp text.
- `three-mesh-ui` has been unmaintained since 2023.
- drei `OrbitControls`, `CameraControls` and similar fight the XR camera. Unmount them during the session with `<IfInSessionMode deny={['immersive-vr','immersive-ar']}>`.

Source: https://github.com/pmndrs/xr/blob/main/docs/getting-started/faq.md
