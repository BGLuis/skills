import { XR, XROrigin, createXRStore, useXR, IfInSessionMode } from '@react-three/xr';
import { OrbitControls } from '@react-three/drei';
import { Controllers } from './my-controllers';

const store = createXRStore({ foveation: 1, frameRate: 'mid' });

export function App() {
  const inSession = useXR((s) => s.session != null);
  return (
    <>
      <button onClick={() => store.enterVR()}>Enter VR</button>
      <XR store={store}>
        <IfInSessionMode deny={['immersive-vr', 'immersive-ar']}>
          <OrbitControls />
        </IfInSessionMode>
        <XROrigin position={[0, 0, 2]} />
        <Controllers />
      </XR>
    </>
  );
}
