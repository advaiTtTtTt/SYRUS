/**
 * Shared slider component — used across all dimension panels.
 *
 * Features:
 *   - Consistent styling via Customizer.css classes
 *   - Smart formatting (integer for step ≥ 1, decimal otherwise)
 *   - Accessible (aria-label, linked label)
 */

import "./Customizer.css";

export interface SliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  unit?: string;
  onChange: (v: number) => void;
}

export default function Slider({
  label,
  value,
  min,
  max,
  step,
  unit = "mm",
  onChange,
}: SliderProps) {
  const id = `slider-${label.toLowerCase().replace(/\s+/g, "-")}`;
  const display = step >= 1 ? String(value) : value.toFixed(1);

  return (
    <div className="slider-row">
      <div className="label-row">
        <label htmlFor={id}>{label}</label>
        <span>
          {display}
          {unit ? ` ${unit}` : ""}
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
