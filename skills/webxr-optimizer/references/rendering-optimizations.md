# Rendering Optimizations for XR

Apply these after `budgets-and-profiling.md` tells you whether the frame is CPU, vertex or fragment bound. Each rule names the bottleneck it fixes. Applying a fragment fix to a CPU-bound app wastes effort and may cost image quality.

## 1. Session-level knobs (set these first, they are nearly free)

### Fixed foveated rendering (fragment bound)
- FFR renders the periphery of each eye at a lower resolution.
- three.js: `renderer.xr.setFoveation(0..1)`, where 0 is full resolution and 1 is maximum foveation. **The default in `WebXRManager` is already `1.0`.** Check that the app did not set it lower.
- `@react-three/xr`: `createXRStore({ foveation: 1 })`. When undefined, it uses the browser default.
- Raw WebXR on Quest: set `XRWebGLLayer.fixedFoveation` (0–1) at runtime, or request `'high-fixed-foveation-level'`, `'medium-fixed-foveation-level'` or `'low-fixed-foveation-level'` in `optionalFeatures`. `fixedFoveation` is Quest-only. Chrome has not shipped it.
- High-contrast or text-heavy scenes show foveation artifacts. Put text in a Layer (§2) or lower the level.
- **FFR silently stops working** in two cases:
  - you render the scene into an intermediate render target and post-process it into the final frame;
  - you switch render targets mid-frame (for example eye buffer → shadow map → eye buffer). This also breaks MSAA.

  Render every offscreen target first, then the whole eye buffer in one pass.
- To verify on device, run `adb shell ovrgpuprofiler -t` in immersive mode. The "stages" count drops when FFR is active.

Sources: https://developers.meta.com/horizon/documentation/web/webxr-ffr/ , https://developer.mozilla.org/en-US/docs/Web/API/XRWebGLLayer/fixedFoveation , three.js r186 `src/renderers/webxr/WebXRManager.js` (`let foveation = 1.0`)

### Framebuffer scale (fragment bound)
- `renderer.xr.setFramebufferScaleFactor(s)` **must be called before the session starts**. During a session, three.js only logs `Cannot change framebuffer scale while presenting`.
- `@react-three/xr` equivalent: `createXRStore({ frameBufferScaling: 'high' | 'mid' | 'low' | number })`.
- Raw WebXR: `new XRWebGLLayer(session, gl, { framebufferScaleFactor })`. `XRWebGLLayer.getNativeFramebufferScaleFactor(session)` gives the scale that matches the panel 1:1.
- **Vision Pro**: a three.js report (issue #27968, r162 era) says the scale factor had no effect there. Verify on the device before relying on it.

Sources: https://threejs.org/docs/pages/WebXRManager.html , https://github.com/mrdoob/three.js/issues/27968

### Frame rate (everything)
See `budgets-and-profiling.md` §1. A lower stable rate beats a higher rate with judder.

### Clear color (fragment, Quest)
- When the background is not the clear color, clear to **black or white**. Adreno GPUs on Quest have a hardware fast-clear for those two colors.
- In `immersive-ar` (passthrough) you must clear to transparent. Don't draw an opaque background there.

Sources: https://developers.meta.com/horizon/documentation/web/webxr-perf-bp/ , https://developers.meta.com/horizon/documentation/web/webxr-mixed-reality/

## 2. WebXR Layers (fragment bound, image quality)

Normally, every eye-buffer pixel is re-rendered each frame, and the compositor resamples it. **Layers hand a quad, cylinder, equirect or cube texture straight to the compositor.**
- A static skybox is uploaded once and never redrawn.
- A video or text panel is sampled once, so it is sharper and cheaper.
- `XRMediaBinding.createQuadLayer` / `createCylinderLayer(video, …)` plays a `<video>` with low overhead (Quest only).

Source: https://developers.meta.com/horizon/documentation/web/webxr-layers/

Support:
- **Quest:** Layers and Media Layers are on by default.
- **Chrome:** Layers arrive in 147; there is no `XRMediaBinding`.
- **visionOS:** texture-array projection layers since Safari 27.0. Other layer types and the default state in 26.x are unconfirmed.

Always request `'layers'` in `optionalFeatures` and check `session.enabledFeatures` before using them.

In three.js r186 the `WebGPURenderer` XR manager has `renderer.xr.createQuadLayer(w, h, position, quaternion, pxW, pxH, renderFn)` and `createCylinderLayer(...)`. They return a mesh that you add to the scene (example `webgpu_xr_native_layers.html`). three's `VRButton` and `XRButton` already request `layers` as an optional feature. Sources: three.js r186 `src/renderers/common/XRManager.js`, `examples/jsm/webxr/VRButton.js`; https://webkit.org/blog/18325/webkit-features-for-safari-27-0/

## 3. Multiview (CPU bound)

- Multiview renders both eyes in one pass. Meta: "Only CPU-bound experiences will benefit from multi-view. Often, a CPU usage reduction of 25% - 50% is possible".
- It needs WebGL 2. On Quest, `OCULUS_multiview` (with MSAA) works out of the box. `OVR_multiview2` sits behind a flag there.
- Meta calls multiview rendering into a WebXR projection layer with `textureType: 'texture-array'` "the recommended way to render a scene on Quest hardware".
- Shaders must be GLSL ES 3.00 and use `gl_ViewID_OVR`.
- Flicker with multiview usually means render targets are being switched mid-frame.

Source: https://developers.meta.com/horizon/documentation/web/web-multiview/

**three.js reality check (verified in r186 sources):**
- `WebGLRenderer` has **no** multiview path.
- Multiview exists only in `WebGPURenderer`: `new THREE.WebGPURenderer({ multiview: true })`.
  - It works with the **WebGL backend** through `OVR_multiview2`.
  - The native WebGPU XR path warns `WebGPU XR does not support multiview yet` and disables it.
- Example: `examples/webgpu_xr_cubes.html`, which also shows the `forceWebGL` fallback.

Sources: three.js r186 `src/renderers/common/Renderer.js`, `src/renderers/common/XRManager.js`

## 4. Draw calls (CPU and vertex bound)

- **Merge static geometry** with `BufferGeometryUtils.mergeGeometries()` (renamed from `mergeBufferGeometries` in r151).
- Use **`InstancedMesh`** for many copies of one mesh. Use **`BatchedMesh`** (r159+) for many different geometries that share one material. It needs `addGeometry()` + `addInstance()`.
- Keep frustum culling effective:
  - split huge meshes, such as a whole building, into chunks;
  - cluster instances spatially;
  - set a correct `boundingSphere` on instanced and batched meshes.
- Use **LOD** (`THREE.LOD`) for distant detail.
- **Stagger CPU work**: animate a third of the objects per frame, and update far objects less often.

Sources: https://developers.meta.com/horizon/documentation/web/webxr-perf-workflow/ , https://developers.meta.com/horizon/documentation/web/webxr-perf-bp/ , three.js r186 `src/objects/BatchedMesh.js`

## 5. Materials, lights, shadows, transparency (fragment bound)

- **Lights**: with heavy PBR, use **one directional or one point light**. Cost rises from directional to point to spot to area. For static lighting, use light probes, environment maps or **baked lightmaps**.
- **PBR** (`MeshStandardMaterial`) only on hero objects. Use `MeshLambertMaterial` / `MeshPhongMaterial` / `MeshBasicMaterial` for the background. Drop optional maps (AO, roughness) or lower their resolution.
- **Shadows** re-render the scene from each light and count against the draw-call and triangle budget. Point-light shadows render 6 maps per frame. Prefer baked shadows or one small shadow map from a directional light.
- **Overdraw**:
  - Opaque objects must draw front-to-back. three.js sorts by default, but a sky sphere centered on the viewer sorts as "near". Give it a high `renderOrder` so it draws last.
  - Particles and large transparent planes are the worst case.
  - **Stop drawing objects that have faded to opacity 0** with `visible = false`, because invisible-but-rendered still costs full price.
- Prefer `mediump` precision and cheaper filtering (reduce anisotropy) where it does not show.

Sources: https://developers.meta.com/horizon/documentation/web/webxr-perf-bp/ , https://developers.meta.com/horizon/documentation/web/webxr-perf-workflow/

## 6. Post-processing (fragment bound, often fatal in XR)

A full-screen pass re-shades every pixel of both eyes at headset resolution. It also renders into an intermediate target, which **disables FFR** (§1) and can break MSAA. On Quest-class GPUs, remove bloom, SSAO, DOF and SMAA chains. Bake the look into materials or textures instead. If a pass is truly required:
- measure it on the device;
- render it at reduced resolution;
- keep the scene pass in one uninterrupted render-target binding.

Source: https://developers.meta.com/horizon/documentation/web/webxr-ffr/

## 7. Assets and memory

- **Textures**: KTX2 / Basis Universal is Meta's recommended compression for WebXR on Quest. The file can be larger than a JPEG, but **GPU memory and bandwidth are much lower**.
  - Use ETC1S for color maps and UASTC for normal maps (KTX Artist Guide).
  - Raw PNG and JPEG are decoded to full RGBA in VRAM.
- **Geometry**: Meshopt or Draco compression in glTF. Simplify meshes offline.
- **Pipeline**: `npx @gltf-transform/cli optimize in.glb out.glb --compress meshopt --texture-compress ktx2`. Its help says "KTX2 optimizes VRAM usage and performance; AVIF and WebP optimize transmission size". For XR, VRAM wins.
- **Requests**: send fewer, larger requests. Many small fetches hurt on the headset.

Loader setup in three.js r186:

```js
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';

const ktx2 = new KTX2Loader()
  .setTranscoderPath('/basis/')        // copy three/examples/jsm/libs/basis/ to your public dir
  .detectSupport(renderer);            // WebGPURenderer: call after `await renderer.init()`
const gltf = new GLTFLoader().setKTX2Loader(ktx2).setMeshoptDecoder(MeshoptDecoder);
```

Sources: https://developers.meta.com/horizon/documentation/web/webxr-perf-bp/ , three.js r186 `examples/webgl_loader_gltf_compressed.html`, `examples/jsm/loaders/KTX2Loader.js` (the default `transcoderPath` is `''`, so you must set it)

## 8. Main-thread hitches (spikes, not averages)

- **Shader compilation** on first sight of a material causes a multi-frame hitch inside the headset. Warm materials up before entering XR with `await renderer.compileAsync(scene, camera)`.
- **Texture upload** on first use stalls too. Pre-upload with `renderer.initTexture(texture)` while still on the 2D page.
- **GC pauses**: never allocate in the render loop. Hoist `new Vector3()`, `new Matrix4()` and arrays to module scope and reuse them.
- **Loading after entry**: load and decode assets before calling `requestSession`, or behind an in-scene loading state. Never block the XR frame on a fetch.

Sources: three.js r186 `src/renderers/WebGLRenderer.js` (`compileAsync`, `initTexture`)

## 9. Render loop correctness (affects everything)

- Drive rendering with `renderer.setAnimationLoop(fn)` in three.js, or `session.requestAnimationFrame(fn)` in raw WebXR. `window.requestAnimationFrame` does not drive the headset, which gives a frozen or black view or double work.
- In XR, three.js renders the per-eye `ArrayCamera`. Don't move the camera yourself. Move a rig or origin group instead (`<XROrigin>` in `@react-three/xr`).
- `@react-three/xr` needs `frameloop="always"`, the R3F default. `"demand"` is not supported by its layers and events code.

Sources: https://threejs.org/docs/#manual/en/introduction/How-to-create-VR-content , https://developer.mozilla.org/en-US/docs/Web/API/WebXR_Device_API/Rendering , `@pmndrs/xr` 6.6.31 sources
