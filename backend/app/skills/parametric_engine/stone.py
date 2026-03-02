"""Center stone placeholder geometry.

The stone is modeled as a simple geometric placeholder (not the actual
gemstone — that's for rendering). For CAD purposes it defines:
  - The volume the stone occupies (for boolean operations)
  - The seat cut dimensions
  - The prong contact surface

We model a round stone as a double-cone (pavilion + crown) which is the
simplest manufacturable approximation for CAD boolean ops.
"""

from __future__ import annotations

import cadquery as cq
import math

from app.schemas.parametric import CenterStone, ParametricRing


def build_stone_placeholder(params: ParametricRing) -> cq.Workplane:
    """Build a simplified stone shape for boolean seat-cutting.

    Stone sits at top of band, centered at X=0, Z = ring_radius + band_thickness/2.
    The stone axis is along Y (pointing up from band).

    For MVP (round stones only), we use a cone+cylinder approximation.
    """
    stone = params.center_stone
    r = stone.diameter / 2.0
    h = stone.height

    # Seat depth: 20% of stone height (midpoint of 15–25% SKILL range)
    seat_depth = h * 0.20

    # Crown height (above girdle): total height - seat depth
    crown_h = h - seat_depth

    # Position: stone center at the top of the band
    # Band outer surface is at X = ring_radius + band_thickness from origin
    # Stone sits at the top (positive Y) centered on the band
    stone_center_x = 0
    stone_center_y = params.band_width / 2.0  # top of band

    # Build stone as a revolved profile (simplified brilliant cut)
    # Profile in XZ: pavilion cone tip at bottom, girdle at middle, crown at top
    profile = (
        cq.Workplane("XZ")
        .moveTo(0, -seat_depth)           # pavilion tip (bottom)
        .lineTo(r, 0)                      # girdle
        .lineTo(r * 0.7, crown_h)          # crown top edge
        .lineTo(0, crown_h)                # center top
        .close()
    )

    stone_solid = profile.revolve(360, (0, 0, 0), (0, 0, 1))

    # Translate to position on ring
    # Stone sits at the top of the band: translate to (ring_radius + band_thickness/2, band_width/2 + crown offset, 0)
    x_pos = params.ring_radius + params.band_thickness / 2.0
    y_pos = params.band_width / 2.0 - seat_depth

    stone_solid = stone_solid.translate((x_pos, y_pos, 0))

    return stone_solid


def get_seat_cutter(params: ParametricRing) -> cq.Workplane:
    """Build a shape to boolean-cut the stone seat from the band.

    The seat is a cylinder that removes material from the band top
    to accept the stone pavilion. Depth = 15–25% of stone height.
    """
    stone = params.center_stone
    r = stone.diameter / 2.0
    seat_depth = stone.height * 0.20  # 20% — safe middle of SKILL range

    # Seat is a cylinder slightly larger than stone (clearance)
    seat_r = r + 0.05  # 0.05mm clearance

    x_pos = params.ring_radius + params.band_thickness / 2.0
    y_start = params.band_width / 2.0 + 0.1  # start just above band top

    seat = (
        cq.Workplane("XY")
        .transformed(offset=(x_pos, y_start, 0))
        .circle(seat_r)
        .extrude(-(seat_depth + 0.1))  # cut downward into band
    )

    return seat
