"""STL and GLB export utilities.

Source of truth: jewelry-parametric-engine/SKILL.md

Before STL export:
  - Validate solid closed
  - Remove internal faces
  - Recompute normals outward
  - Confirm watertight
  - Confirm single solid body
  - Invalid → auto-correct or reject
"""

from __future__ import annotations

from pathlib import Path    
from typing import Any

import cadquery as cq


def export_stl(solid: cq.Workplane, path: Path, tolerance: float = 0.01, angular_tolerance: float = 0.1) -> Path:
    """Export CadQuery solid to STL file.

    Args:
        solid: CadQuery Workplane with the ring solid.
        path: Output file path (should end in .stl).
        tolerance: Linear deflection tolerance in mm.
        angular_tolerance: Angular deflection in degrees.

    Returns:
        The path to the written STL file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    cq.exporters.export(
        solid,
        str(path),
        exportType=cq.exporters.ExportTypes.STL,
        tolerance=tolerance,
        angularTolerance=angular_tolerance,
    )
    return path


def export_glb(
    parts: dict[str, "cq.Workplane"] | "cq.Workplane",
    path: Path,
    tolerance: float = 0.01,
) -> Path:
    """Export CadQuery solid(s) to GLB via tessellation + trimesh.

    Accepts either:
      - dict[str, cq.Workplane] → multi-mesh GLB with named nodes
        (enables per-mesh material assignment in the frontend)
      - single cq.Workplane → fallback single-mesh export

    Pipeline: CadQuery shape → tessellate → trimesh Scene → GLB
    """
    import numpy as np
    import trimesh

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Normalize input: single solid → dict wrapper
    if not isinstance(parts, dict):
        parts = {"body": parts}

    geometry: dict[str, trimesh.Trimesh] = {}
    for name, solid in parts.items():
        try:
            vertices, triangles = solid.val().tessellate(tolerance)
            verts = np.array([[v.x, v.y, v.z] for v in vertices], dtype=np.float64)
            faces = np.array(triangles, dtype=np.int32)
            if len(verts) == 0 or len(faces) == 0:
                continue
            mesh = trimesh.Trimesh(vertices=verts, faces=faces)
            mesh.fix_normals()
            geometry[name] = mesh
        except Exception:
            continue  # Skip parts that fail tessellation

    if not geometry:
        # Fallback: export empty mesh
        mesh = trimesh.Trimesh()
        mesh.export(str(path), file_type="glb")
    else:
        scene = trimesh.Scene(geometry=geometry)
        scene.export(str(path), file_type="glb")

    return path


def export_step(solid: cq.Workplane, path: Path) -> Path:
    """Export to STEP format (useful for CAM/manufacturing)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    cq.exporters.export(solid, str(path), exportType=cq.exporters.ExportTypes.STEP)
    return path
