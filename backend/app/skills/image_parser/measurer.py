"""Geometric measurement extraction from image detections.

Source of truth: jewelry-image-parser/SKILL.md

Ring detection rules:
  - Detect circular/elliptical band
  - estimate inner/outer boundary
  - band_width = outer_radius − inner_radius
  - ring_radius = average(inner_diameter / 2)
  - Ellipse from perspective → correct using vertical axis scaling

Center stone identification:
  - Detect largest gemstone inside ring boundary
  - Shape classification: circular → round, elongated → oval, etc.
  - Diameter from bounding box width, normalized to band width
"""

from __future__ import annotations

from dataclasses import dataclass

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None  # type: ignore
    np = None  # type: ignore

from .detector import Detection, DetectionResult


@dataclass
class Measurements:
    """Raw measurements extracted from image (in pixel ratios)."""
    # Band measurements (as ratios relative to image / ring size)
    ring_outer_radius_px: float = 0.0
    ring_inner_radius_px: float = 0.0
    band_width_ratio: float = 0.0  # band_width / ring_diameter

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
    image: np.ndarray,
    detections: DetectionResult,
) -> Measurements:
    """Extract geometric measurements from detection bounding boxes."""
    m = Measurements()
    h, w = image.shape[:2]
    m.image_height = h
    m.image_width = w

    # ── Ring band measurements ─────────────────────────────────────
    if detections.ring_band is not None:
        x1, y1, x2, y2 = detections.ring_band.bbox
        ring_w = x2 - x1
        ring_h = y2 - y1

        # Approximate outer radius (average of width/height for ellipse correction)
        m.ring_outer_radius_px = (ring_w + ring_h) / 4.0

        # Estimate inner radius: assume band takes up ~15-25% of ring diameter
        # This is refined if we have edge detection data
        inner_estimate_ratio = 0.80  # inner radius ≈ 80% of outer
        m.ring_inner_radius_px = m.ring_outer_radius_px * inner_estimate_ratio

        m.band_width_ratio = (m.ring_outer_radius_px - m.ring_inner_radius_px) / (m.ring_outer_radius_px * 2)

    # ── Center stone measurements ──────────────────────────────────
    if detections.center_stone is not None:
        sx1, sy1, sx2, sy2 = detections.center_stone.bbox
        m.stone_width_px = sx2 - sx1
        m.stone_height_px = sy2 - sy1

        # Shape classification
        aspect = m.stone_width_px / max(m.stone_height_px, 1)
        if 0.85 <= aspect <= 1.15:
            m.stone_shape = "round"
        elif aspect > 1.15 and aspect <= 1.5:
            m.stone_shape = "oval"
        elif m.stone_height_px > m.stone_width_px * 1.3:
            m.stone_shape = "pear"
        else:
            m.stone_shape = "round"  # default per SKILL

        # Stone to ring ratio
        if m.ring_outer_radius_px > 0:
            m.stone_to_ring_ratio = m.stone_width_px / (m.ring_outer_radius_px * 2)

    # ── Prong count ────────────────────────────────────────────────
    m.detected_prong_count = len(detections.prongs)

    return m
