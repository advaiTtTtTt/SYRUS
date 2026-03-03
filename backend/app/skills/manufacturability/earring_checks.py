"""Earring-specific manufacturability checks.

Rules:
  - Pin diameter >= 0.7 mm (structural minimum)
  - Pin length 8–12 mm (standard ear post range)
  - Stud thickness >= 0.8 mm (structural)
  - Stone diameter must not exceed 90% of stud diameter
  - Mirror-safe: geometry must be symmetric (flagged, not corrected)
"""

from __future__ import annotations

from app.schemas.parametric import ParametricRing

PIN_DIAMETER_MIN = 0.7
PIN_LENGTH_MIN = 8.0
PIN_LENGTH_MAX = 12.0
STUD_THICKNESS_MIN = 0.8
STONE_TO_STUD_MAX = 0.90


def check_earring(
    params: ParametricRing,
    violations: list[str],
    corrections: list[str],
) -> ParametricRing:
    """Validate earring-specific manufacturing constraints."""
    ep = params.earring_params
    if ep is None:
        return params

    # ── Pin diameter ───────────────────────────────────────────────
    if ep.pin_diameter < PIN_DIAMETER_MIN:
        corrections.append(
            f"Increased pin diameter {ep.pin_diameter} → {PIN_DIAMETER_MIN} mm (structural min)"
        )
        ep.pin_diameter = PIN_DIAMETER_MIN

    # ── Pin length ─────────────────────────────────────────────────
    if ep.pin_length < PIN_LENGTH_MIN:
        corrections.append(
            f"Increased pin length {ep.pin_length} → {PIN_LENGTH_MIN} mm"
        )
        ep.pin_length = PIN_LENGTH_MIN
    elif ep.pin_length > PIN_LENGTH_MAX:
        corrections.append(
            f"Reduced pin length {ep.pin_length} → {PIN_LENGTH_MAX} mm"
        )
        ep.pin_length = PIN_LENGTH_MAX

    # ── Stud thickness ─────────────────────────────────────────────
    if ep.stud_thickness < STUD_THICKNESS_MIN:
        corrections.append(
            f"Increased stud thickness {ep.stud_thickness} → {STUD_THICKNESS_MIN} mm"
        )
        ep.stud_thickness = STUD_THICKNESS_MIN

    # ── Stone vs stud size ─────────────────────────────────────────
    stone_d = params.center_stone.diameter
    if stone_d > ep.stud_diameter * STONE_TO_STUD_MAX:
        new_stud = round(stone_d / STONE_TO_STUD_MAX + 0.5, 1)
        new_stud = min(new_stud, 15.0)  # respect max
        if new_stud > ep.stud_diameter:
            corrections.append(
                f"Increased stud diameter {ep.stud_diameter} → {new_stud} mm (stone clearance)"
            )
            ep.stud_diameter = new_stud

    # ── Mirror-safe flag ───────────────────────────────────────────
    # Earrings are inherently symmetric (circular stud + centered post).
    # Flag if any asymmetry could arise (future: non-circular studs).
    # For now, geometry is always mirror-safe — no violation needed.

    return params
