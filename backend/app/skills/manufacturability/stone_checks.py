"""Stone seating / interference validation.

Source of truth: manufacturability-validator/SKILL.md

Rules:
  - Seat depth: 15–25% of stone height
  - Tolerance: +0.05 mm / −0.00 mm
  - Stone must NOT penetrate band bottom
  - Stone must NOT float above seat
  - Stone must NOT clip through prongs
"""

from __future__ import annotations

from app.schemas.parametric import ParametricRing

SEAT_DEPTH_MIN_RATIO = 0.15
SEAT_DEPTH_MAX_RATIO = 0.25
SEAT_TOLERANCE_PLUS = 0.05


def check_stone_seating(
    params: ParametricRing,
    violations: list[str],
    corrections: list[str],
) -> ParametricRing:
    """Validate stone seat depth and interference."""
    stone = params.center_stone

    # Compute acceptable seat depth range
    min_seat = stone.height * SEAT_DEPTH_MIN_RATIO
    max_seat = stone.height * SEAT_DEPTH_MAX_RATIO + SEAT_TOLERANCE_PLUS

    # The seat is cut into the band; stone must not penetrate through
    # Max possible seat = band_thickness (stone would poke through bottom)
    if max_seat > params.band_thickness * 0.8:
        # Stone would be too deep — ensure band supports it
        violations.append(
            f"Stone seat depth ({round(max_seat, 2)} mm) approaches band thickness ({params.band_thickness} mm)"
        )
        # Auto-correct: increase band thickness to safely house the stone
        required_thickness = round(max_seat / 0.8 + 0.2, 2)
        if required_thickness <= 3.5:  # within parametric engine limits
            corrections.append(
                f"Increased band thickness to {required_thickness} mm for safe stone seating"
            )
            params.band_thickness = required_thickness
        else:
            corrections.append(
                f"Reduced stone height to fit band (was {stone.height} mm)"
            )
            # Reduce stone height so seat fits within band
            safe_seat = params.band_thickness * 0.8
            stone.height = round(safe_seat / SEAT_DEPTH_MAX_RATIO, 2)

    return params
