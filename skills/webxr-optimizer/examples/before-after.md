# Before / After Examples

Six common fixes. The rule and source behind each are in `references/`.

## 1. Render loop that freezes in the headset

**Before**: the loop is driven by the window. Inside the headset the view freezes or goes black.
```js
function animate() {
  requestAnimationFrame(animate);
  renderer.render(scene, camera);
}
animate();
```

**After**: the XR session drives the loop. three.js switches between window rAF and the XR session automatically.
```js
renderer.setAnimationLoop(() => renderer.render(scene, camera));
```
Scanner rule `xr-window-raf`. See `references/rendering-optimizations.md` §9.

## 2. `@react-three/xr` v5 → v6

**Before** (v5): breaks on import in v6 (`Controllers` and `Hands` were removed), and the `<XR>` props are ignored.
```tsx
import { VRButton, XR, Controllers, Hands } from '@react-three/xr';

export const App = () => (
  <>
    <VRButton />
    <Canvas>
      <XR foveation={1} referenceSpace="local-floor">
        <Controllers />
        <Hands />
      </XR>
    </Canvas>
  </>
);
```

**After** (v6): the store holds the session options. Controllers and hands render by default.
```tsx
import { XR, createXRStore } from '@react-three/xr';

const store = createXRStore({ foveation: 1, frameRate: 'mid' });

export const App = () => (
  <>
    <button onClick={() => store.enterVR()}>Enter VR</button>
    <Canvas>
      <XR store={store}>{/* scene */}</XR>
    </Canvas>
  </>
);
```
Scanner rules `r3f-xr-removed`, `r3f-xr-deprecated` and `r3f-xr-props`. See `references/deprecated-apis.md` §4.

## 3. Pinch does nothing on Apple Vision Pro

**Before**: works on Quest. On Vision Pro with hand tracking granted, every pinch arrives at input index 2 or 3, and three.js drops events from input sources that have no controller slot.
```js
const c0 = renderer.xr.getController(0);
const c1 = renderer.xr.getController(1);
c0.addEventListener('selectstart', onSelectStart);
c1.addEventListener('selectstart', onSelectStart);
```

**After**:
```js
for (let i = 0; i < 4; i++) {
  const ray = renderer.xr.getController(i);
  ray.addEventListener('selectstart', onSelectStart);
  scene.add(ray, renderer.xr.getControllerGrip(i)); // attach held objects to the grip, not the ray
}
```
Scanner rule `xr-two-controller-slots`. See `references/input-and-interaction.md` §2.

## 4. Session refused on some devices

**Before**: `requestSession` rejects on Vision Pro, because WebKit doesn't recognize `anchors`, and on any device that lacks a required feature.
```js
navigator.xr.requestSession('immersive-vr', {
  requiredFeatures: ['local-floor', 'hand-tracking', 'anchors'],
});
```

**After**: only the essentials are required, and the code asks what was granted.
```js
const session = await navigator.xr.requestSession('immersive-vr', {
  optionalFeatures: ['local-floor', 'hand-tracking', 'anchors', 'layers'],
});
const granted = new Set(session.enabledFeatures ?? []);
const space = await session.requestReferenceSpace(granted.has('local-floor') ? 'local-floor' : 'local');
```
Scanner rule `xr-required-optional-feature`. See `references/devices-and-browsers.md` §4.

## 5. Fragment-bound scene on Quest: what to measure, then change

**Before**:
- OVR Metrics shows App GPU Time around 14 ms at 90 Hz (budget 11.1 ms) and a steady stale-frame count.
- With `setFramebufferScaleFactor(0.01)`, frame time drops a lot. The scene is **fragment bound**.
- The scene draws through `EffectComposer` (bloom). That intermediate target **disables foveation**.

**After**:
```js
renderer.xr.setFoveation(1.0);                 // default; verify nothing lowered it
renderer.xr.setFramebufferScaleFactor(0.9);    // before the session, only if still over budget
renderer.setAnimationLoop(() => renderer.render(scene, camera)); // no composer: FFR applies again
```
Then re-measure on the same headset at the same rate. Report the numbers, for example "App GPU Time 14.1 → 9.8 ms, stale frames 0". Never report this from the emulator. See `references/budgets-and-profiling.md` §2 and `references/rendering-optimizations.md` §1 and §6.

## 6. Heavy PNG textures → KTX2

**Before**: 2048² PNG albedo, normal and roughness maps. Each one is decoded to full RGBA in VRAM. This brings texture-bandwidth stalls and long uploads on entry.

**After**: compress offline, then load the KTX2 textures with the transcoder path set:
```bash
npx @gltf-transform/cli optimize scene.glb scene.opt.glb --compress meshopt --texture-compress ktx2
```
```js
const ktx2 = new KTX2Loader().setTranscoderPath('/basis/').detectSupport(renderer);
const loader = new GLTFLoader().setKTX2Loader(ktx2).setMeshoptDecoder(MeshoptDecoder);
```
See `references/rendering-optimizations.md` §7.
