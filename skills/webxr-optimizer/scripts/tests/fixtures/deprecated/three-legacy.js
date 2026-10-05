import * as THREE from '../build/three.min.js';
import '../examples/js/loaders/GLTFLoader.js';
import { VRButton } from 'three/addons/webxr/VRButton.js';

renderer.vr.enabled = true;
document.body.appendChild(WEBVR.createButton(renderer));
const vive = new ViveController(0);
document.body.appendChild(VRButton.createButton(renderer, { referenceSpaceType: 'local' }));
const xrCamera = renderer.xr.getCamera(camera);

const legacy = new THREE.WebGL1Renderer();
renderer.outputEncoding = THREE.sRGBEncoding;
material.map.encoding = THREE.LinearEncoding;
renderer.physicallyCorrectLights = true;
renderer.useLegacyLights = false;
const rt = new THREE.WebGLMultisampleRenderTarget(512, 512);
const geo = new THREE.Geometry();
const merged = BufferGeometryUtils.mergeBufferGeometries([a, b]);
const deg = THREE.Math.radToDeg(1);
const basis = new BasisTextureLoader();

renderer.xr.getController(0);
renderer.xr.getController(1);
