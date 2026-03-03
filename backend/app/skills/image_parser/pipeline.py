"""Image parser pipeline orchestrator.

Orchestrates: detect → measure → normalize → confidence score.

3-Tier fallback strategy:
  Tier 1: YOLO (best quality, requires fine-tuned weights)
  Tier 2: OpenCV heuristic (Hough circles + contour analysis)
  Tier 3: Pure defaults (no CV at all — zero-dependency safe mode)

Source of truth: jewelry-image-parser/SKILL.md
  Priority order: Structural correctness > Symmetry > Manufacturability > Visual approximation
  Prohibited: No hallucinated filigree, no inferred engraving, no gemstone color guessing
"""

from __future__ import annotations

import logging
from pathlib import Path

from app.config import settings
from app.schemas.parametric import CenterStone, ParametricRing
from app.schemas.parse_result import ParseResult

from .confidence import compute_confidence
from .detector import detect_jewelry
from .measurer import measure_from_detections
from .normalizer import normalize_to_parametric

log = logging.getLogger(__name__)

# Fallback defaults from SKILL (when confidence < threshold or CV unavailable)
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

# Per-component fallback thresholds
BAND_CONFIDENCE_THRESHOLD = 0.4
STONE_CONFIDENCE_THRESHOLD = 0.3


def _make_fallback_result(
    reason: str,
    confidence: float = 0.0,
) -> ParseResult:
    """Return conservative defaults with zero confidence."""
    log.info("Using fallback defaults: %s", reason)
    return ParseResult(
        params=FALLBACK_PARAMS.model_copy(deep=True),
        confidence_score=confidence,
        band_confidence=0.0,
        stone_confidence=0.0,
        setting_confidence=0.0,
        symmetry_confidence=0.0,
    )


def parse_image(image_path: Path) -> ParseResult:
    """Full image parsing pipeline.

    Steps:
      1. Detect jewelry components (YOLO → Hough heuristic → fallback)
      2. Measure geometric proportions from detections
      3. Normalize measurements to mm using scale defaults
      4. Compute confidence scores
      5. Apply per-component fallback when confidence < threshold
      6. If overall confidence < 0.6 → use full conservative defaults

    Args:
        image_path: Path to the uploaded jewelry image.

    Returns:
        ParseResult with parametric JSON + confidence scores.
    """
    # ── Tier 3: If OpenCV not available, return pure defaults ──────
    try:
        import cv2
    except ImportError:
        return _make_fallback_result("OpenCV not available")

    # Read image
    img = cv2.imread(str(image_path))
    if img is None:
        return _make_fallback_result("Cannot read image file")

    # ── 1. Detect ──────────────────────────────────────────────────
    try:
        detections = detect_jewelry(image_path)
    except Exception as exc:
        log.warning("Detection failed: %s", exc)
        return _make_fallback_result(f"Detection error: {exc}")

    # ── 2. Measure ─────────────────────────────────────────────────
    measurements = measure_from_detections(img, detections)

    # ── 3. Normalize to parametric ─────────────────────────────────
    params = normalize_to_parametric(measurements)

    # ── 4. Confidence ──────────────────────────────────────────────
    scores = compute_confidence(detections)

    # ── 5. Per-component fallback (graceful degradation) ───────────
    # If band detection is weak, keep defaults for ring dimensions
    if scores["band_confidence"] < BAND_CONFIDENCE_THRESHOLD:
        log.info("Low band confidence (%.2f) — using default ring dimensions", scores["band_confidence"])
        params = params.model_copy(update={
            "ring_radius": FALLBACK_PARAMS.ring_radius,
            "band_width": FALLBACK_PARAMS.band_width,
            "band_thickness": FALLBACK_PARAMS.band_thickness,
        })

    # If stone detection is weak, keep defaults for stone
    if scores["stone_confidence"] < STONE_CONFIDENCE_THRESHOLD:
        log.info("Low stone confidence (%.2f) — using default stone params", scores["stone_confidence"])
        params = params.model_copy(update={
            "center_stone": FALLBACK_PARAMS.center_stone.model_copy(deep=True),
        })

    # ── 6. Full fallback if overall confidence too low ─────────────
    if scores["confidence_score"] < settings.CONFIDENCE_THRESHOLD:
        log.info("Overall confidence %.2f < threshold %.2f — full fallback",
                 scores["confidence_score"], settings.CONFIDENCE_THRESHOLD)
        params = FALLBACK_PARAMS.model_copy(deep=True)

    return ParseResult(
        params=params,
        confidence_score=scores["confidence_score"],
        band_confidence=scores["band_confidence"],
        stone_confidence=scores["stone_confidence"],
        setting_confidence=scores["setting_confidence"],
        symmetry_confidence=scores["symmetry_confidence"],
    )
