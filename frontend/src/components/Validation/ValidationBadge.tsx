/**
 * Validation badge — SAFE / AUTO-CORRECTED / REJECTED indicator.
 */

import React from "react";
import { useProjectStore } from "../../store/useProjectStore";
import type { ManufacturingStatus } from "../../types/jewelry";

const COLORS: Record<ManufacturingStatus, { bg: string; fg: string }> = {
  SAFE: { bg: "#064e3b", fg: "#4ade80" },
  "AUTO-CORRECTED": { bg: "#78350f", fg: "#fbbf24" },
  REJECTED: { bg: "#7f1d1d", fg: "#f87171" },
};

const badgeStyle = (status: ManufacturingStatus): React.CSSProperties => ({
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  padding: "4px 12px",
  borderRadius: 6,
  fontSize: 11,
  fontWeight: 600,
  background: COLORS[status].bg,
  color: COLORS[status].fg,
});

export default function ValidationBadge() {
  const validation = useProjectStore((s) => s.validationResult);

  if (!validation) return null;

  const status = validation.manufacturing_status;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <span style={badgeStyle(status)}>
        {status === "SAFE" && "✓ "}
        {status === "AUTO-CORRECTED" && "⚠ "}
        {status === "REJECTED" && "✗ "}
        {status}
      </span>

      {validation.corrections_applied.length > 0 && (
        <div style={{ fontSize: 11, color: "#aaa", marginLeft: 4 }}>
          {validation.corrections_applied.map((c, i) => (
            <div key={i}>• {c}</div>
          ))}
        </div>
      )}

      {validation.violations_detected.length > 0 &&
        status === "REJECTED" && (
          <div style={{ fontSize: 11, color: "#f87171", marginLeft: 4 }}>
            {validation.violations_detected.map((v, i) => (
              <div key={i}>✗ {v}</div>
            ))}
          </div>
        )}
    </div>
  );
}
