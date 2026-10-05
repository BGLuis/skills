import 'webvr-polyfill';
import WebXRPolyfill from 'webxr-polyfill';

navigator.getVRDisplays().then((displays) => {
  const display = displays[0];
  const frameData = new VRFrameData();
  window.addEventListener('vrdisplaypresentchange', () => {});
  display.submitFrame();
});

navigator.xr.requestDevice().then((device) => gl.setCompatibleXRDevice(device));
navigator.xr.supportsSession('immersive-vr');
navigator.xr.supportsSessionMode('immersive-vr');
navigator.xr.requestSession({ immersive: true });

session.requestFrameOfReference('eye-level');
session.requestReferenceSpace({ type: 'stationary', subtype: 'floor-level' });
session.requestReferenceSpace('stage');
const pose = frame.getDevicePose(frameOfRef);
const inputPose = frame.getInputPose(source, frameOfRef);
const ctx = canvas.getContext('xrpresent');
session.requestSession('immersive-vr', { outputContext: ctx });
session.baseLayer = new XRWebGLLayer(session, gl);

const wrist = hand[XRHand.WRIST];
session.requestSession('immersive-ar', {
  depthSensing: { usagePreference: ['cpu-optimized'], formatPreference: ['luminance-alpha'] },
});

const first = session.inputSources[0];
session.requestSession('immersive-vr', { requiredFeatures: ['local-floor', 'hand-tracking'] });
const gl1 = canvas.getContext('webgl');

function loop() {
  requestAnimationFrame(loop);
}
