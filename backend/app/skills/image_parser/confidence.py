"""Confidence scoring.

Source of truth: jewelry-image-parser/SKILL.md

Weighted average of:
  - Band detection confidence
  - Center stone detection confidence
  - Setting classification confidence
  - Symmetry validation confidence

Range 0.0–1.0. If < 0.6 → conservative defaults, reduce complexity.
"""

from __future__ import annotations

from .detector import DetectionResult

# Weights for confidence components
WEIGHT_BAND = 0.35
WEIGHT_STONE = 0.30
WEIGHT_SETTING = 0.15
WEIGHT_SYMMETRY = 0.20


def compute_confidence(detections: DetectionResult) -> dict[str, float]:
    """Compute per-component and overall confidence scores."""

    band_conf = detections.ring_band.confidence if detections.ring_band else 0.0
    stone_conf = detections.center_stone.confidence if detections.center_stone else 0.0

    # Setting confidence: if we detected prongs, higher confidence
    if len(detections.prongs) >= 2:
        setting_conf = min(1.0, len(detections.prongs) * 0.2)
    elif detections.center_stone:
        setting_conf = 0.3  # assume prong by default
    else:
        setting_conf = 0.0

    # Symmetry: check if ring band bbox is approximately square (circular)
    if detections.ring_band:
        x1, y1, x2, y2 = detections.ring_band.bbox
        w = x2 - x1
        h = y2 - y1
        aspect = min(w, h) / max(w, h) if max(w, h) > 0 else 0
        symmetry_conf = aspect  # 1.0 = perfect circle
    else:
        symmetry_conf = 0.0

    overall = (
        WEIGHT_BAND * band_conf
        + WEIGHT_STONE * stone_conf
        + WEIGHT_SETTING * setting_conf
        + WEIGHT_SYMMETRY * symmetry_conf
    )

    return {
        "band_confidence": round(band_conf, 3),
        "stone_confidence": round(stone_conf, 3),
        "setting_confidence": round(setting_conf, 3),
        "symmetry_confidence": round(symmetry_conf, 3),
        "confidence_score": round(overall, 3),
    }
