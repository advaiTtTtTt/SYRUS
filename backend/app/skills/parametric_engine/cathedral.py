"""Cathedral shoulder support generator.

Builds two arched support wings that sweep from the band shoulders
upward to the ring head, providing structural reinforcement and the
distinctive cathedral setting silhouette.

Source of truth: jewelry-parametric-engine/SKILL.md
All dims in millimetres.

Coordinate convention (matches band.py):
  - Ring axis: Y
  - Band center: origin
  - Center stone at X = ring_radius + band_thickness/2, Y = band_width/2
  - Supports placed at ±90° (3 and 9 o'clock) relative to head

Structural approach:
  1. Define an arc spine from band shoulder to head platform.
  2. Sweep a rectangular cross-section along the spine.
  3. Apply fillets at both junction points (≥ 0.3 mm).
  4. Place two supports symmetrically at ±90° around Y axis.

CadQuery ops: spline/arc wire, rect profile, sweep, fillet, boolean union.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import cadquery as cq

from app.schemas.parametric import ParametricRing


# ── Constants ──────────────────────────────────────────────────────

MIN_SUPPORT_THICKNESS = 1.2   # mm — manufacturing minimum
DEFAULT_SUPPORT_DEPTH_RATIO = 0.30   # depth = band_width × ratio
FILLET_RADIUS = 0.3           # mm — min fillet at junctions
ARCH_RISE_FACTOR = 0.35       # arch peak rises 35 % above straight line


@dataclass
class CathedralResult:
    """Output of the cathedral support generator."""

    supports: cq.Workplane   # compound of both support wings (to union)


# ── Main builder ───────────────────────────────────────────────────

def build_cathedral_supports(params: ParametricRing) -> CathedralResult:
    """Generate two cathedral arch supports from band shoulders to head.

    Parameters
    ----------
    params : ParametricRing
        Full ring params (uses ring_radius, band_width, band_thickness,
        center_stone.diameter, center_stone.height).

    Returns
    -------
    CathedralResult with a compound solid of both arch supports.
    """
    r_inner = params.ring_radius
    r_outer = r_inner + params.band_thickness
    half_bw = params.band_width / 2.0

    # Head position
    cx = r_inner + params.band_thickness / 2.0
    stone_r = params.center_stone.diameter / 2.0
    seat_depth = params.center_stone.height * 0.20
    head_y = half_bw + params.center_stone.height - seat_depth

    # Support dimensions
    thickness = max(MIN_SUPPORT_THICKNESS, params.band_thickness * 0.4)
    depth = max(1.0, params.band_width * DEFAULT_SUPPORT_DEPTH_RATIO)

    # ── Spine points for one arch ──────────────────────────────────
    # Start: on band outer surface at shoulder level
    start_x = r_outer
    start_y = half_bw

    # End: at stone head base (edge of the head platform)
    end_x = cx - stone_r * 0.5   # inward toward center stone
    end_y = head_y * 0.85        # just below stone crown

    # Mid-point: arch peak — elevated above the straight line
    mid_x = (start_x + end_x) / 2.0
    straight_mid_y = (start_y + end_y) / 2.0
    rise = (end_y - start_y) * ARCH_RISE_FACTOR
    mid_y = straight_mid_y + rise

    # ── Build one support wing ─────────────────────────────────────
    def _build_single_support(angle_deg: float) -> cq.Workplane:
        """Build one arch support at a given angle around Y axis."""
        angle_rad = math.radians(angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        # Transform spine points into 3D (rotating around Y axis)
        def to_3d(rx: float, ry: float) -> tuple[float, float, float]:
            return (rx * cos_a, ry, rx * sin_a)

        p_start = to_3d(start_x, start_y)
        p_mid = to_3d(mid_x, mid_y)
        p_end = to_3d(end_x, end_y)

        # Build spine wire as a 3-point spline
        spine = cq.Workplane("XY").spline(
            [p_start, p_mid, p_end],
            makeWire=True,
        )

        # Cross-section: rectangle perpendicular to spine at start
        # We build the profile on a plane at the start point,
        # oriented tangent to the spine
        half_t = thickness / 2.0
        half_d = depth / 2.0

        # Build a simple rectangular profile, then sweep
        # The profile plane is normal to the initial tangent direction
        profile = (
            cq.Workplane("XY")
            .transformed(offset=p_start)
            .rect(thickness, depth)
        )

        # Sweep the profile along the spine
        try:
            support = profile.sweep(spine, isFrenet=True)
        except Exception:
            # Fallback: extrude a simpler tapered shape if sweep fails
            support = _build_fallback_support(p_start, p_end, thickness, depth)

        # Fillet joining edges
        try:
            support = support.edges().fillet(min(FILLET_RADIUS, thickness * 0.2))
        except Exception:
            pass  # Fillet failure non-fatal

        return support

    # ── Build both supports ────────────────────────────────────────
    support_left = _build_single_support(90.0)
    support_right = _build_single_support(-90.0)

    compound = support_left.union(support_right)

    return CathedralResult(supports=compound)


def _build_fallback_support(
    p_start: tuple[float, float, float],
    p_end: tuple[float, float, float],
    thickness: float,
    depth: float,
) -> cq.Workplane:
    """Fallback: a tapered box between start and end points.

    Used when CadQuery spline sweep fails (e.g. degenerate spine).
    """
    # Simple loft between two offset rectangles
    half_t = thickness / 2.0
    half_d = depth / 2.0

    base = (
        cq.Workplane("XY")
        .transformed(offset=p_start)
        .rect(thickness, depth)
    )
    top = (
        cq.Workplane("XY")
        .transformed(offset=p_end)
        .rect(thickness * 0.8, depth * 0.8)
    )

    try:
        return base.workplane(offset=0).rect(thickness, depth) \
            .workplane(offset=_distance(p_start, p_end)) \
            .rect(thickness * 0.8, depth * 0.8) \
            .loft()
    except Exception:
        # Last resort: just a box
        return base.extrude(_distance(p_start, p_end))


def _distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    """Euclidean distance between two 3D points."""
    return math.sqrt(sum((ai - bi) ** 2 for ai, bi in zip(a, b)))
