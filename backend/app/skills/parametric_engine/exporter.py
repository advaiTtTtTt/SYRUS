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


def export_glb(solid: cq.Workplane, path: Path, tolerance: float = 0.01) -> Path:
    """Export CadQuery solid to GLB via tessellation + trimesh.

    Pipeline: CadQuery shape → tessellate → trimesh → GLB
    """
    import numpy as np
    import trimesh

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Tessellate the CadQuery solid
    vertices, triangles = solid.val().tessellate(tolerance)

    # Convert to numpy arrays
    verts = np.array([[v.x, v.y, v.z] for v in vertices], dtype=np.float64)
    faces = np.array(triangles, dtype=np.int32)

    # Build trimesh and export
    mesh = trimesh.Trimesh(vertices=verts, faces=faces)

    # Fix normals (outward-facing per SKILL)
    mesh.fix_normals()

    mesh.export(str(path), file_type="glb")
    return path


def export_step(solid: cq.Workplane, path: Path) -> Path:
    """Export to STEP format (useful for CAM/manufacturing)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    cq.exporters.export(solid, str(path), exportType=cq.exporters.ExportTypes.STEP)
    return path
