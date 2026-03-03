/**
 * Jewelry type selector — ring / pendant / earring.
 *
 * When switching away from ring, resets ring-only settings
 * (setting_style → solitaire, side_stone_layout → null) so
 * the pricer doesn't apply pavé/halo multipliers to non-ring types.
 */

import "./Customizer.css";
import type { JewelryType, ParametricRing } from "../../types/jewelry";
import { useProjectStore } from "../../store/useProjectStore";

const TYPES: { value: JewelryType; label: string; icon: string }[] = [
  { value: "ring", label: "Ring", icon: "💍" },
  { value: "pendant", label: "Pendant", icon: "📿" },
  { value: "earring", label: "Earring", icon: "✨" },
];

export default function JewelryTypeSelector() {
  const { currentParams, updateParams } = useProjectStore();
  const currentType = currentParams.type ?? "ring";

  const handleTypeChange = (newType: JewelryType) => {
    if (newType === currentType) return;

    const updates: Partial<ParametricRing> = { type: newType };

    // Reset ring-only settings when switching away from ring
    if (newType !== "ring") {
      updates.setting_style = "solitaire";
      updates.side_stone_layout = null;
    }

    updateParams(updates);
  };

  return (
    <div>
      <h4 className="section-heading">Jewelry Type</h4>
      <div className="toggle-row">
        {TYPES.map((t) => (
          <button
            key={t.value}
            className={`toggle-btn ${
              currentType === t.value
                ? "toggle-btn--active"
                : "toggle-btn--inactive"
            }`}
            onClick={() => handleTypeChange(t.value)}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>
    </div>
  );
}
