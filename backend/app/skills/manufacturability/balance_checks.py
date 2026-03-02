"""Center of mass and balance / stability checks.

Source of truth: manufacturability-validator/SKILL.md

Rules:
  - Compute center of mass and base support footprint
  - Must balance evenly, not tip forward, uniform weight
  - Unstable → thicken lower band interior
"""

from __future__ import annotations

from app.schemas.parametric import ParametricRing


def check_balance(
    params: ParametricRing,
    violations: list[str],
    corrections: list[str],
) -> ParametricRing:
    """Pre-build balance heuristic based on parametric values.

    A ring with a very large stone relative to band mass may be top-heavy.
    We check the stone-to-band mass ratio as a proxy for balance.
    """
    import math

    # Rough band volume (torus approximation)
    band_vol = 2.0 * math.pi * params.ring_radius * params.band_width * params.band_thickness

    # Rough stone volume (sphere approximation for center stone)
    r = params.center_stone.diameter / 2.0
    stone_vol = (4.0 / 3.0) * math.pi * (r ** 3)

    # If stone volume > 40% of band volume — flag as potentially top-heavy
    ratio = stone_vol / band_vol if band_vol > 0 else 999
    if ratio > 0.4:
        violations.append(
            f"Stone-to-band volume ratio {ratio:.2f} — potentially top-heavy"
        )
        # Auto-correct: increase band thickness slightly
        new_thickness = min(3.5, params.band_thickness + 0.3)
        if new_thickness > params.band_thickness:
            corrections.append(
                f"Increased band thickness {params.band_thickness} → {new_thickness} mm for balance"
            )
            params.band_thickness = new_thickness

    return params
