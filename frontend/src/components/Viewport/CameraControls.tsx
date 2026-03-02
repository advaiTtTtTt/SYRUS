/**
 * Camera orbit controls.
 */

import { OrbitControls } from "@react-three/drei";

export default function CameraControls() {
  return (
    <OrbitControls
      enablePan={true}
      enableZoom={true}
      enableRotate={true}
      minDistance={10}
      maxDistance={60}
      target={[0, 0, 0]}
    />
  );
}
