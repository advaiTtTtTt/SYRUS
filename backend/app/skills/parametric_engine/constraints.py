"""Parameter clamping and pre-build constraint validation.

Source of truth: jewelry-parametric-engine/SKILL.md

Error handling policy:
  Clamp to safe value → log correction → continue.
  Never silently produce invalid geometry.
"""

from __future__ import annotations

from app.schemas.parametric import ParametricRing
from app.utils.logging import log_clamp
from app.utils.units import clamp


# ── Strict limits from SKILL ──────────────────────────────────────

LIMITS = {
    "ring_radius":    (7.0, 12.0),
    "band_width":     (1.5, 6.0),
    "band_thickness": (1.5, 3.5),
    "stone_diameter": (3.0, 12.0),
    "prongs":         (3, 8),
}


def apply_constraints(params: ParametricRing) -> ParametricRing:
    """Clamp all parameters to SKILL-defined ranges, logging any corrections."""
    p = params.model_copy(deep=True)

    # Ring dimensions
    for attr, (lo, hi) in [
        ("ring_radius", LIMITS["ring_radius"]),
        ("band_width", LIMITS["band_width"]),
        ("band_thickness", LIMITS["band_thickness"]),
    ]:
        original = getattr(p, attr)
        clamped = clamp(original, lo, hi)
        if original != clamped:
            log_clamp(attr, original, clamped)
            setattr(p, attr, clamped)

    # Stone diameter
    cs = p.center_stone
    original_dia = cs.diameter
    cs.diameter = clamp(cs.diameter, *LIMITS["stone_diameter"])
    if original_dia != cs.diameter:
        log_clamp("center_stone.diameter", original_dia, cs.diameter)

    # Stone height: 40–70% of diameter
    lo_h = cs.diameter * 0.40
    hi_h = cs.diameter * 0.70
    original_h = cs.height
    cs.height = round(clamp(cs.height, lo_h, hi_h), 2)
    if original_h != cs.height:
        log_clamp("center_stone.height", original_h, cs.height)

    # Prong count
    original_p = cs.prongs
    cs.prongs = int(clamp(cs.prongs, *LIMITS["prongs"]))
    if original_p != cs.prongs:
        log_clamp("center_stone.prongs", float(original_p), float(cs.prongs))

    return p
