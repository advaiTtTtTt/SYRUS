/**
 * Root App component — main layout.
 *
 * Layout:
 *   ┌──────────┬─────────────────────┬────────────────┐
 *   │  Source   │                     │  Customizer    │
 *   │  Image   │    3D Viewport      │  Panel         │
 *   │  (2D)    │                     ├────────────────┤
 *   │          │                     │  Budget Panel  │
 *   ├──────────┴─────────────────────┴────────────────┤
 *   │  Upload | Confidence | Undo/Redo | Validation | Export │
 *   └────────────────────────────────────────────────────────┘
 */

import React, { useEffect } from "react";
import ImageUpload from "./components/ImageUpload";
import SourceImagePanel from "./components/SourceImagePanel";
import Viewport from "./components/Viewport/Viewport";
import CustomizerPanel from "./components/Customizer/CustomizerPanel";
import BudgetPanel from "./components/Budget/BudgetPanel";
import ValidationBadge from "./components/Validation/ValidationBadge";
import ExportButton from "./components/ExportButton";
import { useBuild } from "./hooks/useBuild";
import { useKeyboardShortcuts } from "./hooks/useKeyboardShortcuts";
import { useProjectStore } from "./store/useProjectStore";
import { useStore } from "zustand";
import { estimateCost } from "./api/budgetApi";

const layoutStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "auto 1fr 320px",
  gridTemplateRows: "1fr auto",
  height: "100vh",
  gap: 12,
  padding: 12,
  background: "#0f0f0f",
};

const imagePanelArea: React.CSSProperties = {
  gridColumn: "1",
  gridRow: "1",
  width: 220,
  minHeight: 0,
};

const viewportArea: React.CSSProperties = {
  gridColumn: "2",
  gridRow: "1",
  minHeight: 0,
};

const sidebarArea: React.CSSProperties = {
  gridColumn: "3",
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

const undoBtnStyle = (enabled: boolean): React.CSSProperties => ({
  padding: "4px 10px",
  borderRadius: 6,
  border: "1px solid #333",
  background: enabled ? "#222" : "#111",
  color: enabled ? "#ccc" : "#444",
  fontSize: 12,
  cursor: enabled ? "pointer" : "not-allowed",
  fontWeight: 600,
});

export default function App() {
  // Activate hooks
  useBuild();
  useKeyboardShortcuts();

  const parseResult = useProjectStore((s) => s.parseResult);
  const sourceImage = useProjectStore((s) => s.sourceImage);
  const buildError = useProjectStore((s) => s.buildError);
  const budgetResult = useProjectStore((s) => s.budgetResult);

  // Initial cost estimate on mount so budget panel isn't empty
  useEffect(() => {
    if (!budgetResult) {
      const { currentParams, customization } = useProjectStore.getState();
      estimateCost(currentParams, customization)
        .then((res) => useProjectStore.setState({ budgetResult: res }))
        .catch(() => {}); // Non-fatal
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleUndo = () => useProjectStore.temporal.getState().undo();
  const handleRedo = () => useProjectStore.temporal.getState().redo();

  // Check if undo/redo are available
  const pastStates = useStore(useProjectStore.temporal, (s) => s.pastStates);
  const futureStates = useStore(useProjectStore.temporal, (s) => s.futureStates);

  // Collapse image panel when no image uploaded
  const showImagePanel = !!sourceImage;

  return (
    <div
      style={{
        ...layoutStyle,
        gridTemplateColumns: showImagePanel ? "220px 1fr 320px" : "1fr 320px",
      }}
    >
      {/* Source image panel — 2D side of the 2D→3D demo */}
      {showImagePanel && (
        <div style={imagePanelArea}>
          <SourceImagePanel />
        </div>
      )}

      {/* 3D Viewport */}
      <div style={{ ...viewportArea, gridColumn: showImagePanel ? "2" : "1" }}>
        <Viewport />
      </div>

      {/* Sidebar */}
      <div style={{ ...sidebarArea, gridColumn: showImagePanel ? "3" : "2" }}>
        <CustomizerPanel />
        <BudgetPanel />
      </div>

      {/* Bottom bar */}
      <div style={bottomBar}>
        <div style={{ flex: "0 0 280px" }}>
          <ImageUpload />
        </div>

        {parseResult && (
          <div
            style={{
              fontSize: 11,
              fontWeight: 600,
              color:
                parseResult.confidence_score >= 0.7
                  ? "#4ade80"
                  : parseResult.confidence_score >= 0.4
                  ? "#fbbf24"
                  : "#f87171",
            }}
          >
            AI: {(parseResult.confidence_score * 100).toFixed(0)}%
          </div>
        )}

        {/* Undo / Redo buttons */}
        <div style={{ display: "flex", gap: 4 }}>
          <button
            style={undoBtnStyle(pastStates.length > 0)}
            disabled={pastStates.length === 0}
            onClick={handleUndo}
            title="Undo (Ctrl+Z)"
            aria-label="Undo last change"
          >
            ↩ Undo
          </button>
          <button
            style={undoBtnStyle(futureStates.length > 0)}
            disabled={futureStates.length === 0}
            onClick={handleRedo}
            title="Redo (Ctrl+Shift+Z)"
            aria-label="Redo last change"
          >
            ↪ Redo
          </button>
        </div>

        <ValidationBadge />

        {buildError && (
          <div
            style={{
              fontSize: 11,
              color: "#f87171",
              maxWidth: 200,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
            title={buildError}
          >
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
