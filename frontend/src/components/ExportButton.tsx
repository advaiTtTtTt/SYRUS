/**
 * Export button — download STL or GLB.
 * Only enabled when validation ≠ REJECTED.
 */

import React from "react";
import { useProjectStore } from "../store/useProjectStore";
import { useCanExport } from "../store/selectors";
import { downloadModel } from "../api/exportApi";

const btnStyle = (enabled: boolean): React.CSSProperties => ({
  padding: "8px 16px",
  borderRadius: 6,
  border: "none",
  background: enabled ? "#a78bfa" : "#333",
  color: enabled ? "#000" : "#666",
  fontSize: 12,
  fontWeight: 600,
  cursor: enabled ? "pointer" : "not-allowed",
});

export default function ExportButton() {
  const buildId = useProjectStore((s) => s.buildId);
  const canExport = useCanExport();

  return (
    <div style={{ display: "flex", gap: 8 }}>
      <button
        style={btnStyle(canExport)}
        disabled={!canExport}
        onClick={() => buildId && downloadModel(buildId, "glb")}
      >
        Export GLB
      </button>
      <button
        style={btnStyle(canExport)}
        disabled={!canExport}
        onClick={() => buildId && downloadModel(buildId, "stl")}
      >
        Export STL
      </button>
    </div>
  );
}
