/**
 * Pendant dimension sliders — base_width, base_height, base_thickness, bail.
 */

import "./Customizer.css";
import { PARAM_LIMITS } from "../../types/jewelry";
import type { PendantParams, PendantBaseShape } from "../../types/jewelry";
import { useProjectStore } from "../../store/useProjectStore";

interface SliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  unit?: string;
  onChange: (v: number) => void;
}

function Slider({ label, value, min, max, step, unit = "mm", onChange }: SliderProps) {
  const id = label.toLowerCase().replace(/\s+/g, "-");
  return (
    <div className="slider-row">
      <div className="label-row">
        <label htmlFor={id}>{label}</label>
        <span>
          {value.toFixed(1)} {unit}
        </span>
      </div>
      <input
        id={id}
        type="range"
        className="range-slider"
        min={min}
        max={max}
        step={step}
        value={value}
        aria-label={label}
        onChange={(e) => onChange(parseFloat(e.target.value))}
      />
    </div>
  );
}

const SHAPES: { value: PendantBaseShape; label: string }[] = [
  { value: "circular", label: "Circular" },
  { value: "oval", label: "Oval" },
];

export default function PendantSliders() {
  const { currentParams, updateParams } = useProjectStore();
  const pp = currentParams.pendant_params ?? {
    base_shape: "circular" as PendantBaseShape,
    base_width: 15.0,
    base_height: 20.0,
    base_thickness: 2.0,
    bail_diameter: 5.0,
    bail_thickness: 1.5,
  };

  const update = (partial: Partial<PendantParams>) => {
    updateParams({ pendant_params: { ...pp, ...partial } });
  };

  return (
    <div>
      <h4 className="section-heading">Pendant Dimensions</h4>

      <div className="form-group-sm">
        <label htmlFor="pendant-shape" className="form-label">Base Shape</label>
        <select
          id="pendant-shape"
          className="customizer-select"
          title="Select pendant base shape"
          value={pp.base_shape}
          onChange={(e) => update({ base_shape: e.target.value as PendantBaseShape })}
        >
          {SHAPES.map((s) => (
            <option key={s.value} value={s.value}>{s.label}</option>
          ))}
        </select>
      </div>

      <Slider
        label="Base Width"
        value={pp.base_width}
        {...PARAM_LIMITS.pendant_base_width}
        onChange={(v) => update({ base_width: v })}
      />
      <Slider
        label="Base Height"
        value={pp.base_height}
        {...PARAM_LIMITS.pendant_base_height}
        onChange={(v) => update({ base_height: v })}
      />
      <Slider
        label="Thickness"
        value={pp.base_thickness}
        {...PARAM_LIMITS.pendant_base_thickness}
        onChange={(v) => update({ base_thickness: v })}
      />
      <Slider
        label="Bail Diameter"
        value={pp.bail_diameter}
        {...PARAM_LIMITS.pendant_bail_diameter}
        onChange={(v) => update({ bail_diameter: v })}
      />
      <Slider
        label="Bail Thickness"
        value={pp.bail_thickness}
        {...PARAM_LIMITS.pendant_bail_thickness}
        onChange={(v) => update({ bail_thickness: v })}
      />
    </div>
  );
}
