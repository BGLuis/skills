# WebXR Review Checklist

Audit in this order. Earlier items are cheaper to find and break more users. For each finding, report the rule, the evidence (`file:line` or the measured number) and the reference section that justifies it.

## 1. Breakage (does it run at all?)

- [ ] `python3 scripts/scan_deprecated.py <src>` reports nothing in the *removed* categories (`webvr-*`, `webxr-*`, `three-*`, `r3f-xr-removed`), gated by the installed `three` and `@react-three/xr` versions (`deprecated-apis.md`).
- [ ] Served over HTTPS or `localhost`; iframes carry `allow="xr-spatial-tracking"` (`devices-and-browsers.md` §4).
- [ ] `requestSession` is called synchronously from a user click, never after awaits or timers.
- [ ] `requiredFeatures` holds only what the app cannot run without. Everything else is optional, and the code checks `session.enabledFeatures`.
- [ ] `isSessionSupported` is wrapped in try/catch. With no WebXR (iOS), a fallback is shown (`<model-viewer>`, Quick Look, `<model>`).
- [ ] The render loop is `renderer.setAnimationLoop` or `session.requestAnimationFrame`, never window rAF.

## 2. Cross-device behavior

- [ ] Input iterates over all `inputSources` and uses `select*` events. There are no fixed indices, and three.js has controller slots 0–3 (`input-and-interaction.md` §1–2).
- [ ] Held objects attach to `gripSpace`; raycasts use `targetRaySpace`.
- [ ] Hand tracking is requested explicitly as optional (three r162+), and nothing breaks when it is denied.
- [ ] There is a working path for every target: Quest (controllers and hands), Vision Pro (`immersive-vr` only, transient-pointer), Android XR (hands first) and phones (`screen` taps, DOM Overlay).
- [ ] No UA sniffing to decide features. The Quest UA version jumped from 42 to 144, and Vision Pro reports a Mac/iPad UA.
- [ ] `visibilitychange`, `end` and the reference-space `reset` events are handled.
- [ ] No DOM UI inside the headset (drei `<Html>`, stats overlays). Camera controls are unmounted during the session.

## 3. Performance (measured on a headset)

- [ ] A frame-time number on the target device and refresh rate exists, with no stale frames in normal use (`budgets-and-profiling.md`).
- [ ] The bottleneck is classified as CPU, vertex or fragment before any change.
- [ ] Foveation is on (three's default is 1.0, so check nobody lowered it). The framebuffer scale is set before the session.
- [ ] The frame rate is one the scene sustains (`frameRate: 'mid'` and similar on heavy scenes in `@react-three/xr`).
- [ ] No full-screen post-processing and no mid-frame render-target switches, since both break FFR and MSAA (`rendering-optimizations.md` §1, §6).
- [ ] The draw-call count is known (`renderer.info.render.calls`). Static meshes are merged, repeated meshes instanced or batched.
- [ ] At most one directional or point light on PBR materials, and no real-time point-light shadows.
- [ ] Textures are KTX2 (ETC1S color, UASTC normals) and geometry is Meshopt/Draco. The transcoder path is set.
- [ ] Shaders are warmed up (`compileAsync`) and textures pre-uploaded (`initTexture`) before entering XR. No allocations in the loop.
- [ ] Video, sky and text panels use WebXR Layers where the device supports them.
- [ ] `@react-three/xr`: the store is at module scope, and unused default features (plane and mesh detection, anchors, hit-test) are turned off.

## 4. Test coverage

- [ ] At least one automated test enters an emulated session with IWER (`installRuntime({ forceInstall: true })`) and drives input (`testing-and-debugging.md` §2).
- [ ] The report states what was verified on real hardware and what was only emulated.
