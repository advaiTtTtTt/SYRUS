"""Parametric engine — main build orchestrator.

Combines type-specific geometry + stone seat + settings into a single solid.
Runs constraint clamping, then CadQuery construction, then export.

Supports: ring, pendant, earring — dispatched via build_jewelry().

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

from app.schemas.parametric import JewelryType, ParametricRing, SettingStyle
from app.schemas.validation_result import ManufacturingStatus, ValidationResult
from app.skills.manufacturability.validator import validate_parametric, validate_solid

from .band import build_band
from .cathedral import build_cathedral_supports
from .constraints import apply_constraints
from .earring import build_earring
from .exporter import export_glb, export_stl
from .halo import build_halo
from .pave import build_pave_shoulder
from .pendant import build_pendant
from .prongs import build_prongs
from .stone import get_seat_cutter


@dataclass
class BuildResult:
    """Result of a jewelry build operation."""

    solid: cq.Workplane
    parts: dict[str, cq.Workplane]  # named sub-meshes for GLB material groups
    params_used: ParametricRing  # after clamping + validator corrections
    validation: ValidationResult
    stl_path: Optional[Path] = None
    glb_path: Optional[Path] = None


# ════════════════════════════════════════════════════════════════════
#  Ring builder (original)
# ════════════════════════════════════════════════════════════════════

def _build_ring_solid(
    params: ParametricRing, violations: list[str]
) -> tuple[cq.Workplane, dict[str, cq.Workplane]]:
    """Ring-specific geometry: band → seat cut → prongs → pavé shoulder.

    Returns (full_solid, parts_dict) where parts_dict maps human-readable
    names to individual CadQuery solids for multi-material GLB export.
    """
    parts: dict[str, cq.Workplane] = {}
    band = build_band(params)
    parts["band"] = band

    # Cut stone seat
    try:
        seat_cutter = get_seat_cutter(params)
        ring = band.cut(seat_cutter)
    except Exception:
        ring = band

    # Build center stone placeholder for the GLB (visual only)
    try:
        from .stone import build_stone_placeholder
        stone_solid = build_stone_placeholder(params)
        parts["center_stone"] = stone_solid
    except Exception:
        pass  # Stone placeholder non-fatal

    # Prongs
    if params.setting_type.value == "prong":
        try:
            prongs = build_prongs(params)
            ring = ring.union(prongs)
            parts["prongs"] = prongs
        except Exception:
            violations.append("Prong boolean union failed — exported without prongs")

    # Pavé shoulders (if setting_style requests it and layout is enabled)
    if (
        params.setting_style == SettingStyle.PAVE_SHOULDER
        and params.side_stone_layout is not None
        and params.side_stone_layout.enabled
    ):
        try:
            pave = build_pave_shoulder(params)
            ring = ring.cut(pave.seat_cuts)
            ring = ring.union(pave.micro_prongs)
            parts["pave_stones"] = pave.micro_prongs
        except Exception as e:
            violations.append(f"Pavé shoulder build failed: {e}")

    # Halo (ring of stones around the center stone)
    if (
        params.setting_style == SettingStyle.HALO
        and params.side_stone_layout is not None
        and params.side_stone_layout.enabled
    ):
        try:
            halo = build_halo(params)
            if halo.stone_count > 0:
                ring = ring.union(halo.base_plate)
                ring = ring.cut(halo.seat_cuts)
                parts["halo_stones"] = halo.base_plate
        except Exception as e:
            violations.append(f"Halo build failed: {e}")

    # Cathedral arch supports
    if params.setting_style == SettingStyle.CATHEDRAL:
        try:
            cathedral = build_cathedral_supports(params)
            ring = ring.union(cathedral.supports)
            parts["cathedral"] = cathedral.supports
        except Exception as e:
            violations.append(f"Cathedral support build failed: {e}")

    return ring, parts


# ════════════════════════════════════════════════════════════════════
#  Pendant builder
# ════════════════════════════════════════════════════════════════════

def _build_pendant_solid(
    params: ParametricRing, violations: list[str]
) -> tuple[cq.Workplane, dict[str, cq.Workplane]]:
    """Pendant-specific geometry: base plate → bail → seat → prongs."""
    parts: dict[str, cq.Workplane] = {}
    try:
        solid = build_pendant(params)
        parts["pendant_body"] = solid
        # Add stone placeholder
        try:
            from .stone import build_stone_placeholder
            parts["center_stone"] = build_stone_placeholder(params)
        except Exception:
            pass
        return solid, parts
    except Exception as e:
        violations.append(f"Pendant build error: {e}")
        empty = cq.Workplane("XY")
        return empty, {"pendant_body": empty}


# ════════════════════════════════════════════════════════════════════
#  Earring builder
# ════════════════════════════════════════════════════════════════════

def _build_earring_solid(
    params: ParametricRing, violations: list[str]
) -> tuple[cq.Workplane, dict[str, cq.Workplane]]:
    """Earring-specific geometry: stud → pin → seat → prongs."""
    parts: dict[str, cq.Workplane] = {}
    try:
        solid = build_earring(params)
        parts["earring_body"] = solid
        try:
            from .stone import build_stone_placeholder
            parts["center_stone"] = build_stone_placeholder(params)
        except Exception:
            pass
        return solid, parts
    except Exception as e:
        violations.append(f"Earring build error: {e}")
        empty = cq.Workplane("XY")
        return empty, {"earring_body": empty}


# ════════════════════════════════════════════════════════════════════
#  Dispatch
# ════════════════════════════════════════════════════════════════════

_TYPE_BUILDERS = {
    JewelryType.RING:    _build_ring_solid,
    JewelryType.PENDANT: _build_pendant_solid,
    JewelryType.EARRING: _build_earring_solid,
}


def build_jewelry(
    params: ParametricRing,
    output_dir: Path,
    build_id: str,
) -> BuildResult:
    """Universal jewelry build pipeline.

    Dispatches to the correct builder based on params.type.

    1. Apply parametric constraints (clamping)
    2. Run manufacturability pre-validation
    3. Build type-specific geometry
    4. Run post-build mesh validation
    5. Export STL + GLB
    """

    # ── 1. Constraint clamping ─────────────────────────────────────
    clamped = apply_constraints(params)

    # ── 2. Pre-build manufacturability validation ──────────────────
    validated_params, pre_validation = validate_parametric(clamped)

    if pre_validation.manufacturing_status == ManufacturingStatus.REJECTED:
        return BuildResult(
            solid=cq.Workplane("XY"),
            parts={},
            params_used=validated_params,
            validation=pre_validation,
        )

    # ── 3. Build geometry via dispatcher ───────────────────────────
    builder_fn = _TYPE_BUILDERS.get(validated_params.type, _build_ring_solid)
    solid, parts = builder_fn(validated_params, pre_validation.violations_detected)

    # ── 4. Post-build mesh validation ──────────────────────────────
    final_validation = validate_solid(solid, pre_validation)

    if final_validation.manufacturing_status == ManufacturingStatus.REJECTED:
        return BuildResult(
            solid=solid,
            parts=parts,
            params_used=validated_params,
            validation=final_validation,
        )

    # ── 5. Export ──────────────────────────────────────────────────
    build_dir = output_dir / build_id
    build_dir.mkdir(parents=True, exist_ok=True)

    stl_path = export_stl(solid, build_dir / "model.stl")
    glb_path = export_glb(parts, build_dir / "model.glb")

    return BuildResult(
        solid=solid,
        parts=parts,
        params_used=validated_params,
        validation=final_validation,
        stl_path=stl_path,
        glb_path=glb_path,
    )


# ── Backward compat alias ─────────────────────────────────────────
build_ring = build_jewelry
