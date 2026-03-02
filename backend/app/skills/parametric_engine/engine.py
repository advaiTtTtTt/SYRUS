"""Parametric engine — main build orchestrator.

Combines band + stone seat + prongs into a single solid ring.
Runs constraint clamping, then CadQuery construction, then export.

Source of truth: jewelry-parametric-engine/SKILL.md
  - Parametric construction only
  - No freeform sculpting
  - Preferred ops: revolve(), extrude(), loft(), fillet(), boolean union (clean only)
  - Symmetric across vertical center plane
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cadquery as cq

from app.schemas.parametric import ParametricRing
from app.schemas.validation_result import ManufacturingStatus, ValidationResult
from app.skills.manufacturability.validator import validate_parametric, validate_solid

from .band import build_band
from .constraints import apply_constraints
from .exporter import export_glb, export_stl
from .prongs import build_prongs
from .stone import get_seat_cutter


@dataclass
class BuildResult:
    """Result of a ring build operation."""

    solid: cq.Workplane
    params_used: ParametricRing  # after clamping + validator corrections
    validation: ValidationResult
    stl_path: Optional[Path] = None
    glb_path: Optional[Path] = None


def build_ring(
    params: ParametricRing,
    output_dir: Path,
    build_id: str,
) -> BuildResult:
    """Full ring build pipeline:

    1. Apply parametric constraints (clamping)
    2. Run manufacturability pre-validation
    3. Build band (revolve)
    4. Cut stone seat (boolean subtract)
    5. Build prongs (loft + union)
    6. Union all components
    7. Run post-build mesh validation
    8. Export STL + GLB
    """

    # ── 1. Constraint clamping ─────────────────────────────────────
    clamped = apply_constraints(params)

    # ── 2. Pre-build manufacturability validation ──────────────────
    validated_params, pre_validation = validate_parametric(clamped)

    if pre_validation.manufacturing_status == ManufacturingStatus.REJECTED:
        # Cannot build — return early with rejection
        return BuildResult(
            solid=cq.Workplane("XY"),  # empty
            params_used=validated_params,
            validation=pre_validation,
        )

    # ── 3. Build band ──────────────────────────────────────────────
    band = build_band(validated_params)

    # ── 4. Cut stone seat ──────────────────────────────────────────
    try:
        seat_cutter = get_seat_cutter(validated_params)
        ring = band.cut(seat_cutter)
    except Exception:
        # Seat cut failed — continue with uncut band
        ring = band

    # ── 5. Build and union prongs ──────────────────────────────────
    if validated_params.setting_type.value == "prong":
        try:
            prongs = build_prongs(validated_params)
            ring = ring.union(prongs)
        except Exception:
            # Prong union failed — continue without prongs (logged)
            pre_validation.violations_detected.append(
                "Prong boolean union failed — exported without prongs"
            )

    # ── 6. Post-build mesh validation ──────────────────────────────
    final_validation = validate_solid(ring, pre_validation)

    if final_validation.manufacturing_status == ManufacturingStatus.REJECTED:
        return BuildResult(
            solid=ring,
            params_used=validated_params,
            validation=final_validation,
        )

    # ── 7. Export ──────────────────────────────────────────────────
    build_dir = output_dir / build_id
    build_dir.mkdir(parents=True, exist_ok=True)

    stl_path = export_stl(ring, build_dir / "model.stl")
    glb_path = export_glb(ring, build_dir / "model.glb")

    return BuildResult(
        solid=ring,
        params_used=validated_params,
        validation=final_validation,
        stl_path=stl_path,
        glb_path=glb_path,
    )
