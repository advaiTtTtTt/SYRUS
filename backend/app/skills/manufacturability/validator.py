"""Manufacturability validation orchestrator.

Source of truth: manufacturability-validator/SKILL.md

Runs AFTER geometry generation, BEFORE export.
Authority to reject, auto-correct, clamp, block export.

Pipeline:
  1. Wall / band thickness checks
  2. Prong validation
  3. Stone seating checks
  4. Balance / stability checks
  5. (Post-build) Mesh / solid validation

Performance target: < 300ms for standard ring.
"""

from __future__ import annotations

from typing import Any, Optional

from app.schemas.parametric import ParametricRing
from app.schemas.validation_result import ManufacturingStatus, ValidationResult

from .balance_checks import check_balance
from .mesh_checks import check_mesh_validity
from .prong_checks import check_prongs
from .stone_checks import check_stone_seating
from .wall_checks import check_wall_thickness


def validate_parametric(params: ParametricRing) -> tuple[ParametricRing, ValidationResult]:
    """Run all parametric (pre-build) validation checks.

    Returns a (possibly corrected) ParametricRing and a ValidationResult.
    """
    violations: list[str] = []
    corrections: list[str] = []

    # Work on a deep copy to avoid mutating the caller's object
    p = params.model_copy(deep=True)

    # ── 1. Wall / band checks ─────────────────────────────────────
    p = check_wall_thickness(p, violations, corrections)

    # Check for hard rejection
    if any("REJECTED" in v for v in violations):
        return p, ValidationResult(
            violations_detected=violations,
            corrections_applied=corrections,
            manufacturing_status=ManufacturingStatus.REJECTED,
        )

    # ── 2. Prong checks ───────────────────────────────────────────
    p = check_prongs(p, violations, corrections)

    # ── 3. Stone seating checks ────────────────────────────────────
    p = check_stone_seating(p, violations, corrections)

    # ── 4. Balance / stability ─────────────────────────────────────
    p = check_balance(p, violations, corrections)

    # ── Determine status ───────────────────────────────────────────
    if any("REJECTED" in v for v in violations):
        status = ManufacturingStatus.REJECTED
    elif corrections:
        status = ManufacturingStatus.AUTO_CORRECTED
    else:
        status = ManufacturingStatus.SAFE

    return p, ValidationResult(
        violations_detected=violations,
        corrections_applied=corrections,
        manufacturing_status=status,
    )


def validate_solid(
    solid: Any,
    parametric_result: ValidationResult,
) -> ValidationResult:
    """Run post-build mesh/solid validation on the CadQuery output.

    Appends to the existing parametric validation result.
    """
    violations = list(parametric_result.violations_detected)
    corrections = list(parametric_result.corrections_applied)

    mesh_ok = check_mesh_validity(solid, violations, corrections)

    if not mesh_ok:
        status = ManufacturingStatus.REJECTED
    elif corrections != list(parametric_result.corrections_applied):
        status = ManufacturingStatus.AUTO_CORRECTED
    else:
        status = parametric_result.manufacturing_status

    return ValidationResult(
        violations_detected=violations,
        corrections_applied=corrections,
        manufacturing_status=status,
    )
