/**
 * Stone controls — diameter, prong count, shape.
 */

import "./Customizer.css";
import { PARAM_LIMITS, type StoneShape } from "../../types/jewelry";
import { useProjectStore } from "../../store/useProjectStore";

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
      <h4 className="section-heading">Center Stone</h4>

      {/* Shape selector */}
      <div className="form-group">
        <label htmlFor="shape-select" className="form-label">Shape</label>
        <select
          id="shape-select"
          className="customizer-select"
          title="Select stone shape"
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
      <div className="slider-row">
        <div className="label-row">
          <label htmlFor="diameter-slider">Diameter</label>
          <span>{stone.diameter.toFixed(1)} mm</span>
        </div>
        <input
          id="diameter-slider"
          type="range"
          className="range-slider"
          min={PARAM_LIMITS.stone_diameter.min}
          max={PARAM_LIMITS.stone_diameter.max}
          step={PARAM_LIMITS.stone_diameter.step}
          value={stone.diameter}
          aria-label="Stone diameter"
          onChange={(e) => {
            const dia = parseFloat(e.target.value);
            updateStone({ diameter: dia, height: +(dia * 0.6).toFixed(2) });
          }}
        />
      </div>

      {/* Prong count slider */}
      <div className="slider-row">
        <div className="label-row">
          <label htmlFor="prong-slider">Prongs</label>
          <span>{stone.prongs}</span>
        </div>
        <input
          id="prong-slider"
          type="range"
          className="range-slider"
          min={PARAM_LIMITS.stone_prongs.min}
          max={PARAM_LIMITS.stone_prongs.max}
          step={PARAM_LIMITS.stone_prongs.step}
          value={stone.prongs}
          aria-label="Number of prongs"
          onChange={(e) => updateStone({ prongs: parseInt(e.target.value) })}
        />
      </div>
    </div>
  );
}
