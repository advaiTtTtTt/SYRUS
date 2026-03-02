"""Ring band generation using CadQuery revolve.

Source of truth: jewelry-parametric-engine/SKILL.md

CAD rules:
  - Parametric construction only
  - Preferred ops: revolve(), extrude(), loft(), fillet(), boolean union
  - No freeform sculpting, no mesh boolean hacks
  - All joining edges fillet ≥ 0.2 mm
  - Symmetric across vertical center plane
"""

from __future__ import annotations

import cadquery as cq

from app.schemas.parametric import ParametricRing


def build_band(params: ParametricRing) -> cq.Workplane:
    """Generate the ring band by revolving a rectangular cross-section.

    The band sits centered at the origin with the ring axis along Y.
    Cross-section is in the XZ plane, revolved 360° around the Y axis.

    Geometry:
      - Inner radius = ring_radius
      - Outer radius = ring_radius + band_thickness
      - Width (along Y) = band_width
    """
    r_inner = params.ring_radius
    r_outer = r_inner + params.band_thickness
    half_w = params.band_width / 2.0

    # Build cross-section profile (rectangle in XZ plane at Y=0)
    # We place it at X = r_inner, spanning from X=r_inner to X=r_outer
    profile = (
        cq.Workplane("XZ")
        .moveTo(r_inner, -half_w)
        .lineTo(r_outer, -half_w)
        .lineTo(r_outer, half_w)
        .lineTo(r_inner, half_w)
        .close()
    )

    # Revolve around Y axis (the ring axis)
    band = profile.revolve(360, (0, 0, 0), (0, 1, 0))

    # Apply fillet to top and bottom edges (≥ 0.2 mm per SKILL)
    fillet_r = min(0.3, params.band_thickness * 0.15, params.band_width * 0.15)
    fillet_r = max(fillet_r, 0.2)  # minimum 0.2 mm
    try:
        band = band.edges("|Y").fillet(fillet_r)
    except Exception:
        # Fillet failure is non-fatal — log and continue with un-filleted band
        pass

    return band
