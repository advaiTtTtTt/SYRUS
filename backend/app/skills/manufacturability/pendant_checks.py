"""Pendant-specific manufacturability checks.

Rules:
  - Bail thickness >= 0.8 mm (structural minimum for chain attachment)
  - Bail diameter >= 2.0 mm (chain must pass through)
  - Base plate thickness >= 1.0 mm (structural integrity)
  - Bail attachment structural integrity: bail_thickness >= base_thickness * 0.5
  - Balance: stone diameter must not exceed 80% of base width
"""

from __future__ import annotations

from app.schemas.parametric import ParametricRing

BAIL_THICKNESS_MIN = 0.8
BAIL_DIAMETER_MIN = 2.0
BASE_THICKNESS_MIN = 1.0
BAIL_ATTACHMENT_RATIO = 0.5   # bail_thickness >= base_thickness * ratio
STONE_TO_BASE_MAX = 0.80     # stone diameter / base width


def check_pendant(
    params: ParametricRing,
    violations: list[str],
    corrections: list[str],
) -> ParametricRing:
    """Validate pendant-specific manufacturing constraints."""
    pp = params.pendant_params
    if pp is None:
        return params

    # ── Bail thickness ─────────────────────────────────────────────
    if pp.bail_thickness < BAIL_THICKNESS_MIN:
        corrections.append(
            f"Increased bail thickness {pp.bail_thickness} → {BAIL_THICKNESS_MIN} mm (structural min)"
        )
        pp.bail_thickness = BAIL_THICKNESS_MIN

    # ── Bail diameter ──────────────────────────────────────────────
    if pp.bail_diameter < BAIL_DIAMETER_MIN:
        corrections.append(
            f"Increased bail diameter {pp.bail_diameter} → {BAIL_DIAMETER_MIN} mm (chain clearance)"
        )
        pp.bail_diameter = BAIL_DIAMETER_MIN

    # ── Base thickness ─────────────────────────────────────────────
    if pp.base_thickness < BASE_THICKNESS_MIN:
        corrections.append(
            f"Increased base thickness {pp.base_thickness} → {BASE_THICKNESS_MIN} mm"
        )
        pp.base_thickness = BASE_THICKNESS_MIN

    # ── Bail attachment structural integrity ────────────────────────
    min_bail = pp.base_thickness * BAIL_ATTACHMENT_RATIO
    if pp.bail_thickness < min_bail:
        safe_bail = round(min_bail, 2)
        corrections.append(
            f"Increased bail thickness {pp.bail_thickness} → {safe_bail} mm (attachment integrity)"
        )
        pp.bail_thickness = safe_bail

    # ── Balance: stone vs base ─────────────────────────────────────
    stone_d = params.center_stone.diameter
    if stone_d > pp.base_width * STONE_TO_BASE_MAX:
        new_base = round(stone_d / STONE_TO_BASE_MAX + 0.5, 1)
        new_base = min(new_base, 30.0)  # respect max limit
        if new_base > pp.base_width:
            corrections.append(
                f"Increased pendant base width {pp.base_width} → {new_base} mm (stone balance)"
            )
            pp.base_width = new_base

    return params
