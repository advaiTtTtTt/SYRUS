"""Image parser pipeline orchestrator.

Orchestrates: YOLO detect → SAM segment → measure → normalize → confidence score.

Source of truth: jewelry-image-parser/SKILL.md
  Priority order: Structural correctness > Symmetry > Manufacturability > Visual approximation
  Prohibited: No hallucinated filigree, no inferred engraving, no gemstone color guessing
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from app.config import settings
from app.schemas.parametric import CenterStone, ParametricRing
from app.schemas.parse_result import ParseResult

from .confidence import compute_confidence
from .detector import detect_jewelry
from .measurer import measure_from_detections
from .normalizer import normalize_to_parametric

# Fallback defaults from SKILL (when confidence < threshold)
FALLBACK_PARAMS = ParametricRing(
    ring_radius=9.0,
    band_width=2.2,
    band_thickness=1.8,
    center_stone=CenterStone(
        type="round",
        diameter=6.0,
        height=3.6,
        prongs=4,
    ),
    setting_type="prong",
    side_stones=[],
)


def parse_image(image_path: Path) -> ParseResult:
    """Full image parsing pipeline.

    Steps:
      1. Detect jewelry components (YOLO / heuristic fallback)
      2. Measure geometric proportions from detections
      3. Normalize measurements to mm using scale defaults
      4. Compute confidence scores
      5. If confidence < 0.6 → use conservative defaults

    Args:
        image_path: Path to the uploaded jewelry image.

    Returns:
        ParseResult with parametric JSON + confidence scores.
    """
    import cv2

    # Read image
    img = cv2.imread(str(image_path))
    if img is None:
        # Cannot read — return fallback defaults
        return ParseResult(
            params=FALLBACK_PARAMS.model_copy(deep=True),
            confidence_score=0.0,
            band_confidence=0.0,
            stone_confidence=0.0,
            setting_confidence=0.0,
            symmetry_confidence=0.0,
        )

    # ── 1. Detect ──────────────────────────────────────────────────
    detections = detect_jewelry(image_path)

    # ── 2. Measure ─────────────────────────────────────────────────
    measurements = measure_from_detections(img, detections)

    # ── 3. Normalize to parametric ─────────────────────────────────
    params = normalize_to_parametric(measurements)

    # ── 4. Confidence ──────────────────────────────────────────────
    scores = compute_confidence(detections)

    # ── 5. Low confidence → fallback defaults ──────────────────────
    if scores["confidence_score"] < settings.CONFIDENCE_THRESHOLD:
        params = FALLBACK_PARAMS.model_copy(deep=True)

    return ParseResult(
        params=params,
        confidence_score=scores["confidence_score"],
        band_confidence=scores["band_confidence"],
        stone_confidence=scores["stone_confidence"],
        setting_confidence=scores["setting_confidence"],
        symmetry_confidence=scores["symmetry_confidence"],
    )
