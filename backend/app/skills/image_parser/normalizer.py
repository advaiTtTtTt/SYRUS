"""Scale normalization — convert pixel ratios to mm dimensions.

Source of truth: jewelry-image-parser/SKILL.md

Since we cannot infer absolute scale from a single 2D image, we anchor
to the SKILL-defined default ring_radius (9 mm) and scale everything
proportionally from detected pixel ratios.

Perspective correction is applied when the detected ring is elliptical
rather than circular (indicating a non-frontal camera angle).

Parameter ranges (clamped per jewelry-parametric-engine SKILL):
  - ring_radius: 7.0–12.0 mm
  - band_width: 1.5–6.0 mm
  - band_thickness: 1.5–3.5 mm
  - stone diameter: 3.0–12.0 mm
  - prongs: 3–8
"""

from __future__ import annotations

from app.schemas.parametric import CenterStone, ParametricRing, StoneShape

from .measurer import Measurements

# Default scale anchors from SKILL
DEFAULT_RING_RADIUS = 9.0          # mm
DEFAULT_BAND_WIDTH = 2.2           # mm
DEFAULT_BAND_THICKNESS = 1.8       # mm
DEFAULT_STONE_DIAMETER = 6.0       # mm
DEFAULT_STONE_HEIGHT_RATIO = 0.60  # 60% of diameter


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def normalize_to_parametric(measurements: Measurements) -> ParametricRing:
    """Convert image measurements into a parametric ring definition.

    Scaling strategy:
      1. Anchor ring_radius to 9mm (SKILL default)
      2. Scale band_width from detected band_width_ratio
      3. Scale stone diameter from stone_to_ring_ratio
      4. Apply perspective correction factor
      5. Clamp all values to SKILL parameter ranges
    """

    # ── Ring dimensions ────────────────────────────────────────────
    ring_radius = DEFAULT_RING_RADIUS  # anchor

    if measurements.band_width_ratio > 0:
        ring_diameter = ring_radius * 2.0
        band_width = ring_diameter * measurements.band_width_ratio

        # Apply perspective correction (wider band appears narrower in perspective)
        if measurements.perspective_factor < 0.95:
            band_width /= max(measurements.perspective_factor, 0.6)

        band_width = _clamp(band_width, 1.5, 6.0)
    else:
        band_width = DEFAULT_BAND_WIDTH

    # Band thickness cannot be measured from a 2D front-facing image.
    # Estimate proportionally: thicker bands tend to be thicker in depth.
    if band_width > 3.0:
        band_thickness = _clamp(band_width * 0.7, 1.5, 3.5)
    else:
        band_thickness = DEFAULT_BAND_THICKNESS

    # ── Center stone ───────────────────────────────────────────────
    if measurements.stone_to_ring_ratio > 0:
        ring_diameter = ring_radius * 2.0
        stone_diameter = ring_diameter * measurements.stone_to_ring_ratio

        # Perspective correction for stone too
        if measurements.perspective_factor < 0.95:
            stone_diameter /= max(measurements.perspective_factor, 0.6)

        stone_diameter = _clamp(stone_diameter, 3.0, 12.0)
    else:
        stone_diameter = DEFAULT_STONE_DIAMETER

    stone_height = round(stone_diameter * DEFAULT_STONE_HEIGHT_RATIO, 2)

    # Shape
    shape_map = {
        "round": StoneShape.ROUND,
        "oval": StoneShape.OVAL,
        "emerald": StoneShape.EMERALD,
        "pear": StoneShape.PEAR,
    }
    stone_shape = shape_map.get(measurements.stone_shape, StoneShape.ROUND)

    # Prong count
    prong_count = measurements.detected_prong_count
    if prong_count < 3:
        prong_count = 4  # default per SKILL: unclear → default 4

    return ParametricRing(
        ring_radius=round(ring_radius, 2),
        band_width=round(band_width, 2),
        band_thickness=round(band_thickness, 2),
        center_stone=CenterStone(
            type=stone_shape,
            diameter=round(stone_diameter, 2),
            height=stone_height,
            prongs=_clamp(prong_count, 3, 8),
        ),
        setting_type="prong",  # default per SKILL: unclear → prong
        side_stones=[],        # MVP: no side stone detection
    )
