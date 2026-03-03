/**
 * Main 3D viewport — React Three Fiber canvas.
 * Includes welcome empty-state, turntable auto-rotate, and ErrorBoundary wrapping.
 */

import { Canvas } from "@react-three/fiber";
import React, { Suspense, useCallback, useRef, useState } from "react";
import { useProjectStore } from "../../store/useProjectStore";
import ErrorBoundary from "../ErrorBoundary";
import CameraControls from "./CameraControls";
import Lighting from "./Lighting";
import RingModel from "./RingModel";

const SPEED_STEPS = [1, 2, 4, 8];
const BG_PRESETS = [
  { label: "Dark", value: "#1a1a2e" },
  { label: "Charcoal", value: "#2d2d3d" },
  { label: "Midnight", value: "#0f0f1a" },
  { label: "Slate", value: "#334155" },
  { label: "Warm", value: "#2e1a1a" },
  { label: "White", value: "#e8e8e8" },
];

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: "100%",
    height: "100%",
    position: "relative",
    borderRadius: 12,
    overflow: "hidden",
    transition: "background 0.3s ease",
  },
  overlay: {
    position: "absolute",
    top: 12,
    right: 12,
    display: "flex",
    gap: 8,
    zIndex: 10,
  },
  loading: {
    position: "absolute",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    color: "#a78bfa",
    fontSize: 14,
    zIndex: 10,
  },
  welcome: {
    position: "absolute",
    top: 16,
    left: 16,
    right: 16,
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    gap: 6,
    padding: "16px 12px",
    background: "rgba(167, 139, 250, 0.08)",
    border: "1px solid rgba(167, 139, 250, 0.2)",
    borderRadius: 10,
    zIndex: 10,
    pointerEvents: "none" as const,
  },
};

const turntableBtn = (active: boolean): React.CSSProperties => ({
  padding: "5px 10px",
  borderRadius: 6,
  border: active ? "1px solid #a78bfa" : "1px solid #333",
  background: active ? "rgba(167,139,250,0.15)" : "rgba(0,0,0,0.5)",
  color: active ? "#a78bfa" : "#888",
  fontSize: 11,
  fontWeight: 600,
  cursor: "pointer",
  backdropFilter: "blur(4px)",
  transition: "all 0.2s",
});

const speedBtn: React.CSSProperties = {
  padding: "3px 7px",
  borderRadius: 4,
  border: "1px solid #333",
  background: "rgba(0,0,0,0.5)",
  color: "#888",
  fontSize: 10,
  cursor: "pointer",
  backdropFilter: "blur(4px)",
};

const settingsPanel: React.CSSProperties = {
  position: "absolute",
  top: 44,
  right: 12,
  background: "rgba(15,15,26,0.92)",
  border: "1px solid #333",
  borderRadius: 8,
  padding: "10px 12px",
  display: "flex",
  flexDirection: "column",
  gap: 10,
  zIndex: 20,
  backdropFilter: "blur(8px)",
  minWidth: 170,
};

const settingsLabel: React.CSSProperties = {
  fontSize: 10,
  fontWeight: 600,
  color: "#888",
  textTransform: "uppercase",
  letterSpacing: "0.5px",
};

const swatchRow: React.CSSProperties = {
  display: "flex",
  gap: 6,
  flexWrap: "wrap",
};

const swatchStyle = (color: string, active: boolean): React.CSSProperties => ({
  width: 22,
  height: 22,
  borderRadius: 6,
  background: color,
  border: active ? "2px solid #a78bfa" : "2px solid transparent",
  cursor: "pointer",
  transition: "border-color 0.15s, transform 0.15s",
  transform: active ? "scale(1.15)" : "scale(1)",
  boxShadow: active ? "0 0 6px rgba(167,139,250,0.4)" : "none",
});

export default function Viewport() {
  const isBuilding = useProjectStore((s) => s.isBuilding);
  const parseResult = useProjectStore((s) => s.parseResult);

  const [autoRotate, setAutoRotate] = useState(false);
  const [speedIdx, setSpeedIdx] = useState(1); // default = 2x
  const [bgColor, setBgColor] = useState("#1a1a2e");
  const [showGrid, setShowGrid] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const colorInputRef = useRef<HTMLInputElement>(null);

  const toggleRotate = useCallback(() => setAutoRotate((p) => !p), []);
  const cycleSpeed = useCallback(
    () => setSpeedIdx((i) => (i + 1) % SPEED_STEPS.length),
    [],
  );
  const toggleGrid = useCallback(() => setShowGrid((p) => !p), []);
  const toggleSettings = useCallback(() => setShowSettings((p) => !p), []);

  return (
    <div style={{ ...styles.container, background: bgColor }}>
      {/* Toolbar overlay — top-right */}
      <div style={styles.overlay}>
        {autoRotate && (
          <button style={speedBtn} onClick={cycleSpeed} title="Rotation speed">
            {SPEED_STEPS[speedIdx]}x
          </button>
        )}
        <button
          style={turntableBtn(autoRotate)}
          onClick={toggleRotate}
          title={autoRotate ? "Stop turntable" : "Start turntable (auto-rotate)"}
        >
          {autoRotate ? "⏸ Turntable" : "▶ Turntable"}
        </button>
        <button
          style={turntableBtn(showSettings)}
          onClick={toggleSettings}
          title="Viewport settings"
          aria-label="Viewport settings"
        >
          ⚙
        </button>
      </div>

      {/* Settings dropdown */}
      {showSettings && (
        <div style={settingsPanel}>
          <div>
            <div style={settingsLabel}>Background</div>
            <div style={{ ...swatchRow, marginTop: 6 }}>
              {BG_PRESETS.map((p) => (
                <button
                  key={p.value}
                  style={swatchStyle(p.value, bgColor === p.value)}
                  onClick={() => setBgColor(p.value)}
                  title={p.label}
                  aria-label={`Background: ${p.label}`}
                />
              ))}
              <button
                style={{
                  ...swatchStyle("transparent", false),
                  background:
                    "conic-gradient(red,yellow,lime,aqua,blue,magenta,red)",
                  position: "relative",
                }}
                onClick={() => colorInputRef.current?.click()}
                title="Custom color"
                aria-label="Pick custom background color"
              />
              <input
                ref={colorInputRef}
                type="color"
                value={bgColor}
                onChange={(e) => setBgColor(e.target.value)}
                style={{ position: "absolute", opacity: 0, pointerEvents: "none" }}
                aria-hidden="true"
              />
            </div>
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <span style={settingsLabel}>Grid</span>
            <button
              style={turntableBtn(showGrid)}
              onClick={toggleGrid}
              aria-label={showGrid ? "Hide grid" : "Show grid"}
            >
              {showGrid ? "On" : "Off"}
            </button>
          </div>
        </div>
      )}

      {/* Welcome hint when no image has been parsed yet */}
      {!parseResult && !isBuilding && (
        <div style={styles.welcome}>
          <div style={{ fontSize: 28 }}>💍</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: "#a78bfa" }}>
            Welcome to SYRUS
          </div>
          <div style={{ fontSize: 12, color: "#888", textAlign: "center" }}>
            Upload a jewelry image below to generate a 3D model, or use the
            customizer panel to design from scratch.
          </div>
          <div style={{ fontSize: 10, color: "#666", marginTop: 4 }}>
            Ctrl+Z to undo · Ctrl+Shift+Z to redo
          </div>
        </div>
      )}

      {isBuilding && (
        <div style={styles.loading}>
          <span className="spinner spinner--lg" style={{ marginRight: 10 }} />
          Building 3D model...
        </div>
      )}

      <ErrorBoundary>
        <Canvas
          camera={{ position: [0, 15, 30], fov: 45 }}
          shadows
          gl={{ toneMappingExposure: 1.2 }}
        >
          <Suspense fallback={null}>
            <Lighting />
            <RingModel />
            <CameraControls
              autoRotate={autoRotate}
              autoRotateSpeed={SPEED_STEPS[speedIdx]}
            />
            {showGrid && <gridHelper args={[40, 40, "#333", "#222"]} />}
          </Suspense>
        </Canvas>
      </ErrorBoundary>
    </div>
  );
}
