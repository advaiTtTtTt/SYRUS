"""Bezel setting generation.

Source of truth: jewelry-parametric-engine/SKILL.md

Bezel rules:
  - Wall thickness ≥ 0.8 mm
  - Height 20–30% of stone height above girdle
  - Must include internal seat lip
  - No sharp internal corners

NOTE: Bezel is Phase 2 (ENABLE_BEZEL_SETTING feature flag).
This module provides a stub implementation.
"""

from __future__ import annotations

import cadquery as cq

from app.schemas.parametric import ParametricRing

BEZEL_WALL_MIN = 0.8
BEZEL_HEIGHT_RATIO_MIN = 0.20
BEZEL_HEIGHT_RATIO_MAX = 0.30


def build_bezel(params: ParametricRing) -> cq.Workplane:
    """Generate a bezel setting around the center stone.

    Phase 2 implementation — currently raises NotImplementedError.
    """
    raise NotImplementedError(
        "Bezel setting is Phase 2. Use prong setting for MVP."
    )
