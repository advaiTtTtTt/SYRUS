/**
 * Side stone layout controls — shown when setting_style is not solitaire.
 *
 * Controls: count, diameter, rows.
 */

import { PARAM_LIMITS } from "../../types/jewelry";
import type { SideStoneLayout, SideStonePattern } from "../../types/jewelry";
import { useProjectStore } from "../../store/useProjectStore";
import Slider from "./Slider";

const PATTERNS: { value: SideStonePattern; label: string }[] = [
  { value: "pave", label: "Pavé" },
  { value: "channel", label: "Channel" },
  { value: "halo", label: "Halo" },
];

export default function SideStoneControls() {
  const { currentParams, updateParams } = useProjectStore();
  const style = currentParams.setting_style ?? "solitaire";

  // Don't show for solitaire
  if (style === "solitaire") return null;

  const ssl: SideStoneLayout = currentParams.side_stone_layout ?? {
    enabled: true,
    pattern: style === "halo" ? "halo" : "pave",
    count: 10,
    diameter: 1.5,
    rows: 1,
  };

  const update = (partial: Partial<SideStoneLayout>) => {
    updateParams({ side_stone_layout: { ...ssl, ...partial } });
  };

  return (
    <div>
      <h4 className="section-heading">Side Stone Layout</h4>

      <div className="form-group-sm">
        <label htmlFor="ssl-pattern" className="form-label">Pattern</label>
        <select
          id="ssl-pattern"
          className="customizer-select"
          title="Select side stone pattern"
          value={ssl.pattern}
          onChange={(e) => update({ pattern: e.target.value as SideStonePattern })}
        >
          {PATTERNS.map((p) => (
            <option key={p.value} value={p.value}>{p.label}</option>
          ))}
        </select>
      </div>

      <Slider
        label="Stone Count"
        value={ssl.count}
        {...PARAM_LIMITS.ssl_count}
        unit=""
        onChange={(v) => update({ count: v })}
      />
      <Slider
        label="Stone Diameter"
        value={ssl.diameter}
        {...PARAM_LIMITS.ssl_diameter}
        onChange={(v) => update({ diameter: v })}
      />
      <Slider
        label="Rows"
        value={ssl.rows}
        {...PARAM_LIMITS.ssl_rows}
        unit=""
        onChange={(v) => update({ rows: v })}
      />
    </div>
  );
}
