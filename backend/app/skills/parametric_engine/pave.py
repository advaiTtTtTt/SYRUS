"""Pavé shoulder stone generator.

Distributes small stones along the upper arc of a ring band's shoulders,
with bead-set micro-prong supports between adjacent stones.

Source of truth: jewelry-parametric-engine/SKILL.md
All dims in millimetres.

Coordinate convention (matches band.py):
  - Ring axis: Y
  - Band center: origin
  - Outer radius: ring_radius + band_thickness
  - Stone head at top-dead-center (angle = 0 in XZ plane)

Geometric approach:
  1. Compute placement radius (band outer surface).
  2. Compute angular pitch from stone diameter + min spacing.
  3. Place stones symmetrically on both shoulders (±15° to ±90° arcs).
  4. Each stone: sphere embedded 40% into band surface.
  5. Bead-set micro-prongs between adjacent stones.
  6. Multi-row: offset rows along Y with half-pitch stagger.

CadQuery ops used: sphere, cylinder, loft, boolean union/cut.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import cadquery as cq

from app.schemas.parametric import ParametricRing, SideStoneLayout


# ── Constants ──────────────────────────────────────────────────────

MIN_SPACING_MM = 0.3          # Minimum gap between adjacent pavé stones
EMBED_RATIO = 0.40            # Stone embedded 40 % into band surface
MICRO_PRONG_HEIGHT = 0.4      # mm — bead prong above band surface
MICRO_PRONG_RADIUS = 0.25     # mm — bead prong base radius

# Angular exclusion zone around center-stone head (radians each side)
HEAD_EXCLUSION_RAD = math.radians(15)
# Maximum arc extent for shoulder stones (radians each side from head)
MAX_ARC_RAD = math.radians(90)


@dataclass
class PaveResult:
    """Output of the pavé shoulder generator."""

    seat_cuts: cq.Workplane       # compound of all seat cavities (to subtract)
    micro_prongs: cq.Workplane    # compound of all bead-set supports (to add)
    stone_count: int              # actual number of stones placed


# ── Helpers ────────────────────────────────────────────────────────

def _angular_pitch(stone_diameter: float, spacing: float, radius: float) -> float:
    """Angular step (radians) for evenly spaced stones along an arc."""
    arc_per_stone = stone_diameter + spacing
    return arc_per_stone / radius


def _max_stones_per_shoulder(
    stone_diameter: float,
    spacing: float,
    radius: float,
    arc_start: float = HEAD_EXCLUSION_RAD,
    arc_end: float = MAX_ARC_RAD,
) -> int:
    """Max number of stones that fit in one shoulder arc."""
    arc_length = (arc_end - arc_start) * radius
    return max(0, int(arc_length / (stone_diameter + spacing)))


# ── Main builder ───────────────────────────────────────────────────

def build_pave_shoulder(
    params: ParametricRing,
    layout: Optional[SideStoneLayout] = None,
) -> PaveResult:
    """Generate pavé shoulder seat cuts and micro-prong supports.

    Parameters
    ----------
    params : ParametricRing
        Full jewelry params (uses ring_radius, band_width, band_thickness).
    layout : SideStoneLayout | None
        Side stone layout config.  Falls back to params.side_stone_layout.

    Returns
    -------
    PaveResult with seat_cuts (subtract from band) and micro_prongs (union).
    """
    ssl = layout or params.side_stone_layout
    if ssl is None or not ssl.enabled:
        # Nothing to do — return empty compounds
        empty = cq.Workplane("XY")
        return PaveResult(seat_cuts=empty, micro_prongs=empty, stone_count=0)

    stone_d = ssl.diameter
    stone_r = stone_d / 2.0
    spacing = max(MIN_SPACING_MM, stone_d * 0.15)  # at least 15 % of diameter
    rows = ssl.rows  # 1–3

    r_outer = params.ring_radius + params.band_thickness
    half_bw = params.band_width / 2.0

    # Placement radius: stones sit on the outer surface
    r_place = r_outer

    pitch = _angular_pitch(stone_d, spacing, r_place)
    max_per_shoulder = _max_stones_per_shoulder(stone_d, spacing, r_place)

    # Requested count per shoulder (0 = auto-fill)
    if ssl.count > 0:
        per_shoulder = min(ssl.count // 2, max_per_shoulder)
    else:
        per_shoulder = max_per_shoulder

    if per_shoulder == 0:
        empty = cq.Workplane("XY")
        return PaveResult(seat_cuts=empty, micro_prongs=empty, stone_count=0)

    total_placed = 0
    seat_solids: list[cq.Workplane] = []
    prong_solids: list[cq.Workplane] = []

    embed_depth = stone_r * EMBED_RATIO  # how deep stone sinks into band

    for row_idx in range(rows):
        # Y offset for multi-row: center row at Y = half_bw (top surface),
        # additional rows step inward
        y_offset = half_bw - row_idx * (stone_d + spacing * 0.5)
        if y_offset < -half_bw + stone_r:
            break  # no room for another row

        # Half-pitch stagger for even rows (hexagonal close-pack)
        stagger = pitch / 2.0 if row_idx % 2 == 1 else 0.0

        for side in (+1, -1):  # positive and negative shoulder arcs
            for i in range(per_shoulder):
                angle = side * (HEAD_EXCLUSION_RAD + pitch * 0.5 + pitch * i + stagger)

                # Stone center on the outer surface of the torus
                sx = r_place * math.cos(angle)
                sz = r_place * math.sin(angle)
                sy = y_offset

                # Seat cut: sphere slightly larger than stone (clearance)
                seat = (
                    cq.Workplane("XY")
                    .transformed(offset=(sx, sy, sz))
                    .sphere(stone_r + 0.05)
                )
                seat_solids.append(seat)

                # Micro-prong (bead set): small tapered nub between stones
                # Place at midpoint between this stone and the next one
                if i < per_shoulder - 1:
                    next_angle = side * (HEAD_EXCLUSION_RAD + pitch * 0.5 + pitch * (i + 1) + stagger)
                    mid_angle = (angle + next_angle) / 2.0
                    mx = r_place * math.cos(mid_angle)
                    mz = r_place * math.sin(mid_angle)

                    prong = (
                        cq.Workplane("XY")
                        .transformed(offset=(mx, sy, mz))
                        .circle(MICRO_PRONG_RADIUS)
                        .workplane(offset=MICRO_PRONG_HEIGHT)
                        .circle(MICRO_PRONG_RADIUS * 0.5)
                        .loft()
                    )
                    prong_solids.append(prong)

                total_placed += 1

    # Combine into compound solids
    seat_compound = seat_solids[0]
    for s in seat_solids[1:]:
        seat_compound = seat_compound.union(s)

    if prong_solids:
        prong_compound = prong_solids[0]
        for p in prong_solids[1:]:
            prong_compound = prong_compound.union(p)
    else:
        prong_compound = cq.Workplane("XY")

    return PaveResult(
        seat_cuts=seat_compound,
        micro_prongs=prong_compound,
        stone_count=total_placed,
    )
