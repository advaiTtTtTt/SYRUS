/**
 * Dimension sliders — ring_radius, band_width, band_thickness.
 */

import "./Customizer.css";
import { PARAM_LIMITS } from "../../types/jewelry";
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

export default function DimensionSliders() {
  const { currentParams, updateParams } = useProjectStore();

  return (
    <div>
      <h4 className="section-heading">Ring Dimensions</h4>
      <Slider
        label="Ring Radius"
        value={currentParams.ring_radius}
        {...PARAM_LIMITS.ring_radius}
        onChange={(v) => updateParams({ ring_radius: v })}
      />
      <Slider
        label="Band Width"
        value={currentParams.band_width}
        {...PARAM_LIMITS.band_width}
        onChange={(v) => updateParams({ band_width: v })}
      />
      <Slider
        label="Band Thickness"
        value={currentParams.band_thickness}
        {...PARAM_LIMITS.band_thickness}
        onChange={(v) => updateParams({ band_thickness: v })}
      />
    </div>
  );
}
