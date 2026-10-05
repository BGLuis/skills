# Deprecated and Removed APIs

Most broken WebXR code was copied from a tutorial written against an API that no longer exists. Run `scripts/scan_deprecated.py` first. It flags the mechanical cases in this file, with `file:line`. Then read the matching section below for the replacement.

**Gate every finding by the installed version.** Read `three` and `@react-three/xr` from `package.json` or the lockfile. Something "removed in r162" only breaks a project on r162+. Below that it is a migration to schedule. Versions checked on 2026-10-05:
- `three` 0.186.1 (r186)
- `@react-three/xr` 6.6.31
- `@react-three/fiber` 9.8.1 (v10 is alpha/canary only, so don't migrate to it)
- `@react-three/drei` 10.7.9

Sources: https://github.com/mrdoob/three.js/wiki/Migration-Guide (and diffs of the published `three@0.NNN.0` packages on unpkg), https://github.com/pmndrs/xr/blob/main/docs/migration/from-react-three-xr-5.md , npm registry.

## 1. WebVR (removed from every browser)

| Old | Replacement |
|---|---|
| `navigator.getVRDisplays()`, `VRDisplay`, `VRFrameData`, `VRPose`, `VRLayerInit` | `navigator.xr.isSessionSupported()` + `navigator.xr.requestSession()` |
| `display.requestPresent()` / `exitPresent()` | `requestSession(mode)` / `session.end()` |
| `display.requestAnimationFrame` + `submitFrame()` | `session.requestAnimationFrame()`; the frame is submitted when the callback returns |
| `getFrameData()` | `frame.getViewerPose(refSpace)` → `XRViewerPose.views` |
| `stageParameters` | `XRBoundedReferenceSpace.boundsGeometry` |
| `vrdisplaypresentchange` | `XRSession` `end` event |
| `navigator.getGamepads()` for controller pose | `session.inputSources` + `frame.getPose(inputSource.gripSpace, refSpace)` |
| `webvr-polyfill` | Native WebXR |

Chrome deprecated WebVR 1.1 in Chrome 77, with removal planned for 79–80. WebXR also never enumerates devices: there is no device list, to prevent fingerprinting. Sources: https://github.com/immersive-web/webxr/blob/main/webvr-migration.md , https://developer.chrome.com/blog/chrome-77-deps-rems , https://developer.mozilla.org/en-US/docs/Web/API/Navigator/getVRDisplays

## 2. Early WebXR drafts (2018–2019 tutorials, old polyfills)

| Old | Replacement | Spec change |
|---|---|---|
| `navigator.xr.requestDevice()`, `XRDevice` | `navigator.xr.requestSession(mode)`; there is no device object | 2018-10, commit 75164fc |
| `supportsSession()`, `supportsSessionMode()` | `isSessionSupported(mode)`, which resolves to a boolean | 2019-09. Chrome planned the `supportsSession` removal for 135 (chromestatus 5114816316047360) |
| `requestSession({ immersive: true })`, `{ exclusive: true }` | `requestSession('immersive-vr' \| 'immersive-ar' \| 'inline', { requiredFeatures, optionalFeatures })` | 2018-10 |
| `XRPresentationContext`, `outputContext`, `XRSessionCreationOptions` | `XRSessionInit` + `session.updateRenderState({ baseLayer })` | 2019 |
| `session.baseLayer = layer` | `session.updateRenderState({ baseLayer: new XRWebGLLayer(session, gl) })`; read it from `session.renderState.baseLayer` | 2019-01 |
| `requestFrameOfReference('eye-level' \| 'stage' \| 'head-model')`, `XRFrameOfReference`, `XRCoordinateSystem` | `session.requestReferenceSpace('local' \| 'local-floor' \| 'bounded-floor' \| 'unbounded' \| 'viewer')` | 2018-11 / 2019-05 |
| Reference spaces `{type:'stationary', subtype:'eye-level' \| 'floor-level'}`, `'bounded'` | `'local'`, `'local-floor'`, `'bounded-floor'` | 2019-05, commit 8812f40 |
| `getDevicePose()`, `XRDevicePose`, `pose.viewMatrix`, `getViewMatrix()` | `frame.getViewerPose(refSpace)`, `view.transform.inverse.matrix`, `view.projectionMatrix` | 2018–2019 |
| `getInputPose()`, `XRInputPose`, `pointerMatrix` | `frame.getPose(inputSource.targetRaySpace \| gripSpace, refSpace)` | 2019-01 |
| `setCompatibleXRDevice()` | `await gl.makeXRCompatible()`; the `{ xrCompatible: true }` context attribute is discouraged as "slow synchronous behavior" | spec |
| `XRWebGLLayer.requestViewportScaling()` | `view.requestViewportScale(scale)` | 2019 |
| `session` `blur` / `focus` events | `visibilitychange` + `session.visibilityState` | 2019-06 |
| `XRHand.WRIST`, `XRHand.INDEX_FINGER_TIP` and similar constants, `hand[index]` | String joint names via the maplike: `hand.get('wrist')`, `hand.get('index-finger-tip')` | 2020-12 |

`webxr-polyfill` is effectively unmaintained: its last npm release is 2.0.3 (2020), and it still advertises a WebVR fallback that no browser ships. Don't add it to Quest, Vision Pro or Android XR projects.

Sources: https://github.com/immersive-web/webxr/commits/main (commits cited above), https://immersive-web.github.io/webxr/ "Changes" section, https://github.com/immersive-web/webxr-hand-input/commit/5cab8f9

### Depth sensing churn (2024–2026, spec level)

The changes:
- `formatPreference` became `dataFormatPreference`.
- The `"unsigned-int"` format became `"unsigned-short"`.
- `depthNear` and `depthFar` were **removed** from `XRDepthInformation`, in favor of the view's projection.
- `depthType` (`'raw'` / `'smooth'`), `depthActive`, `pauseDepthSensing()` and `resumeDepthSensing()` were added. They are in Chrome 139+ and Quest 33.3+.

Browser rollout per field varies, so feature-detect each property. Source: https://github.com/immersive-web/depth-sensing/commits/main , https://chromestatus.com/feature/5074096916004864

## 3. three.js

Each row lists the old API, its replacement, and when it was deprecated and removed.

### WebXR

| Old | Replacement | Deprecated → removed |
|---|---|---|
| `renderer.vr.enabled`, `renderer.vr.setDevice()` | `renderer.xr.enabled = true` | removed **r112** |
| `WEBVR.createButton()`, `examples/js/vr/WebVR.js` | `VRButton.createButton(renderer)` from `three/addons/webxr/VRButton.js` | removed r112 |
| `ViveController`, `DaydreamController`, `GearVRController` | `renderer.xr.getController(i)` + `XRControllerModelFactory` | r94–r111 |
| `VRButton.createButton(renderer, { referenceSpaceType })` | `renderer.xr.setReferenceSpaceType(...)`; the second argument is now an `XRSessionInit` | r116 |
| `renderer.xr.getCamera(camera)` | `renderer.xr.getCamera()` (no argument; returns the `ArrayCamera`) | r129 |
| `window.requestAnimationFrame(render)` as the XR loop | `renderer.setAnimationLoop(render)` (renamed from `animate()` in r93) | — |
| Hand tracking assumed without being requested | `VRButton.createButton(renderer, { optionalFeatures: ['hand-tracking'] })` | not default since **r162** |

### Renderer, color and lighting

| Old | Replacement | Deprecated → removed |
|---|---|---|
| `WebGL1Renderer`, WebGL 1 contexts | `WebGLRenderer` (WebGL 2 only) | r153 → **r163** |
| `renderer.outputEncoding`, `sRGBEncoding`, `LinearEncoding`, `texture.encoding` | `renderer.outputColorSpace = SRGBColorSpace`, `texture.colorSpace = SRGBColorSpace` (color maps) or `NoColorSpace` (data maps) | r152 → **r162** |
| `GammaEncoding`, `RGBEEncoding`, `RGBM7/16Encoding`, `gammaOutput`, `gammaFactor` | Color management, HDR loaders | removed r112–r136 |
| `renderer.physicallyCorrectLights` | Delete it; physically correct lighting is the default | r150 → **r160** |
| `renderer.useLegacyLights` | Delete it | r155 → **r165** |
| `WebGLMultisampleRenderTarget` | `new WebGLRenderTarget(w, h, { samples: 4 })` | removed r138 |
| `WebGLMultipleRenderTargets` | `WebGLRenderTarget` with `count` | r162 |
| `PCFSoftShadowMap` | `PCFShadowMap` (now soft) | deprecated r182 |
| `MeshGouraudMaterial` | `MeshLambertMaterial` | deprecated r173 |
| `Clock` | `Timer` (in core since r179) | deprecated r183 |

### Geometry and utilities

| Old | Replacement | Deprecated → removed |
|---|---|---|
| `new THREE.Geometry()`, `Face3` | `BufferGeometry` | removed r125 / r126 |
| `BufferGeometryUtils.mergeBufferGeometries()` | `mergeGeometries()` | r151 → **r161** |
| `mergeBufferAttributes()` | `mergeAttributes()` | r151 |
| `THREE.Math` | `THREE.MathUtils` | r113 |
| `ImageUtils.loadTexture()` | `new TextureLoader().load()` | removed r89 |
| `uv2` attribute | `uv1` + `material.aoMap.channel = 1` | r151–r152 |

### Loaders and modules

| Old | Replacement | Deprecated → removed |
|---|---|---|
| `BasisTextureLoader` | `KTX2Loader` | r137 → r150 |
| `RGBELoader` | `HDRLoader` | renamed r180 |
| `KTX2Loader.detectSupportAsync()` | `detectSupport(renderer)` after `await renderer.init()` | deprecated r181 |
| `DRACOLoader.setDecoderConfig()` | Nothing (WASM only) | deprecated r185 |
| `examples/js/*`, `build/three.js`, `build/three.min.js` | ES modules: `import … from 'three'` and `three/addons/...` | r148 / r161 |
| `three/examples/jsm/...` imports | `three/addons/...` (alias since r144) | **Info only.** It is still exported in r186, so it is style, not breakage |

### WebGPURenderer

| Old | Replacement | Deprecated → removed |
|---|---|---|
| `renderAsync()`, `computeAsync()`, `clearAsync()`, `initTextureAsync()`, `hasFeatureAsync()` | Sync versions after `await renderer.init()` | deprecated r181 |
| `PostProcessing` (from `three/webgpu`) | `RenderPipeline` | r183 |

### Still current in r186: do not flag
- `renderer.xr.*`: `setFoveation`, `setFramebufferScaleFactor`, `setReferenceSpaceType`, `getController`, `getControllerGrip`, `getHand`, `getCamera()`, `getSession`.
- `VRButton`, `ARButton` and `XRButton` from `three/addons/webxr/`.
- `XRControllerModelFactory`, `XRHandModelFactory`, `OculusHandModel`.
- `GLTFLoader.setKTX2Loader`, `setMeshoptDecoder`, `setDRACOLoader`.
- `renderer.setAnimationLoop`.

## 4. @react-three/xr v5 → v6

v6 (2024-07) still ships a compatibility layer, so some old names **still work but are deprecated**. Others are **gone** and fail at import time.

### Removed (breaks)

| v5 or earlier | v6 replacement |
|---|---|
| `VRCanvas`, `ARCanvas`, `XRCanvas`, `DefaultXRControllers` | `<Canvas><XR store={store}>…</XR></Canvas>` |
| `<Controllers />`, `<Hands />` | Nothing to add: `<XR>` renders controllers, hands, transient pointers, gaze and screen input by default. Configure them with `createXRStore({ controller, hand, transientPointer, gaze, screenInput })` |
| `useController('left')` | `useXRInputSourceState('controller', 'left')` |
| `useHitTest(cb)` | `useXRHitTest(fn, relativeTo, trackableType)` / `<XRHitTest>` |
| `useTeleportation`, `TeleportationPlane` | `createXRStore({ controller: { teleportPointer: true } })` + `<XROrigin>` + `<TeleportTarget onTeleport>` |
| `Ray` | Built-in ray pointer of the default controller or hand |
| `startSession`, `stopSession`, `toggleSession` | `store.enterVR()`, `store.enterAR()`, `store.enterXR(mode)`, `store.getState().session?.end()` |
| `<XR foveation frameRate referenceSpace onSessionStart onSessionEnd …>` props | `createXRStore({ foveation, frameRate, frameBufferScaling, … })`, `store.onSessionEnd(cb)`. The origin is `local-floor` by default; move it with `<XROrigin>` |
| `XRButton` `sessionInit` prop | Store options `hitTest`, `anchors`, `planeDetection`, `meshDetection`, `depthSensing`, `handTracking`, `layers`, `domOverlay`, `bounded`, `customSessionInit` |
| `useXR()` returning `{ isPresenting, player, controllers, isHandTracking }` | `useXR(s => s.session != null)`, `<XROrigin>` / `s.origin`, `useXRInputSourceStates()` |

### Deprecated (still works, migrate)

| v5 or earlier | v6 replacement |
|---|---|
| `VRButton`, `ARButton`, `XRButton` (from `@react-three/xr`) | `<button onClick={() => store.enterVR()}>` (or `enterAR()` / `enterXR()`) |
| `Interactive`, `useInteraction` | R3F pointer events: `onClick`, `onPointerDown`, `onPointerEnter`, … |
| `RayGrab` | `@react-three/handle` |
| `useXREvent` | `useXRInputSourceEvent` or R3F events |
| `useXRHandState`, `useXRControllerState`, `useXRTransientPointerState`, `useXRGazeState`, `useXRScreenInputState` | `useXRInputSourceState(type, handedness)` |
| `useXRReferenceSpace` | `useXRSpace(type)` |
| `useSessionModeSupported`, `useSessionFeatureEnabled` | `useXRSessionModeSupported`, `useXRSessionFeatureEnabled` |
| `<XRHandJoint joint="wrist">` | `<XRSpace space="wrist">` |

Defaults worth tuning in v6 (`@pmndrs/xr` `init.js`):
- **Session features.** v6 requests `anchors`, `layers`, `mesh-detection`, `plane-detection`, `hit-test` and `dom-overlay` as optional features. It also requests `hand-tracking`, except on Vision Pro. Turn off the ones you don't use (`createXRStore({ planeDetection: false, meshDetection: false, … })`), since each one can mean a permission prompt or runtime work.
- **Emulation and session offer.** `emulate` injects IWER on localhost, and `offerSession` defaults to `true`.

Sources: https://github.com/pmndrs/xr/blob/main/docs/migration/from-react-three-xr-5.md , `@react-three/xr` 6.6.31 `dist/deprecated/*.d.ts` and `dist/index.d.ts`

## 5. Other libraries

| Library | Status | Use instead |
|---|---|---|
| `webxr-polyfill` | Unmaintained (2.0.3, 2020) | Native WebXR. IWER for desktop testing |
| `three-mesh-ui` | Unmaintained (last release 2023) | `@react-three/uikit`, a `CanvasTexture` panel, or a WebXR quad layer |
| `three-stdlib` | Maintained, but lags `three/addons`, with no r173+ XR changes | `three/addons/...` for XR code |
| `@webxr-input-profiles/motion-controllers` | 1.0.0 (2020). three vendors its own copy | Only needed outside `XRControllerModelFactory` |
| Immersive Web Emulator extension, Mozilla WebXR API Emulator | Archived | IWER (see `testing-and-debugging.md`) |
| drei `<Html>`, `OrbitControls`, `CameraControls` | Not XR-aware | See `input-and-interaction.md` §6 |
