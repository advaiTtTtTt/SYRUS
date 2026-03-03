"""Earring geometry builder.

Generates a stud earring from parametric JSON using CadQuery primitives:
  1. Stud base disc
  2. Back pin (post)
  3. Stone seat cut
  4. Mirror-safe geometry (symmetric about YZ plane)

Source of truth: jewelry-parametric-engine/SKILL.md
All dims in millimetres.  CadQuery primitives only.
"""

from __future__ import annotations

import math

import cadquery as cq

from app.schemas.parametric import EarringParams, ParametricRing
from .stone import get_seat_cutter


def _build_stud_base(ep: EarringParams) -> cq.Workplane:
    """Create the stud base disc, lying flat in XZ with thickness along Y."""
    stud = (
        cq.Workplane("XZ")
        .circle(ep.stud_diameter / 2.0)
        .extrude(ep.stud_thickness)
    )

    # Slight dome on front face for aesthetics (safe fillet)
    try:
        stud = stud.edges(">Y").fillet(ep.stud_thickness * 0.2)
    except Exception:
        pass  # Fillet non-fatal

    return stud


def _build_back_pin(ep: EarringParams) -> cq.Workplane:
    """Create the back pin (post) that goes through the earlobe.

    Pin extends from the back surface of the stud along -Y axis.
    Tapered slightly at the tip for comfort.
    """
    pin_r = ep.pin_diameter / 2.0
    tip_r = pin_r * 0.5  # taper to 50% at tip

    # Pin starts at back of stud (Y=0)  and extends to Y = -pin_length
    pin = (
        cq.Workplane("XZ")
        .circle(pin_r)
        .workplane(offset=-ep.pin_length)
        .circle(tip_r)
        .loft()
    )

    return pin


def build_earring(params: ParametricRing) -> cq.Workplane:
    """Build complete single earring geometry.

    Components:
      1. Stud base disc
      2. Back pin
      3. Stone seat boolean cut
      4. Prongs (if prong setting)

    Geometry is mirror-safe: symmetric about YZ plane.
    A pair is produced at rendering/export time, not here.
    """
    ep = params.earring_params
    if ep is None:
        from app.schemas.parametric import EarringParams as EP
        ep = EP()

    # 1. Stud base
    earring = _build_stud_base(ep)

    # 2. Back pin
    try:
        pin = _build_back_pin(ep)
        earring = earring.union(pin)
    except Exception:
        pass  # Pin union failure non-fatal

    # 3. Stone seat — cut into front surface
    try:
        seat = get_seat_cutter(params)
        earring = earring.cut(seat)
    except Exception:
        pass

    # 4. Prongs
    if params.setting_type.value == "prong":
        try:
            from .prongs import build_prongs
            prongs = build_prongs(params)
            earring = earring.union(prongs)
        except Exception:
            pass

    return earring
