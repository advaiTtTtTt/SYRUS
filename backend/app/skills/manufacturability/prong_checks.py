"""Prong validation checks.

Source of truth: manufacturability-validator/SKILL.md

Rules:
  - Min prong thickness: 0.8 mm (recommended 1.0–1.3 mm)
  - Must extend ≥ 0.5 mm above girdle
  - Base fusion depth ≥ 0.4 mm
  - Must not intersect each other
  - Must be tapered (no cylindrical rods)
  - Too thin → increase to 0.8 mm
  - Intersecting → recalculate angular spacing
"""

from __future__ import annotations

import math

from app.schemas.parametric import ParametricRing

PRONG_THICKNESS_MIN = 0.8
PRONG_ABOVE_GIRDLE_MIN = 0.5
PRONG_BASE_FUSION_MIN = 0.4


def check_prongs(
    params: ParametricRing,
    violations: list[str],
    corrections: list[str],
) -> ParametricRing:
    """Validate prong configuration for manufacturability."""
    if params.setting_type.value != "prong":
        return params

    stone = params.center_stone

    # ── Prong count vs stone diameter ──────────────────────────────
    # Check angular spacing: prongs evenly spaced around stone perimeter
    circumference = math.pi * stone.diameter
    spacing = circumference / stone.prongs

    # Each prong occupies ~PRONG_THICKNESS_MIN along the perimeter
    if spacing < PRONG_THICKNESS_MIN * 2:
        # Prongs would overlap — reduce count
        max_prongs = max(3, int(circumference / (PRONG_THICKNESS_MIN * 2)))
        corrections.append(
            f"Reduced prong count {stone.prongs} → {max_prongs} (overlap at stone diameter {stone.diameter} mm)"
        )
        stone.prongs = max_prongs

    # ── Prong reach validation ─────────────────────────────────────
    # Prongs must extend above girdle by ≥ 0.5 mm.
    # Girdle is roughly at stone height midpoint. We validate seat depth later.
    # Here we just ensure stone height allows prong extension.
    min_stone_height_for_prongs = PRONG_ABOVE_GIRDLE_MIN + (stone.diameter * 0.15)
    if stone.height < min_stone_height_for_prongs:
        corrections.append(
            f"Increased stone height {stone.height} → {round(min_stone_height_for_prongs, 2)} mm for prong clearance"
        )
        stone.height = round(min_stone_height_for_prongs, 2)

    return params
