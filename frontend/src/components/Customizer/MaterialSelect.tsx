/**
 * Material selection — metal type & gemstone material.
 *
 * Per image-parser SKILL: metal type and gemstone color are
 * NEVER inferred from image — always user-selected.
 */

import "./Customizer.css";
import type { GemstoneMaterial, MetalType } from "../../types/jewelry";
import { useProjectStore } from "../../store/useProjectStore";

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
      <h4 className="section-heading">Materials</h4>

      <div className="form-group-sm">
        <label htmlFor="metal-select" className="form-label">Metal</label>
        <select
          id="metal-select"
          className="customizer-select"
          title="Select metal type"
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
        <label htmlFor="gem-select" className="form-label">Gemstone</label>
        <select
          id="gem-select"
          className="customizer-select"
          title="Select gemstone material"
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
