/**
 * Stone controls — diameter, prong count, shape.
 */

import React from "react";
import { PARAM_LIMITS, type StoneShape } from "../../types/jewelry";
import { useProjectStore } from "../../store/useProjectStore";

const selectStyle: React.CSSProperties = {
  width: "100%",
  padding: "6px 8px",
  borderRadius: 6,
  border: "1px solid #444",
  background: "#1a1a1a",
  color: "#e0e0e0",
  fontSize: 12,
  marginBottom: 12,
};

const sliderRow: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 4,
  marginBottom: 12,
};

const labelRow: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  fontSize: 12,
  color: "#ccc",
};

const SHAPES: { value: StoneShape; label: string }[] = [
  { value: "round", label: "Round" },
  { value: "oval", label: "Oval" },
  { value: "emerald", label: "Emerald" },
  { value: "pear", label: "Pear" },
];

export default function StoneControls() {
  const { currentParams, updateStone } = useProjectStore();
  const stone = currentParams.center_stone;

  return (
    <div>
      <h4 style={{ fontSize: 13, color: "#a78bfa", marginBottom: 12 }}>
        Center Stone
      </h4>

      {/* Shape selector */}
      <div style={{ marginBottom: 12 }}>
        <label style={{ fontSize: 12, color: "#ccc" }}>Shape</label>
        <select
          style={selectStyle}
          value={stone.type}
          onChange={(e) => updateStone({ type: e.target.value as StoneShape })}
        >
          {SHAPES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
      </div>

      {/* Diameter slider */}
      <div style={sliderRow}>
        <div style={labelRow}>
          <span>Diameter</span>
          <span>{stone.diameter.toFixed(1)} mm</span>
        </div>
        <input
          type="range"
          style={{ width: "100%", accentColor: "#a78bfa" }}
          min={PARAM_LIMITS.stone_diameter.min}
          max={PARAM_LIMITS.stone_diameter.max}
          step={PARAM_LIMITS.stone_diameter.step}
          value={stone.diameter}
          onChange={(e) => {
            const dia = parseFloat(e.target.value);
            updateStone({ diameter: dia, height: +(dia * 0.6).toFixed(2) });
          }}
        />
      </div>

      {/* Prong count slider */}
      <div style={sliderRow}>
        <div style={labelRow}>
          <span>Prongs</span>
          <span>{stone.prongs}</span>
        </div>
        <input
          type="range"
          style={{ width: "100%", accentColor: "#a78bfa" }}
          min={PARAM_LIMITS.stone_prongs.min}
          max={PARAM_LIMITS.stone_prongs.max}
          step={PARAM_LIMITS.stone_prongs.step}
          value={stone.prongs}
          onChange={(e) => updateStone({ prongs: parseInt(e.target.value) })}
        />
      </div>
    </div>
  );
}
