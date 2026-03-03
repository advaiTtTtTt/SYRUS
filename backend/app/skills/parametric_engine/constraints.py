"""Parameter clamping and pre-build constraint validation.

Source of truth: jewelry-parametric-engine/SKILL.md

Error handling policy:
  Clamp to safe value → log correction → continue.
  Never silently produce invalid geometry.

Supports: ring, pendant, earring
"""

from __future__ import annotations

from app.schemas.parametric import JewelryType, ParametricRing
from app.utils.logging import log_clamp
from app.utils.units import clamp


# ── Strict limits from SKILL ──────────────────────────────────────

LIMITS = {
    # Shared
    "stone_diameter": (3.0, 12.0),
    "prongs":         (3, 8),
    # Ring
    "ring_radius":    (7.0, 12.0),
    "band_width":     (1.5, 6.0),
    "band_thickness": (1.5, 3.5),
    # Pendant
    "pendant_base_width":     (8.0, 30.0),
    "pendant_base_height":    (8.0, 35.0),
    "pendant_base_thickness": (1.0, 3.5),
    "pendant_bail_diameter":  (2.0, 8.0),
    "pendant_bail_thickness": (0.8, 2.5),
    # Earring
    "earring_stud_diameter":  (4.0, 15.0),
    "earring_stud_thickness": (0.8, 3.0),
    "earring_pin_length":     (8.0, 12.0),
    "earring_pin_diameter":   (0.7, 1.2),
    # Side stone layout
    "ssl_count":    (0, 60),
    "ssl_diameter": (1.0, 4.0),
    "ssl_rows":     (1, 3),
}


def _clamp_ring(p: ParametricRing) -> None:
    """Clamp ring-specific parameters."""
    for attr, key in [
        ("ring_radius", "ring_radius"),
        ("band_width", "band_width"),
        ("band_thickness", "band_thickness"),
    ]:
        original = getattr(p, attr)
        clamped = clamp(original, *LIMITS[key])
        if original != clamped:
            log_clamp(attr, original, clamped)
            setattr(p, attr, clamped)


def _clamp_pendant(p: ParametricRing) -> None:
    """Clamp pendant-specific parameters."""
    pp = p.pendant_params
    if pp is None:
        return
    for attr, key in [
        ("base_width",     "pendant_base_width"),
        ("base_height",    "pendant_base_height"),
        ("base_thickness", "pendant_base_thickness"),
        ("bail_diameter",  "pendant_bail_diameter"),
        ("bail_thickness", "pendant_bail_thickness"),
    ]:
        original = getattr(pp, attr)
        clamped = clamp(original, *LIMITS[key])
        if original != clamped:
            log_clamp(f"pendant.{attr}", original, clamped)
            setattr(pp, attr, clamped)


def _clamp_earring(p: ParametricRing) -> None:
    """Clamp earring-specific parameters."""
    ep = p.earring_params
    if ep is None:
        return
    for attr, key in [
        ("stud_diameter",  "earring_stud_diameter"),
        ("stud_thickness", "earring_stud_thickness"),
        ("pin_length",     "earring_pin_length"),
        ("pin_diameter",   "earring_pin_diameter"),
    ]:
        original = getattr(ep, attr)
        clamped = clamp(original, *LIMITS[key])
        if original != clamped:
            log_clamp(f"earring.{attr}", original, clamped)
            setattr(ep, attr, clamped)


def _clamp_stone(p: ParametricRing) -> None:
    """Clamp shared stone parameters."""
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


def _clamp_side_stone_layout(p: ParametricRing) -> None:
    """Clamp side stone layout parameters (if present)."""
    ssl = p.side_stone_layout
    if ssl is None or not ssl.enabled:
        return
    for attr, key in [
        ("count",    "ssl_count"),
        ("diameter", "ssl_diameter"),
        ("rows",     "ssl_rows"),
    ]:
        original = getattr(ssl, attr)
        clamped_val = clamp(float(original), *LIMITS[key])
        clamped_val = int(clamped_val) if isinstance(original, int) else clamped_val
        if original != clamped_val:
            log_clamp(f"side_stone_layout.{attr}", float(original), float(clamped_val))
            setattr(ssl, attr, clamped_val)


# ── Type dispatch map ──────────────────────────────────────────────

_TYPE_CLAMP = {
    JewelryType.RING:    _clamp_ring,
    JewelryType.PENDANT: _clamp_pendant,
    JewelryType.EARRING: _clamp_earring,
}


def apply_constraints(params: ParametricRing) -> ParametricRing:
    """Clamp all parameters to SKILL-defined ranges, logging any corrections."""
    p = params.model_copy(deep=True)

    # Type-specific clamping
    clamp_fn = _TYPE_CLAMP.get(p.type, _clamp_ring)
    clamp_fn(p)

    # Shared stone clamping
    _clamp_stone(p)

    # Side stone layout clamping (ring-only, but safe to call always)
    _clamp_side_stone_layout(p)

    return p
