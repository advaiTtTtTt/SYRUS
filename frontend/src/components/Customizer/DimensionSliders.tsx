/**
 * Dimension sliders — ring_radius, band_width, band_thickness.
 */

import { PARAM_LIMITS } from "../../types/jewelry";
import { useProjectStore } from "../../store/useProjectStore";
import Slider from "./Slider";

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
