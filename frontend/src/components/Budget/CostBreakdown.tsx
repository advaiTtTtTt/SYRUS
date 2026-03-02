/**
 * Cost breakdown display.
 */

import React from "react";
import type { CostBreakdown } from "../../types/jewelry";

const rowStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  fontSize: 12,
  color: "#ccc",
  marginBottom: 4,
};

function formatINR(v: number): string {
  return `₹${v.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

interface Props {
  breakdown: CostBreakdown;
}

export default function CostBreakdownView({ breakdown }: Props) {
  return (
    <div>
      <div style={rowStyle}>
        <span>Metal</span>
        <span>{formatINR(breakdown.metal_cost)}</span>
      </div>
      <div style={rowStyle}>
        <span>Gemstone</span>
        <span>{formatINR(breakdown.gemstone_cost)}</span>
      </div>
      {breakdown.side_stones_cost > 0 && (
        <div style={rowStyle}>
          <span>Side Stones</span>
          <span>{formatINR(breakdown.side_stones_cost)}</span>
        </div>
      )}
      {breakdown.setting_multiplier !== 1.0 && (
        <div style={rowStyle}>
          <span>Setting Complexity</span>
          <span>×{breakdown.setting_multiplier}</span>
        </div>
      )}
      <div
        style={{
          ...rowStyle,
          borderTop: "1px solid #333",
          paddingTop: 6,
          marginTop: 6,
          fontWeight: 600,
          color: "#fff",
          fontSize: 14,
        }}
      >
        <span>Total</span>
        <span>{formatINR(breakdown.total_cost)}</span>
      </div>
    </div>
  );
}
