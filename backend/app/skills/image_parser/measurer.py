"""Geometric measurement extraction from image detections.

Source of truth: jewelry-image-parser/SKILL.md

Extracts pixel-space ratios and geometric relationships that the
normalizer will convert into real-world mm dimensions.

Key measurements:
  - band_width_ratio: (outer_r − inner_r) / ring_diameter
  - stone_to_ring_ratio: stone_diameter_px / ring_diameter_px
  - stone shape via aspect ratio + ellipse data
  - prong count
  - perspective correction via ellipse axis ratio
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None  # type: ignore
    np = None  # type: ignore

from .detector import Detection, DetectionResult

log = logging.getLogger(__name__)


@dataclass
class Measurements:
    """Raw measurements extracted from image (in pixel ratios)."""
    # Band measurements (as ratios relative to image / ring size)
    ring_outer_radius_px: float = 0.0
    ring_inner_radius_px: float = 0.0
    band_width_ratio: float = 0.0  # band_width / ring_diameter

    # Perspective correction factor (1.0 = no correction needed)
    perspective_factor: float = 1.0

    # Stone measurements
    stone_width_px: float = 0.0
    stone_height_px: float = 0.0
    stone_shape: str = "round"
    stone_to_ring_ratio: float = 0.0  # stone_diameter / ring_diameter

    # Prong count
    detected_prong_count: int = 0

    # Image scale
    image_height: int = 0
    image_width: int = 0


def measure_from_detections(
    image: "np.ndarray",
    detections: DetectionResult,
) -> Measurements:
    """Extract geometric measurements from detections.

    Uses ellipse data (if available from heuristic path) for more
    accurate measurements. Falls back to bbox-based approximations.
    """
    m = Measurements()
    h, w = image.shape[:2]
    m.image_height = h
    m.image_width = w

    # ── Ring band measurements ─────────────────────────────────────
    if detections.ring_band is not None:
        x1, y1, x2, y2 = detections.ring_band.bbox
        ring_w = x2 - x1
        ring_h = y2 - y1

        # Use detected circle radius if available (more accurate)
        if detections.ring_band.radius is not None:
            m.ring_outer_radius_px = float(detections.ring_band.radius)
        else:
            m.ring_outer_radius_px = (ring_w + ring_h) / 4.0

        # Perspective correction: ratio of minor/major axis
        if ring_w > 0 and ring_h > 0:
            m.perspective_factor = min(ring_w, ring_h) / max(ring_w, ring_h)
        else:
            m.perspective_factor = 1.0

        # Use ellipse data if available for better inner radius estimate
        if detections.ring_ellipse is not None:
            (_, _), (ma, mi), _ = detections.ring_ellipse
            outer_r = (ma + mi) / 4.0
            m.ring_outer_radius_px = outer_r

        # Estimate inner radius using edge analysis within the ring bbox
        inner_ratio = _estimate_inner_radius_ratio(image, detections.ring_band)
        m.ring_inner_radius_px = m.ring_outer_radius_px * inner_ratio

        ring_diameter = m.ring_outer_radius_px * 2.0
        if ring_diameter > 0:
            m.band_width_ratio = (m.ring_outer_radius_px - m.ring_inner_radius_px) / ring_diameter

    # ── Center stone measurements ──────────────────────────────────
    if detections.center_stone is not None:
        sx1, sy1, sx2, sy2 = detections.center_stone.bbox
        m.stone_width_px = float(sx2 - sx1)
        m.stone_height_px = float(sy2 - sy1)

        # Shape classification (use ellipse data if available)
        m.stone_shape = _classify_stone_shape(
            m.stone_width_px, m.stone_height_px, detections.stone_ellipse
        )

        # Stone to ring ratio
        if m.ring_outer_radius_px > 0:
            # Use the larger dimension (corrected for perspective)
            stone_apparent_diameter = max(m.stone_width_px, m.stone_height_px)
            m.stone_to_ring_ratio = stone_apparent_diameter / (m.ring_outer_radius_px * 2)

    # ── Prong count ────────────────────────────────────────────────
    raw_count = len(detections.prongs)

    # Heuristic: if we detected some but not all prongs (partial image),
    # round up to nearest even number (prongs are almost always symmetric)
    if 1 <= raw_count <= 2:
        m.detected_prong_count = 4  # likely missed some
    elif 3 <= raw_count <= 5:
        m.detected_prong_count = raw_count if raw_count in (3, 4) else 4
    elif raw_count >= 6:
        m.detected_prong_count = min(8, raw_count)
    else:
        m.detected_prong_count = 0  # none found → normalizer will default to 4

    return m


def _estimate_inner_radius_ratio(
    image: "np.ndarray", ring_det: Detection
) -> float:
    """Estimate inner_radius / outer_radius from edge density within the ring bbox.

    The ring band is the area between inner and outer circles.
    Analyze radial edge density to find the band boundary.
    Returns inner_radius as a fraction of outer_radius (typically 0.70–0.88).
    """
    try:
        x1, y1, x2, y2 = ring_det.bbox
        roi = image[y1:y2, x1:x2]
        if roi.size == 0:
            return 0.80

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi
        edges = cv2.Canny(gray, 50, 150)

        rh, rw = edges.shape
        cx, cy = rw // 2, rh // 2
        outer_r = max(rw, rh) // 2

        # Sample edge density at different radii from center
        radii = np.linspace(outer_r * 0.5, outer_r * 0.95, 20)
        densities = []
        for r in radii:
            # Create ring-shaped mask at this radius
            mask = np.zeros_like(edges)
            cv2.circle(mask, (cx, cy), int(r + 2), 255, 4)
            overlap = cv2.bitwise_and(edges, mask)
            densities.append(np.sum(overlap > 0))

        if densities:
            # Inner boundary is where edge density peaks (inner edge of band)
            peak_idx = int(np.argmax(densities))
            inner_ratio = float(radii[peak_idx]) / outer_r
            # Clamp to reasonable range
            return max(0.65, min(0.90, inner_ratio))

    except Exception:
        pass

    return 0.80  # safe default


def _classify_stone_shape(
    width_px: float,
    height_px: float,
    ellipse_data: object,
) -> str:
    """Classify stone shape per SKILL rules.

    - Circular → "round"
    - Elongated symmetric → "oval"
    - Rectangular step-cut → "emerald"
    - Teardrop → "pear"
    - Ambiguous → "round" (default)
    """
    if width_px <= 0 or height_px <= 0:
        return "round"

    aspect = width_px / height_px

    # Use ellipse eccentricity if available for better classification
    eccentricity = 0.0
    if ellipse_data is not None:
        try:
            (_, _), (ma, mi), _ = ellipse_data
            if ma > 0 and mi > 0:
                a = max(ma, mi) / 2
                b = min(ma, mi) / 2
                eccentricity = math.sqrt(1 - (b / a) ** 2) if a > 0 else 0
        except (TypeError, ValueError):
            pass

    # Classification logic
    if 0.85 <= aspect <= 1.18 and eccentricity < 0.45:
        return "round"
    elif eccentricity > 0.7 and aspect > 1.3:
        return "oval"
    elif aspect > 1.15 and aspect <= 1.6:
        return "oval"
    elif height_px > width_px * 1.3:
        return "pear"
    else:
        return "round"  # default per SKILL
