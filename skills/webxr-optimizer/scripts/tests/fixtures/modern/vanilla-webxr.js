// Modern equivalents of every pattern in ../deprecated: the scanner must report nothing here.
// Comments mentioning old APIs (getVRDisplays, renderer.vr, sRGBEncoding) are ignored.
import * as THREE from 'three';
import { VRButton } from 'three/addons/webxr/VRButton.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js';

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.xr.enabled = true;
renderer.xr.setReferenceSpaceType('local-floor');
renderer.xr.setFoveation(1.0);
renderer.outputColorSpace = THREE.SRGBColorSpace;
texture.colorSpace = THREE.SRGBColorSpace;
const encoder = new TextEncoder();
const body = { encoding: 'utf8' };
const rt = new THREE.WebGLRenderTarget(512, 512, { samples: 4 });
const geo = new THREE.BoxGeometry(1, 1, 1);
const merged = mergeGeometries([geo, geo.clone()]);
const deg = THREE.MathUtils.radToDeg(1);
const ktx2 = new KTX2Loader();
const xrCamera = renderer.xr.getCamera();
document.body.appendChild(VRButton.createButton(renderer, { optionalFeatures: ['hand-tracking'] }));

for (let i = 0; i < 4; i++) {
  scene.add(renderer.xr.getController(i), renderer.xr.getControllerGrip(i));
}

export async function enter() {
  if (!(await navigator.xr.isSessionSupported('immersive-vr'))) return;
  const session = await navigator.xr.requestSession('immersive-vr', {
    requiredFeatures: ['local-floor'],
    optionalFeatures: ['hand-tracking', 'layers', 'anchors'],
    depthSensing: { usagePreference: ['gpu-optimized'], dataFormatPreference: ['float32'] },
  });
  const gl = canvas.getContext('webgl2');
  await gl.makeXRCompatible();
  session.updateRenderState({ baseLayer: new XRWebGLLayer(session, gl) });
  const layer = session.renderState.baseLayer;
  const space = await session.requestReferenceSpace('local-floor');
  session.requestAnimationFrame(function onFrame(t, frame) {
    for (const source of session.inputSources) {
      const pose = frame.getPose(source.targetRaySpace, space);
      const tip = source.hand?.get('index-finger-tip');
    }
    frame.session.requestAnimationFrame(onFrame);
  });
}

renderer.setAnimationLoop(() => renderer.render(scene, camera));
