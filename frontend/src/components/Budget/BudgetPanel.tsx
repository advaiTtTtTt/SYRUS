/**
 * Budget panel — cost display + budget target input.
 */

import React, { useState } from "react";
import { useProjectStore } from "../../store/useProjectStore";
import { useBudget } from "../../hooks/useBudget";
import type { BudgetAdjustment } from "../../types/jewelry";
import CostBreakdownView from "./CostBreakdown";
import SuggestionCard from "./SuggestionCard";

const panelStyle: React.CSSProperties = {
  padding: 16,
  background: "#111",
  borderRadius: 12,
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "6px 8px",
  borderRadius: 6,
  border: "1px solid #444",
  background: "#1a1a1a",
  color: "#e0e0e0",
  fontSize: 12,
};

const btnStyle: React.CSSProperties = {
  width: "100%",
  padding: "8px 12px",
  borderRadius: 6,
  border: "none",
  background: "#a78bfa",
  color: "#000",
  fontSize: 12,
  fontWeight: 600,
  cursor: "pointer",
  marginTop: 8,
};

export default function BudgetPanel() {
  const budgetResult = useProjectStore((s) => s.budgetResult);
  const isBuilding = useProjectStore((s) => s.isBuilding);
  const [targetBudget, setTargetBudget] = useState("");
  const [adjustment, setAdjustment] = useState<BudgetAdjustment | null>(null);
  const [loading, setLoading] = useState(false);
  const { applyBudgetAdjustment } = useBudget();

  const handleAdjust = async () => {
    const budget = parseFloat(targetBudget);
    if (isNaN(budget) || budget <= 0) return;
    setLoading(true);
    try {
      const result = await applyBudgetAdjustment(budget);
      setAdjustment(result);
    } catch {
      // Error handled elsewhere
    }
    setLoading(false);
  };

  return (
    <div style={panelStyle}>
      <h3 style={{ fontSize: 15, fontWeight: 600, color: "#fff", marginBottom: 12 }}>
        Budget
      </h3>

      {budgetResult ? (
        <CostBreakdownView breakdown={budgetResult.breakdown} />
      ) : (
        <div style={{ fontSize: 12, color: "#666", padding: "8px 0" }}>
          {isBuilding ? "Calculating cost..." : "Adjust a parameter to see cost"}
        </div>
      )}

      <div style={{ marginTop: 16 }}>
        <label style={{ fontSize: 12, color: "#ccc" }}>Target Budget (₹)</label>
        <input
          style={inputStyle}
          type="number"
          min="1"
          placeholder="e.g. 50000"
          value={targetBudget}
          onChange={(e) => setTargetBudget(e.target.value)}
        />
        <button
          style={{
            ...btnStyle,
            opacity: loading ? 0.6 : 1,
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 8,
          }}
          onClick={handleAdjust}
          disabled={loading}
        >
          {loading && <span className="spinner" />}
          {loading ? "Adjusting..." : "Fit to Budget"}
        </button>
      </div>

      {adjustment && <SuggestionCard adjustment={adjustment} />}
    </div>
  );
}
