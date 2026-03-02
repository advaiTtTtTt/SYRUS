/**
 * Suggestion card — shows budget adjustment results.
 */

import React from "react";
import type { BudgetAdjustment } from "../../types/jewelry";

const cardStyle: React.CSSProperties = {
  background: "#1a1a2e",
  borderRadius: 8,
  padding: 12,
  marginTop: 12,
  fontSize: 12,
};

interface Props {
  adjustment: BudgetAdjustment;
}

export default function SuggestionCard({ adjustment }: Props) {
  return (
    <div style={cardStyle}>
      <div style={{ color: adjustment.budget_fit ? "#4ade80" : "#f87171", fontWeight: 600, marginBottom: 8 }}>
        {adjustment.budget_fit ? "✓ Budget fit achieved" : "✗ Cannot fit budget"}
      </div>
      {adjustment.changes_applied.length > 0 && (
        <div>
          <span style={{ color: "#aaa" }}>Changes:</span>
          <ul style={{ margin: "4px 0 0 16px", color: "#ccc" }}>
            {adjustment.changes_applied.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      )}
      <div style={{ marginTop: 8, color: "#aaa" }}>
        Cost: ₹{adjustment.original_cost.toLocaleString("en-IN")} →{" "}
        <span style={{ color: "#fff", fontWeight: 600 }}>
          ₹{adjustment.adjusted_cost.toLocaleString("en-IN")}
        </span>
      </div>
    </div>
  );
}
