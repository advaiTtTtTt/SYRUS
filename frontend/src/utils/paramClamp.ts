/**
 * Client-side parameter range enforcement.
 * Mirrors backend/app/skills/parametric_engine/constraints.py
 */

import { PARAM_LIMITS, type ParametricRing } from "../types/jewelry";

export function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

export function clampParams(params: ParametricRing): ParametricRing {
  return {
    ...params,
    ring_radius: clamp(params.ring_radius, PARAM_LIMITS.ring_radius.min, PARAM_LIMITS.ring_radius.max),
    band_width: clamp(params.band_width, PARAM_LIMITS.band_width.min, PARAM_LIMITS.band_width.max),
    band_thickness: clamp(params.band_thickness, PARAM_LIMITS.band_thickness.min, PARAM_LIMITS.band_thickness.max),
    center_stone: {
      ...params.center_stone,
      diameter: clamp(params.center_stone.diameter, PARAM_LIMITS.stone_diameter.min, PARAM_LIMITS.stone_diameter.max),
      prongs: clamp(params.center_stone.prongs, PARAM_LIMITS.stone_prongs.min, PARAM_LIMITS.stone_prongs.max),
    },
  };
}
