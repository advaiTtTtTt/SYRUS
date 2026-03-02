/**
 * Dimension sliders — ring_radius, band_width, band_thickness.
 */

import React from "react";
import { PARAM_LIMITS } from "../../types/jewelry";
import { useProjectStore } from "../../store/useProjectStore";

const sliderStyle: React.CSSProperties = {
  width: "100%",
  accentColor: "#a78bfa",
};

const rowStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 4,
  marginBottom: 12,
};

const labelStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  fontSize: 12,
  color: "#ccc",
};

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
  return (
    <div style={rowStyle}>
      <div style={labelStyle}>
        <span>{label}</span>
        <span>
          {value.toFixed(1)} {unit}
        </span>
      </div>
      <input
        type="range"
        style={sliderStyle}
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
      />
    </div>
  );
}

export default function DimensionSliders() {
  const { currentParams, updateParams } = useProjectStore();

  return (
    <div>
      <h4 style={{ fontSize: 13, color: "#a78bfa", marginBottom: 12 }}>
        Ring Dimensions
      </h4>
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
