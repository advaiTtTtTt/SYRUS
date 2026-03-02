"""Wall thickness and band structural checks.

Source of truth: manufacturability-validator/SKILL.md

Rules:
  - Min wall thickness: 1.0 mm (recommended 1.2–1.8 mm)
  - < 1.0 mm → auto-increase
  - < 0.6 mm → reject as structurally unsafe
  - Min band thickness: 1.5 mm
  - Min band width: 1.5 mm
  - Continuous curvature, fillet ≥ 0.2 mm
"""

from __future__ import annotations

from app.schemas.parametric import ParametricRing


# Thresholds from SKILL
WALL_MIN = 1.0
WALL_REJECT = 0.6
BAND_THICKNESS_MIN = 1.5
BAND_WIDTH_MIN = 1.5


def check_wall_thickness(
    params: ParametricRing,
    violations: list[str],
    corrections: list[str],
) -> ParametricRing:
    """Validate and auto-correct wall / band dimensions."""

    # ── Band thickness ─────────────────────────────────────────────
    if params.band_thickness < WALL_REJECT:
        violations.append(
            f"Band thickness {params.band_thickness} mm < {WALL_REJECT} mm — structurally unsafe, REJECTED"
        )
        return params  # caller will set REJECTED status

    if params.band_thickness < BAND_THICKNESS_MIN:
        corrections.append(
            f"Increased band thickness {params.band_thickness} → {BAND_THICKNESS_MIN} mm"
        )
        params.band_thickness = BAND_THICKNESS_MIN

    # ── Band width ─────────────────────────────────────────────────
    if params.band_width < BAND_WIDTH_MIN:
        corrections.append(
            f"Increased band width {params.band_width} → {BAND_WIDTH_MIN} mm"
        )
        params.band_width = BAND_WIDTH_MIN

    return params
