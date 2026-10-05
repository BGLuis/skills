# Frame Budgets and Profiling

In XR a missed frame is not a lower FPS number. The compositor reuses or reprojects the previous frame, and the user sees **judder**, stuttering animations and black bars at the edge of the field of view. Optimize against the frame budget, measured on the device.

## 1. Budgets

| Refresh rate | Budget per frame (CPU and GPU each) | Where |
|---|---|---|
| 60 Hz | 16.6 ms | Phones (handheld AR) |
| 72 Hz | 13.7 ms | Meta Quest default (Quest 1 era) |
| 90 Hz | 11.1 ms | Quest 2 default in the Browser; IWER's Quest 3 preset reports 90 |
| 120 Hz | 8.3 ms | Opt-in on Quest through `updateTargetFrameRate` |

Source: https://developers.meta.com/horizon/documentation/web/webxr-perf-workflow/ (60/72/90), https://developers.meta.com/horizon/documentation/web/webxr-frames/ (Browser defaults).

Rules:
- **Pick the rate the scene actually sustains.** If the page cannot keep up, the system invents the missing frames and system load *rises*. Lowering the rate gives every frame more time. Raise it only with headroom. Source: webxr-frames page above.
- The frame-rate API (`session.supportedFrameRates`, `session.frameRate`, `session.updateTargetFrameRate(rate)`, and the `frameratechange` event) exists on **Quest Browser 16.4+ only**. Chrome (Android XR and phones) has not shipped it, and it is unknown on visionOS. Always feature-detect with `session.supportedFrameRates !== undefined`. `updateTargetFrameRate` rejects with `TypeError` for a rate that is not in the list. Sources: https://immersive-web.github.io/webxr/ , https://chromestatus.com/feature/5157293366181888
- `@react-three/xr` defaults to `frameRate: 'high'`, the highest supported rate. On a heavy scene, set `createXRStore({ frameRate: 'mid' })` or `'low'`, or a function, instead of letting it judder. Source: https://github.com/pmndrs/xr/blob/main/docs/tutorials/store.md

## 2. The official bottleneck workflow (Meta)

Change one thing at a time and re-measure on the headset.

1. **CPU or GPU bound?** Disable all rendering, so nothing is culled, submitted or shaded.
   - FPS barely changes → **CPU bound**.
   - FPS improves a lot → **GPU bound**.
2. **If GPU bound: vertex or fragment?** Set the render scale to about **0.01** with `renderer.xr.setFramebufferScaleFactor(0.01)` before the session starts.
   - No change → **vertex bound**: too much geometry or too many draw calls.
   - Improves → **fragment bound** (fill-rate): too many or too expensive pixels.
3. **CPU bound** → find hot code paths with Chrome tracing (`xr.debug` category). Optimize **any app logic over 2 ms**. Draw calls cost CPU no matter how small the mesh: "Submitting 1000 individual triangles as unique draw calls would likely cause your app to run at less than 72 frames per second".

Source: https://developers.meta.com/horizon/documentation/web/webxr-perf-workflow/

Fixes by bottleneck are in `rendering-optimizations.md`:

| Bottleneck | First things to try |
|---|---|
| CPU (draw calls) | Merge static meshes, `InstancedMesh` / `BatchedMesh`, multiview, fewer state changes |
| CPU (logic) | Stagger updates across frames, no allocation in the loop, move physics/pathfinding off the hot path |
| Vertex | LOD, simplification, break huge meshes apart so frustum culling works, cull instances |
| Fragment | Fixed foveation, front-to-back order, cheaper materials, fewer lights, compressed textures, no post-processing pass, Layers for video/sky/text |

## 3. Tools by device

| Device | Frame time HUD | CPU profile | GPU profile |
|---|---|---|---|
| Meta Quest | OVR Metrics Tool (FPS, **Stale Frame Count**, CPU/GPU level and utilization, App GPU Time) | `chrome://inspect` → **trace** → `xr.debug` | `ovrgpuprofiler`, RenderDoc (Meta fork, "Performance Counter Viewer", sort by GPU Duration; "Depth Test" overlay for overdraw) |
| Apple Vision Pro | none documented for WebXR | Safari Web Inspector (Timelines) from a Mac | Web Inspector; WebGL timer queries need the "WebGL Timer Queries" flag |
| Android XR / phones | in-app counters | `chrome://inspect` → DevTools Performance | in-app counters |

Commands and setup are in `testing-and-debugging.md`.

**In-app counters** in three.js, read once per frame inside `setAnimationLoop`:
- `renderer.info.render.calls` and `.triangles`
- `renderer.info.memory.geometries` and `.textures`
- `renderer.info.programs.length`

If you render several passes per frame, set `renderer.info.autoReset = false` and call `renderer.info.reset()` at the start of each frame. Source: https://threejs.org/docs/pages/WebGLRenderer.html

Measure frame-to-frame time from the timestamp the loop receives:
```js
let last = 0;
renderer.setAnimationLoop((t, frame) => {
  const dt = t - last; last = t;   // ~11.1 ms at 90 Hz; sustained higher values mean missed frames
  renderer.render(scene, camera);
});
```

**What not to trust:**
- Desktop Chrome FPS, the IWER emulator and the visionOS Simulator all run on a desktop GPU with software paths. **They are never performance evidence.**
- `stats.js` and `stats-gl` are DOM overlays and are not visible inside an immersive session.
- drei's `PerformanceMonitor` lowers `dpr`. **In XR the framebuffer size comes from `framebufferScaleFactor`, not from `dpr`**, so its `onDecline` does nothing for the headset (inference from its implementation).

## 4. Reading stale frames

- A **stale frame** is a frame that was not delivered on time, so the compositor reused the previous one.
- A stale count that sits between 0 and the refresh rate means inconsistent delivery: the user sees judder.
- Fix it by lowering the frame rate or the per-frame cost until stale frames sit at 0 during normal use.

Sources: https://developers.meta.com/horizon/documentation/unity/ts-ovrstats/ , https://developers.meta.com/horizon/blog/ovr-metrics-tool-vrapi-what-do-these-metrics-mean/

## 5. Reporting

Report each change as **device + refresh rate + metric before → after**, for example: "Quest 3 @ 90 Hz: App GPU Time 13.2 ms → 9.4 ms, stale frames/s 18 → 0 after enabling foveation 1.0 and dropping the bloom pass." When no headset was available, say so and label every number as an estimate.
