import { VRButton, XR, Controllers, Hands, Interactive, useXR } from '@react-three/xr';
import { useHitTest } from '@react-three/xr';

export function Scene() {
  const { isPresenting, player } = useXR();
  return (
    <XR foveation={1} referenceSpace="local-floor">
      <Controllers />
      <Hands />
    </XR>
  );
}
