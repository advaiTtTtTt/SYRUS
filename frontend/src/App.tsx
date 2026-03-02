/**
 * Root App component — main layout.
 *
 * Layout:
 *   ┌──────────────────────────┬────────────────┐
 *   │                          │  Customizer    │
 *   │    3D Viewport           │  Panel         │
 *   │                          ├────────────────┤
 *   │                          │  Budget Panel  │
 *   ├──────────────────────────┴────────────────┤
 *   │  Upload | Validation | Export             │
 *   └──────────────────────────────────────────-┘
 */

import React from "react";
import ImageUpload from "./components/ImageUpload";
import Viewport from "./components/Viewport/Viewport";
import CustomizerPanel from "./components/Customizer/CustomizerPanel";
import BudgetPanel from "./components/Budget/BudgetPanel";
import ValidationBadge from "./components/Validation/ValidationBadge";
import ExportButton from "./components/ExportButton";
import { useBuild } from "./hooks/useBuild";
import { useProjectStore } from "./store/useProjectStore";

const layoutStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1fr 320px",
  gridTemplateRows: "1fr auto",
  height: "100vh",
  gap: 12,
  padding: 12,
  background: "#0f0f0f",
};

const viewportArea: React.CSSProperties = {
  gridColumn: "1",
  gridRow: "1",
  minHeight: 0,
};

const sidebarArea: React.CSSProperties = {
  gridColumn: "2",
  gridRow: "1",
  display: "flex",
  flexDirection: "column",
  gap: 12,
  overflowY: "auto",
};

const bottomBar: React.CSSProperties = {
  gridColumn: "1 / -1",
  gridRow: "2",
  display: "flex",
  alignItems: "center",
  gap: 16,
  padding: "8px 12px",
  background: "#111",
  borderRadius: 12,
};

export default function App() {
  // Activate the auto-build hook
  useBuild();

  const parseResult = useProjectStore((s) => s.parseResult);
  const buildError = useProjectStore((s) => s.buildError);

  return (
    <div style={layoutStyle}>
      {/* 3D Viewport */}
      <div style={viewportArea}>
        <Viewport />
      </div>

      {/* Sidebar */}
      <div style={sidebarArea}>
        <CustomizerPanel />
        <BudgetPanel />
      </div>

      {/* Bottom bar */}
      <div style={bottomBar}>
        <div style={{ flex: "0 0 280px" }}>
          <ImageUpload />
        </div>

        {parseResult && (
          <div style={{ fontSize: 11, color: "#888" }}>
            Confidence: {(parseResult.confidence_score * 100).toFixed(0)}%
          </div>
        )}

        <ValidationBadge />

        {buildError && (
          <div style={{ fontSize: 11, color: "#f87171", maxWidth: 200 }}>
            {buildError}
          </div>
        )}

        <div style={{ marginLeft: "auto" }}>
          <ExportButton />
        </div>
      </div>
    </div>
  );
}
