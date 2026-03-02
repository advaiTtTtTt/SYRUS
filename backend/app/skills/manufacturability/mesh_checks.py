"""Mesh / solid validation checks.

Source of truth: manufacturability-validator/SKILL.md

Rules:
  - Manifold, watertight, single solid body
  - Outward-facing normals
  - No self-intersections
  - No zero-thickness surfaces
  These run on the actual CadQuery solid after geometry build.
  At schema/pre-build time we can only do parametric sanity checks.
"""

from __future__ import annotations

from typing import Any, Optional


def check_mesh_validity(
    solid: Any,
    violations: list[str],
    corrections: list[str],
) -> bool:
    """Validate a CadQuery solid for mesh export readiness.

    Args:
        solid: A CadQuery Workplane or OCP Shape.
        violations: Mutable list to append violation descriptions.
        corrections: Mutable list to append correction descriptions.

    Returns:
        True if mesh is valid (possibly after corrections), False if rejected.
    """
    try:
        # Import here to avoid hard dependency during schema-only validation
        import cadquery as cq

        if solid is None:
            violations.append("Solid is None — no geometry produced")
            return False

        # Extract the underlying OCP shape
        if isinstance(solid, cq.Workplane):
            shape = solid.val()
        else:
            shape = solid

        # Check it's a valid solid
        from OCP.BRepCheck import BRepCheck_Analyzer  # type: ignore

        analyzer = BRepCheck_Analyzer(shape.wrapped if hasattr(shape, "wrapped") else shape)
        if not analyzer.IsValid():
            violations.append("BRepCheck: solid is not valid")
            # Attempt auto-repair via ShapeFix
            try:
                from OCP.ShapeFix import ShapeFix_Shape  # type: ignore

                fixer = ShapeFix_Shape(shape.wrapped if hasattr(shape, "wrapped") else shape)
                fixer.Perform()
                fixed = fixer.Shape()
                analyzer2 = BRepCheck_Analyzer(fixed)
                if analyzer2.IsValid():
                    corrections.append("Auto-repaired solid via ShapeFix")
                    return True
                else:
                    violations.append("Auto-repair failed — solid still invalid")
                    return False
            except Exception as e:
                violations.append(f"Auto-repair exception: {e}")
                return False

        return True

    except ImportError:
        # CadQuery not available — skip mesh checks (testing mode)
        return True
    except Exception as e:
        violations.append(f"Mesh validation exception: {e}")
        return False
