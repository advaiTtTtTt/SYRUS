"""Confidence scoring.

Source of truth: jewelry-image-parser/SKILL.md

Weighted average of:
  - Band detection confidence    (35%)
  - Center stone detection       (30%)
  - Setting classification       (15%)
  - Symmetry validation          (20%)

Range 0.0–1.0. If < 0.6 → conservative defaults, reduce complexity.

Confidence is also boosted or penalized based on geometric sanity:
  - Stone inside ring bbox   → +bonus
  - Stone larger than ring   → penalty
  - Ring nearly circular     → symmetry boost
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

    # ── Setting confidence ─────────────────────────────────────────
    if len(detections.prongs) >= 4:
        setting_conf = min(1.0, 0.5 + len(detections.prongs) * 0.1)
    elif len(detections.prongs) >= 2:
        setting_conf = min(0.7, len(detections.prongs) * 0.2)
    elif detections.center_stone:
        setting_conf = 0.3  # assume prong by default
    else:
        setting_conf = 0.0

    # ── Symmetry confidence ────────────────────────────────────────
    symmetry_conf = 0.0
    if detections.ring_band:
        x1, y1, x2, y2 = detections.ring_band.bbox
        w = x2 - x1
        h = y2 - y1
        if max(w, h) > 0:
            aspect = min(w, h) / max(w, h)
            symmetry_conf = aspect  # 1.0 = perfect circle

    # ── Geometric sanity bonuses/penalties ──────────────────────────
    geo_bonus = 0.0
    if detections.ring_band and detections.center_stone:
        rb = detections.ring_band.bbox
        cs = detections.center_stone.bbox

        # Check if stone is geometrically inside the ring bbox
        stone_cx = (cs[0] + cs[2]) / 2
        stone_cy = (cs[1] + cs[3]) / 2
        if rb[0] <= stone_cx <= rb[2] and rb[1] <= stone_cy <= rb[3]:
            geo_bonus += 0.05  # stone center inside ring — good
        else:
            geo_bonus -= 0.10  # stone outside ring — suspicious

        # Check stone isn't larger than ring
        stone_w = cs[2] - cs[0]
        ring_w = rb[2] - rb[0]
        if stone_w > ring_w * 0.9:
            geo_bonus -= 0.10  # stone too large — likely misdetection

    overall = (
        WEIGHT_BAND * band_conf
        + WEIGHT_STONE * stone_conf
        + WEIGHT_SETTING * setting_conf
        + WEIGHT_SYMMETRY * symmetry_conf
        + geo_bonus
    )

    # Clamp to [0, 1]
    overall = max(0.0, min(1.0, overall))

    return {
        "band_confidence": round(band_conf, 3),
        "stone_confidence": round(stone_conf, 3),
        "setting_confidence": round(setting_conf, 3),
        "symmetry_confidence": round(symmetry_conf, 3),
        "confidence_score": round(overall, 3),
    }
