/**
 * Three.js lighting setup for jewelry rendering.
 */

import { Environment } from "@react-three/drei";

export default function Lighting() {
  return (
    <>
      <ambientLight intensity={0.3} />
      <directionalLight position={[5, 10, 7]} intensity={1.2} castShadow />
      <directionalLight position={[-4, 8, -3]} intensity={0.4} />
      <pointLight position={[0, 12, 0]} intensity={0.8} />
      <pointLight position={[3, 6, 10]} intensity={0.3} color="#ffe4c4" />
      {/* Environment map for gem reflections & metal specular */}
      <Environment preset="studio" />
    </>
  );
}
