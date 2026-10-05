# three.js and React Three Fiber in XR

Correct, current setup for the two supported stacks, verified against three r186 and `@react-three/xr` 6.6.31. For *building* R3F XR experiences in depth (store, interactions, teleport, uikit, validation), the pmndrs team ships its own `pmndrs-xr` Agent Skill in https://github.com/pmndrs/xr/tree/main/skills/pmndrs-xr . Use this file for the performance and compatibility side.

## 1. Which renderer

| | `WebGLRenderer` + `WebXRManager` | `WebGPURenderer` + `XRManager` |
|---|---|---|
| Maturity | Production. Every device | XR since r173; native `XRGPUBinding` since **r185** |
| Multiview | **No** | Yes, `new WebGPURenderer({ multiview: true })`, but **only on the WebGL backend** (`OVR_multiview2`). The WebGPU backend warns and disables it |
| Layers | Projection layer automatically (`getBaseLayer()` returns an `XRProjectionLayer` when Layers are supported) | Also `renderer.xr.createQuadLayer(...)` / `createCylinderLayer(...)` |
| WebGPU in XR | n/a | Vision Pro (Safari 26.2+); Quest experimental (Browser 146+); not in Chrome |

**Recommendation:**
- Use `WebGLRenderer` unless you need TSL/WebGPU features or multiview.
- If you use `WebGPURenderer`, request `optionalFeatures: ['webgpu']` and install `setupWebGLXRFallback` from `three/addons/webxr/WebGLXRFallback.js`. It switches to a WebGL-backend renderer when the browser has no `XRGPUBinding`.

Sources: three.js r186 `src/renderers/common/XRManager.js`, `src/renderers/common/Renderer.js`, `examples/webgpu_xr_cubes.html`, `examples/jsm/webxr/WebGLXRFallback.js`; https://github.com/mrdoob/three.js/pull/30346

## 2. three.js setup that avoids the usual traps

```js
import * as THREE from 'three';
import { VRButton } from 'three/addons/webxr/VRButton.js';

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(innerWidth, innerHeight);
renderer.xr.enabled = true;
renderer.xr.setReferenceSpaceType('local-floor');   // default; must be set before the session
renderer.xr.setFramebufferScaleFactor(1.0);         // before the session; lower it if fragment bound
renderer.xr.setFoveation(1.0);                      // default; 0 = off, 1 = max
document.body.appendChild(VRButton.createButton(renderer, { optionalFeatures: ['hand-tracking'] }));

for (let i = 0; i < 4; i++) {                       // 4 slots: Vision Pro pinches arrive at index 2-3
  scene.add(renderer.xr.getController(i), renderer.xr.getControllerGrip(i));
}

await renderer.compileAsync(scene, camera);         // avoid shader-compile hitches after entering

renderer.setAnimationLoop((time, frame) => {         // never window.requestAnimationFrame
  renderer.render(scene, camera);                   // three swaps in the per-eye XR camera
});
```

Defaults in `WebXRManager` (r186):
- `framebufferScaleFactor` 1.0
- `referenceSpaceType` `'local-floor'`
- `foveation` 1.0

`VRButton` and `XRButton` request `local-floor`, `bounded-floor` and `layers` as optional features by default. `ARButton` also requests `dom-overlay`.

Rules:
- **Don't move `camera` during a session.** WebXR owns the head pose. Put the camera in a `Group` (a "rig" or "dolly") and move the group for locomotion.
- **Change scale factor and reference space before entering.** Both are ignored, with a warning, while presenting.
- **Post-processing via `EffectComposer` renders into intermediate targets.** That disables foveation and, on Quest, costs a full-resolution pass per eye. See `rendering-optimizations.md` §6.
- **Color**: set `renderer.outputColorSpace = THREE.SRGBColorSpace` (the default) and `texture.colorSpace` for color textures. The old `encoding` API is gone (r162).

Source: three.js r186 `src/renderers/webxr/WebXRManager.js`, `examples/jsm/webxr/VRButton.js`; https://threejs.org/docs/#manual/en/introduction/How-to-create-VR-content

## 3. React Three Fiber + `@react-three/xr` v6 setup

```tsx
import { Canvas } from '@react-three/fiber';
import { XR, createXRStore, IfInSessionMode } from '@react-three/xr';
import { OrbitControls } from '@react-three/drei';

const store = createXRStore({
  foveation: 1,              // 0..1; undefined = browser default
  frameRate: 'mid',          // 'high' (default) | 'mid' | 'low' | false; Quest only
  frameBufferScaling: 1,     // 'high' | 'mid' | 'low' | number
  planeDetection: false,     // v6 requests several features by default: turn off what you don't use
  meshDetection: false,
  anchors: false,
  hitTest: false,
});

export function App() {
  return (
    <>
      <button onClick={() => store.enterVR()}>Enter VR</button>
      <Canvas>
        <XR store={store}>
          <IfInSessionMode deny={['immersive-vr', 'immersive-ar']}>
            <OrbitControls />
          </IfInSessionMode>
          {/* scene */}
        </XR>
      </Canvas>
    </>
  );
}
```

Rules:
- **Create the store once, at module scope.** Creating it during render produces a new store, and a new session offer, on every render.
- **Enter from a real user gesture** with `store.enterVR()` / `store.enterAR()`. `VRButton` / `ARButton` from `@react-three/xr` are deprecated.
- **Keep `frameloop="always"`**, the R3F default. `@react-three/xr`'s layers and events code does not support `"demand"`.
- **Never move the camera.** Move `<XROrigin>` instead.
- **DOM is invisible inside the headset.** That includes drei `<Html>`. Use `@react-three/uikit`, or `XRDomOverlay` for phone AR.
- **The emulator and session offer are on by default.** `emulate` auto-injects IWER on localhost when no WebXR is present, and `offerSession` is on. For automated tests that install IWER themselves, use `createXRStore({ emulate: false, offerSession: false })`.
- **Hand and controller models come from jsDelivr by default.** Set `baseAssetPath` to self-host them.
- **R3F v9 (React 19) no longer converts texture props to sRGB.** Set `texture.colorSpace = THREE.SRGBColorSpace` yourself on textures loaded outside drei/R3F helpers.

Sources: https://github.com/pmndrs/xr/blob/main/docs/tutorials/store.md , https://github.com/pmndrs/xr/blob/main/docs/getting-started/faq.md , https://r3f.docs.pmnd.rs/tutorials/v9-migration-guide , `@pmndrs/xr` 6.6.31 `dist/init.js`, `dist/store.d.ts`

## 4. Version compatibility

- `@react-three/xr` 6.6.x peers: `@react-three/fiber >=8`, `react >=18`, `three *`.
- drei 10 requires R3F ^9 and React ^19.
- R3F **v10 is alpha/canary only** (2026-10). Don't upgrade production XR apps to it.
- `three-stdlib` (used by drei) lags behind `three/addons`. Import XR helpers (`VRButton`, `XRControllerModelFactory`, …) from `three/addons/webxr/`, not from `three-stdlib`.

Source: npm registry (2026-10-05)
