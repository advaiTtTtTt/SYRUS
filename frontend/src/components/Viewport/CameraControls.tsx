/**
 * Camera orbit controls with optional turntable auto-rotate.
 */

import { OrbitControls } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useRef } from "react";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";

interface Props {
  autoRotate?: boolean;
  autoRotateSpeed?: number;
}

export default function CameraControls({
  autoRotate = false,
  autoRotateSpeed = 2.0,
}: Props) {
  const ref = useRef<OrbitControlsImpl>(null);

  // Smoothly interpolate rotation speed for buttery transitions
  useFrame(() => {
    if (ref.current) {
      ref.current.autoRotate = autoRotate;
      ref.current.autoRotateSpeed = autoRotateSpeed;
    }
  });

  return (
    <OrbitControls
      ref={ref}
      enablePan={true}
      enableZoom={true}
      enableRotate={true}
      enableDamping={true}
      dampingFactor={0.08}
      minDistance={10}
      maxDistance={60}
      maxPolarAngle={Math.PI * 0.85}
      target={[0, 0, 0]}
    />
  );
}
