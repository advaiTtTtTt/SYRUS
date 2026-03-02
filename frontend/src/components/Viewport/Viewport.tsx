/**
 * Main 3D viewport — React Three Fiber canvas.
 */

import { Canvas } from "@react-three/fiber";
import React, { Suspense } from "react";
import { useProjectStore } from "../../store/useProjectStore";
import CameraControls from "./CameraControls";
import Lighting from "./Lighting";
import RingModel from "./RingModel";

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: "100%",
    height: "100%",
    position: "relative",
    background: "#1a1a2e",
    borderRadius: 12,
    overflow: "hidden",
  },
  overlay: {
    position: "absolute",
    top: 12,
    right: 12,
    display: "flex",
    gap: 8,
    zIndex: 10,
  },
  badge: {
    padding: "4px 10px",
    borderRadius: 6,
    fontSize: 11,
    fontWeight: 600,
  },
  loading: {
    position: "absolute",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    color: "#a78bfa",
    fontSize: 14,
  },
};

export default function Viewport() {
  const isBuilding = useProjectStore((s) => s.isBuilding);

  return (
    <div style={styles.container}>
      {isBuilding && <div style={styles.loading}>Building 3D model...</div>}
      <Canvas
        camera={{ position: [0, 15, 30], fov: 45 }}
        shadows
        gl={{ toneMappingExposure: 1.2 }}
      >
        <Suspense fallback={null}>
          <Lighting />
          <RingModel />
          <CameraControls />
          <gridHelper args={[40, 40, "#333", "#222"]} />
        </Suspense>
      </Canvas>
    </div>
  );
}
