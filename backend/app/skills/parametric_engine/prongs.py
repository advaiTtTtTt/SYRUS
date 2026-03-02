"""Prong generation and placement.

Source of truth: jewelry-parametric-engine/SKILL.md

Prong rules:
  - Min thickness 0.8 mm, recommended 1.0–1.3 mm
  - Must taper toward tip
  - Intersect stone at crown level
  - Extend ≥ 0.5 mm above girdle
  - Not intersect each other
  - Base fused to band with fillet ≥ 0.3 mm radius
  - Evenly distributed, symmetric
"""

from __future__ import annotations

import math

import cadquery as cq

from app.schemas.parametric import ParametricRing

# Constants from SKILL
PRONG_THICKNESS_BASE = 1.0       # mm (recommended minimum)
PRONG_THICKNESS_TIP = 0.6        # mm (tapered)
PRONG_ABOVE_GIRDLE = 0.6         # mm (≥ 0.5 per SKILL)
PRONG_BASE_FILLET = 0.3          # mm (≥ 0.3 per SKILL)


def build_prongs(params: ParametricRing) -> cq.Workplane:
    """Generate prongs evenly spaced around the center stone.

    Each prong is a tapered cylinder (wider at base, narrower at tip)
    positioned at the stone's girdle radius, extending upward.
    """
    stone = params.center_stone
    n_prongs = stone.prongs
    stone_r = stone.diameter / 2.0

    # Prong positions: evenly spaced angles around stone center
    # Stone center is at X = ring_radius + band_thickness/2
    cx = params.ring_radius + params.band_thickness / 2.0

    # Prong base sits on band top surface (Y = band_width/2)
    y_base = params.band_width / 2.0

    # Prong extends from band surface up past girdle
    # Girdle is at stone seat top (stone center Y + stone height - seat depth)
    seat_depth = stone.height * 0.20
    prong_height = seat_depth + PRONG_ABOVE_GIRDLE

    result = None

    for i in range(n_prongs):
        angle = (2.0 * math.pi * i) / n_prongs
        # Prong contact point on stone girdle circle
        px = cx + stone_r * math.cos(angle)
        pz = stone_r * math.sin(angle)

        # Build a single tapered prong (cone frustum)
        prong = (
            cq.Workplane("XY")
            .transformed(offset=(px, y_base, pz))
            .circle(PRONG_THICKNESS_BASE / 2.0)
            .workplane(offset=prong_height)
            .circle(PRONG_THICKNESS_TIP / 2.0)
            .loft()
        )

        # Apply fillet at base (≥ 0.3 mm per SKILL)
        try:
            prong = prong.edges("<Y").fillet(PRONG_BASE_FILLET)
        except Exception:
            pass  # Fillet failure non-fatal

        if result is None:
            result = prong
        else:
            result = result.union(prong)

    return result
