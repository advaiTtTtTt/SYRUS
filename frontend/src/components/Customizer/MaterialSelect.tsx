/**
 * Material selection — metal type & gemstone material.
 *
 * Per image-parser SKILL: metal type and gemstone color are
 * NEVER inferred from image — always user-selected.
 */

import React from "react";
import type { GemstoneMaterial, MetalType } from "../../types/jewelry";
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

const METALS: { value: MetalType; label: string }[] = [
  { value: "18k_gold", label: "18K Gold" },
  { value: "14k_gold", label: "14K Gold" },
  { value: "platinum", label: "Platinum" },
  { value: "silver", label: "Silver" },
];

const GEMS: { value: GemstoneMaterial; label: string }[] = [
  { value: "diamond", label: "Diamond" },
  { value: "ruby", label: "Ruby" },
  { value: "sapphire", label: "Sapphire" },
  { value: "emerald", label: "Emerald" },
  { value: "moissanite", label: "Moissanite" },
];

export default function MaterialSelect() {
  const { customization, updateCustomization } = useProjectStore();

  return (
    <div>
      <h4 style={{ fontSize: 13, color: "#a78bfa", marginBottom: 12 }}>
        Materials
      </h4>

      <div style={{ marginBottom: 8 }}>
        <label style={{ fontSize: 12, color: "#ccc" }}>Metal</label>
        <select
          style={selectStyle}
          value={customization.metal_type}
          onChange={(e) =>
            updateCustomization({ metal_type: e.target.value as MetalType })
          }
        >
          {METALS.map((m) => (
            <option key={m.value} value={m.value}>
              {m.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label style={{ fontSize: 12, color: "#ccc" }}>Gemstone</label>
        <select
          style={selectStyle}
          value={customization.gemstone_material}
          onChange={(e) =>
            updateCustomization({
              gemstone_material: e.target.value as GemstoneMaterial,
            })
          }
        >
          {GEMS.map((g) => (
            <option key={g.value} value={g.value}>
              {g.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
