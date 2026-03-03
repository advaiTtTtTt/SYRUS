"""Pendant geometry builder.

Generates a pendant from parametric JSON using CadQuery primitives:
  1. Base plate (circular or oval disc)
  2. Bail (attachment loop at top)
  3. Stone seat cut
  4. Prong placement on flat plate

Source of truth: jewelry-parametric-engine/SKILL.md
All dims in millimetres.  CadQuery primitives only.
"""

from __future__ import annotations

import math

import cadquery as cq

from app.schemas.parametric import PendantBaseShape, PendantParams, ParametricRing
from .stone import build_stone_placeholder, get_seat_cutter, SEAT_DEPTH_RATIO


def _build_base_plate(pp: PendantParams) -> cq.Workplane:
    """Create the pendant base disc/oval, lying flat in XZ with thickness along Y."""
    if pp.base_shape == PendantBaseShape.OVAL:
        # Oval: extrude an ellipse
        # CadQuery lacks native ellipse()  →  draw with circle then scale
        base = (
            cq.Workplane("XZ")
            .circle(pp.base_width / 2.0)
            .extrude(pp.base_thickness)
        )
        # Scale Z to create oval (base_height / base_width ratio)
        scale_z = pp.base_height / pp.base_width
        base = base.val().transformShape(
            cq.Matrix([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, scale_z, 0],
            ])
        )
        return cq.Workplane("XY").add(base)
    else:
        # Circular disc
        base = (
            cq.Workplane("XZ")
            .circle(pp.base_width / 2.0)
            .extrude(pp.base_thickness)
        )
        return base


def _build_bail(pp: PendantParams) -> cq.Workplane:
    """Create the bail (loop) at the top of the pendant.

    The bail is a torus section: a half-ring that sits at the top edge
    of the base plate, providing the chain attachment point.
    """
    bail_r = pp.bail_diameter / 2.0      # outer radius of the bail loop
    wire_r = pp.bail_thickness / 2.0     # cross-section radius

    # Bail profile: circle cross-section
    # Revolved 180° around a vertical axis at the top of the base
    profile = (
        cq.Workplane("XZ")
        .transformed(offset=(bail_r, 0, 0))
        .circle(wire_r)
    )
    bail = profile.revolve(180, (0, 0, 0), (0, 0, 1))

    # Position bail at top of base plate
    # Base plate center is at origin; top edge is at Z = base_height/2 (or base_width/2 for circular)
    offset_z = pp.base_width / 2.0  # top of circular base
    offset_y = pp.base_thickness     # on top surface

    bail = bail.translate((0, offset_y / 2.0, offset_z))
    return bail


def build_pendant(params: ParametricRing) -> cq.Workplane:
    """Build complete pendant geometry.

    Components:
      1. Base plate (circular/oval disc)
      2. Bail loop (top attachment)
      3. Stone seat boolean cut
      4. Prongs (if prong setting)
    """
    pp = params.pendant_params
    if pp is None:
        from app.schemas.parametric import PendantParams as PP
        pp = PP()

    # 1. Base plate
    pendant = _build_base_plate(pp)

    # 2. Bail
    try:
        bail = _build_bail(pp)
        pendant = pendant.union(bail)
    except Exception:
        pass  # Bail union failure non-fatal

    # 3. Stone seat — cut into top surface of base plate
    try:
        seat = get_seat_cutter(params)
        pendant = pendant.cut(seat)
    except Exception:
        pass  # Seat cut failure non-fatal

    # 4. Prongs (reuse ring prong builder — prongs sit on flat plate)
    if params.setting_type.value == "prong":
        try:
            from .prongs import build_prongs
            prongs = build_prongs(params)
            pendant = pendant.union(prongs)
        except Exception:
            pass

    return pendant
