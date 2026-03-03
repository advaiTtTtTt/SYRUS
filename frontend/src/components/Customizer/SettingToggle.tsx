/**
 * Setting type toggle + setting style selector.
 *
 * Setting type: prong vs bezel (bezel disabled in Phase 2).
 * Setting style: solitaire / pavé shoulder / halo / cathedral.
 */

import "./Customizer.css";
import type { SettingType, SettingStyle, SideStoneLayout } from "../../types/jewelry";
import { useProjectStore } from "../../store/useProjectStore";

const STYLES: { value: SettingStyle; label: string }[] = [
  { value: "solitaire", label: "Solitaire" },
  { value: "pave_shoulder", label: "Pavé" },
  { value: "halo", label: "Halo" },
  { value: "cathedral", label: "Cathedral" },
];

/** Default side stone layout per style. */
const SSL_DEFAULTS: Record<string, SideStoneLayout> = {
  pave_shoulder: { enabled: true, pattern: "pave", count: 10, diameter: 1.5, rows: 1 },
  halo: { enabled: true, pattern: "halo", count: 12, diameter: 1.3, rows: 1 },
  cathedral: { enabled: false, pattern: "pave", count: 0, diameter: 1.5, rows: 1 },
};

export default function SettingToggle() {
  const { currentParams, updateParams } = useProjectStore();
  const currentStyle = currentParams.setting_style ?? "solitaire";

  const handleStyleChange = (style: SettingStyle) => {
    const updates: Partial<typeof currentParams> = { setting_style: style };
    if (style === "solitaire") {
      updates.side_stone_layout = null;
    } else if (!currentParams.side_stone_layout?.enabled) {
      updates.side_stone_layout = SSL_DEFAULTS[style] ?? SSL_DEFAULTS.pave_shoulder;
    }
    updateParams(updates);
  };

  return (
    <div>
      <h4 className="section-heading">Setting Type</h4>
      <div className="toggle-row">
        <button
          className={`toggle-btn ${currentParams.setting_type === "prong" ? "toggle-btn--active" : "toggle-btn--inactive"}`}
          onClick={() => updateParams({ setting_type: "prong" as SettingType })}
        >
          Prong
        </button>
        <button
          className="toggle-btn toggle-btn--inactive toggle-btn--disabled"
          disabled
          title="Bezel setting — coming in Phase 2"
        >
          Bezel
        </button>
      </div>

      <h4 className="section-heading" style={{ marginTop: 16 }}>Setting Style</h4>
      <div className="toggle-row" style={{ flexWrap: "wrap" }}>
        {STYLES.map((s) => (
          <button
            key={s.value}
            className={`toggle-btn ${
              currentStyle === s.value
                ? "toggle-btn--active"
                : "toggle-btn--inactive"
            }`}
            onClick={() => handleStyleChange(s.value)}
          >
            {s.label}
          </button>
        ))}
      </div>
    </div>
  );
}
