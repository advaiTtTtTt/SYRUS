"""Scale normalization — convert pixel ratios to mm dimensions.

Source of truth: jewelry-image-parser/SKILL.md

Scale normalization defaults (when real-world scale unknown):
  - ring_radius = 9 mm
  - band_width = 2.2 mm
  - band_thickness = 1.8 mm
  - All other dimensions scaled proportionally
"""

from __future__ import annotations

from app.schemas.parametric import CenterStone, ParametricRing, StoneShape

from .measurer import Measurements

# Default scale anchors from SKILL
DEFAULT_RING_RADIUS = 9.0      # mm
DEFAULT_BAND_WIDTH = 2.2       # mm
DEFAULT_BAND_THICKNESS = 1.8   # mm
DEFAULT_STONE_DIAMETER = 6.0   # mm
DEFAULT_STONE_HEIGHT_RATIO = 0.60  # 60% of diameter


def normalize_to_parametric(measurements: Measurements) -> ParametricRing:
    """Convert image measurements into a parametric ring definition.

    Since we don't know absolute scale from a 2D image, we use
    the SKILL-defined default ring_radius as anchor and scale
    everything proportionally.
    """

    # ── Ring dimensions ────────────────────────────────────────────
    ring_radius = DEFAULT_RING_RADIUS  # anchor

    if measurements.band_width_ratio > 0:
        # Scale band_width proportionally to the ring diameter
        ring_diameter = ring_radius * 2.0
        band_width = ring_diameter * measurements.band_width_ratio
        # Clamp to reasonable range
        band_width = max(1.5, min(6.0, band_width))
    else:
        band_width = DEFAULT_BAND_WIDTH

    band_thickness = DEFAULT_BAND_THICKNESS  # not measurable from 2D image

    # ── Center stone ───────────────────────────────────────────────
    if measurements.stone_to_ring_ratio > 0:
        stone_diameter = ring_radius * 2.0 * measurements.stone_to_ring_ratio
        stone_diameter = max(3.0, min(12.0, stone_diameter))
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
        ring_radius=ring_radius,
        band_width=round(band_width, 2),
        band_thickness=band_thickness,
        center_stone=CenterStone(
            type=stone_shape,
            diameter=round(stone_diameter, 2),
            height=stone_height,
            prongs=min(8, max(3, prong_count)),
        ),
        setting_type="prong",  # default per SKILL: unclear → prong
        side_stones=[],  # MVP: no side stone detection
    )
