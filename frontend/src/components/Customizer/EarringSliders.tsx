/**
 * Earring dimension sliders — stud_diameter, stud_thickness, pin_length, pin_diameter.
 */

import { PARAM_LIMITS } from "../../types/jewelry";
import type { EarringParams } from "../../types/jewelry";
import { useProjectStore } from "../../store/useProjectStore";
import Slider from "./Slider";

export default function EarringSliders() {
  const { currentParams, updateParams } = useProjectStore();
  const ep = currentParams.earring_params ?? {
    stud_diameter: 6.0,
    stud_thickness: 1.5,
    pin_length: 10.0,
    pin_diameter: 0.8,
  };

  const update = (partial: Partial<EarringParams>) => {
    updateParams({ earring_params: { ...ep, ...partial } });
  };

  return (
    <div>
      <h4 className="section-heading">Earring Dimensions</h4>
      <Slider
        label="Stud Diameter"
        value={ep.stud_diameter}
        {...PARAM_LIMITS.earring_stud_diameter}
        onChange={(v) => update({ stud_diameter: v })}
      />
      <Slider
        label="Stud Thickness"
        value={ep.stud_thickness}
        {...PARAM_LIMITS.earring_stud_thickness}
        onChange={(v) => update({ stud_thickness: v })}
      />
      <Slider
        label="Pin Length"
        value={ep.pin_length}
        {...PARAM_LIMITS.earring_pin_length}
        onChange={(v) => update({ pin_length: v })}
      />
      <Slider
        label="Pin Diameter"
        value={ep.pin_diameter}
        {...PARAM_LIMITS.earring_pin_diameter}
        onChange={(v) => update({ pin_diameter: v })}
      />
    </div>
  );
}
