"""Halo layout generator.

Distributes small stones in a circular ring around the center stone,
embedded in a thin annular base plate at the ring head.

Source of truth: jewelry-parametric-engine/SKILL.md
All dims in millimetres.

Coordinate convention (matches band.py / stone.py):
  - Ring axis: Y
  - Center stone is at X = ring_radius + band_thickness/2, Y = band_width/2
  - Halo ring lies in the XZ plane at the center-stone girdle level

Spacing math:
  R_halo = center_stone_radius + gap + halo_stone_radius
  Circumference C = 2π × R_halo
  N = floor(C / (halo_stone_diameter + min_spacing))
  θ = 2π / N  (uniform angular spacing → perfect symmetry)

CadQuery ops: annular extrude, sphere seat cuts, boolean union/cut.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import cadquery as cq

from app.schemas.parametric import ParametricRing, SideStoneLayout


# ── Constants ──────────────────────────────────────────────────────

MIN_SPACING_MM = 0.3        # Minimum gap between adjacent halo stones
GAP_TO_CENTER = 0.3         # Metal wall between center stone and halo stones
EMBED_RATIO = 0.40          # Stone embedded 40 % into halo base
BASE_PLATE_THICKNESS = 0.8  # mm — annular halo base plate height
BASE_PLATE_MARGIN = 0.3     # mm extra beyond halo stones outer edge


@dataclass
class HaloResult:
    """Output of the halo layout generator."""

    base_plate: cq.Workplane      # annular disc to union with ring head
    seat_cuts: cq.Workplane       # compound of all seat cavities (to subtract)
    stone_count: int              # actual number of halo stones placed


# ── Helpers ────────────────────────────────────────────────────────

def _auto_count(halo_radius: float, stone_diameter: float, spacing: float) -> int:
    """Calculate max number of halo stones from circumference."""
    circumference = 2.0 * math.pi * halo_radius
    per_stone = stone_diameter + spacing
    if per_stone <= 0:
        return 0
    return max(0, int(circumference / per_stone))


# ── Main builder ───────────────────────────────────────────────────

def build_halo(
    params: ParametricRing,
    layout: Optional[SideStoneLayout] = None,
) -> HaloResult:
    """Generate halo base plate and seat cuts around the center stone.

    Parameters
    ----------
    params : ParametricRing
        Full jewelry params (uses ring geometry + center stone).
    layout : SideStoneLayout | None
        Side stone layout config.  Falls back to params.side_stone_layout.

    Returns
    -------
    HaloResult with base_plate (union), seat_cuts (subtract), stone_count.
    """
    ssl = layout or params.side_stone_layout
    if ssl is None or not ssl.enabled:
        empty = cq.Workplane("XY")
        return HaloResult(base_plate=empty, seat_cuts=empty, stone_count=0)

    stone_d = ssl.diameter
    stone_r = stone_d / 2.0
    spacing = max(MIN_SPACING_MM, stone_d * 0.15)

    center_r = params.center_stone.diameter / 2.0

    # Halo circle radius: center stone edge + gap + halo stone center
    r_halo = center_r + GAP_TO_CENTER + stone_r

    # Stone count: auto-calculate or clamp to geometric max
    auto_n = _auto_count(r_halo, stone_d, spacing)
    if ssl.count > 0:
        n_stones = min(ssl.count, auto_n)
    else:
        n_stones = auto_n

    if n_stones < 3:
        # Too few stones for a credible halo — skip
        empty = cq.Workplane("XY")
        return HaloResult(base_plate=empty, seat_cuts=empty, stone_count=0)

    # Angular spacing (uniform)
    d_theta = 2.0 * math.pi / n_stones

    # ── Position context ───────────────────────────────────────────
    # Center stone X position on the ring
    cx = params.ring_radius + params.band_thickness / 2.0
    # Halo sits at the girdle level: Y = band_width/2 (top of band)
    cy = params.band_width / 2.0

    # ── Build annular base plate ───────────────────────────────────
    inner_r = center_r + GAP_TO_CENTER * 0.5
    outer_r = r_halo + stone_r + BASE_PLATE_MARGIN

    base_plate = (
        cq.Workplane("XZ")
        .transformed(offset=(cx, cy, 0))
        .circle(outer_r)
        .circle(inner_r)  # inner hole
        .extrude(BASE_PLATE_THICKNESS)
    )

    # ── Place halo stones ──────────────────────────────────────────
    seat_solids: list[cq.Workplane] = []

    for i in range(n_stones):
        angle = d_theta * i
        # Stone center relative to center-stone position
        sx = cx + r_halo * math.cos(angle)
        sz = r_halo * math.sin(angle)
        sy = cy + BASE_PLATE_THICKNESS * (1.0 - EMBED_RATIO)

        seat = (
            cq.Workplane("XY")
            .transformed(offset=(sx, sy, sz))
            .sphere(stone_r + 0.05)  # seat clearance
        )
        seat_solids.append(seat)

    # Combine seat cuts
    seat_compound = seat_solids[0]
    for s in seat_solids[1:]:
        seat_compound = seat_compound.union(s)

    return HaloResult(
        base_plate=base_plate,
        seat_cuts=seat_compound,
        stone_count=n_stones,
    )
