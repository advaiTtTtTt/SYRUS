/**
 * Export button — download STL or GLB.
 * Only enabled when validation ≠ REJECTED.
 */

import React, { useState } from "react";
import { useProjectStore } from "../store/useProjectStore";
import { useCanExport } from "../store/selectors";
import { downloadModel } from "../api/exportApi";
import { toast } from "../utils/toast";

const btnStyle = (enabled: boolean): React.CSSProperties => ({
  padding: "8px 16px",
  borderRadius: 6,
  border: "none",
  background: enabled ? "#a78bfa" : "#333",
  color: enabled ? "#000" : "#666",
  fontSize: 12,
  fontWeight: 600,
  cursor: enabled ? "pointer" : "not-allowed",
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
});

export default function ExportButton() {
  const buildId = useProjectStore((s) => s.buildId);
  const jewelryType = useProjectStore((s) => s.currentParams.type) ?? "ring";
  const canExport = useCanExport();
  const [exporting, setExporting] = useState<string | null>(null);

  const handleExport = async (format: "glb" | "stl") => {
    if (!buildId || !canExport) return;
    setExporting(format);
    try {
      await downloadModel(buildId, format, jewelryType);
      toast.success(`Exported ${format.toUpperCase()} successfully`);
    } catch {
      toast.error(`Export failed — try rebuilding`);
    } finally {
      setExporting(null);
    }
  };

  return (
    <div style={{ display: "flex", gap: 8 }}>
      <button
        style={btnStyle(canExport && exporting !== "glb")}
        disabled={!canExport || !!exporting}
        onClick={() => handleExport("glb")}
        aria-label="Export GLB model"
      >
        {exporting === "glb" && <span className="spinner" />}
        Export GLB
      </button>
      <button
        style={btnStyle(canExport && exporting !== "stl")}
        disabled={!canExport || !!exporting}
        onClick={() => handleExport("stl")}
        aria-label="Export STL model"
      >
        {exporting === "stl" && <span className="spinner" />}
        Export STL
      </button>
    </div>
  );
}
