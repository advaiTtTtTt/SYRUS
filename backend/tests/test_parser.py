"""Tests for jewelry-image-parser SKILL (unit tests without actual images).

Covers:
  - Normalizer: pixel ratios → mm params
  - Confidence scorer: detection quality evaluation
  - Measurer: detection → measurement extraction
  - Pipeline: fallback logic when OpenCV unavailable
  - Detector: data class construction
"""

import pytest
import sys
import os
from unittest.mock import MagicMock

# Mock heavy CV dependencies before any app imports
cv2_mock = MagicMock()
cv2_mock.__version__ = "4.10.0"
sys.modules.setdefault("cv2", cv2_mock)

# numpy should already be installed, but mock ultralytics/torch/SAM
for mod in ["ultralytics", "torch", "torchvision", "segment_anything"]:
    sys.modules.setdefault(mod, MagicMock())

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.schemas.parametric import ParametricRing
from app.skills.image_parser.normalizer import normalize_to_parametric
from app.skills.image_parser.measurer import Measurements
from app.skills.image_parser.confidence import compute_confidence
from app.skills.image_parser.detector import Detection, DetectionResult


# ── Normalizer tests ───────────────────────────────────────────────

class TestNormalization:
    def test_default_measurements_produce_defaults(self):
        """Empty measurements should return SKILL-defined defaults."""
        m = Measurements()
        result = normalize_to_parametric(m)
        assert result.ring_radius == 9.0
        assert result.band_width == 2.2
        assert result.band_thickness == 1.8
        assert result.center_stone.diameter == 6.0

    def test_stone_ratio_applied(self):
        m = Measurements(
            ring_outer_radius_px=100,
            ring_inner_radius_px=80,
            band_width_ratio=0.1,
            stone_width_px=60,
            stone_height_px=60,
            stone_shape="round",
            stone_to_ring_ratio=0.3,
        )
        result = normalize_to_parametric(m)
        # stone_diameter = 9.0 * 2.0 * 0.3 = 5.4
        assert abs(result.center_stone.diameter - 5.4) < 0.1

    def test_prong_count_defaults_to_4(self):
        m = Measurements(detected_prong_count=0)
        result = normalize_to_parametric(m)
        assert result.center_stone.prongs == 4

    def test_prong_count_clamped_to_range(self):
        m = Measurements(detected_prong_count=6)
        result = normalize_to_parametric(m)
        assert 3 <= result.center_stone.prongs <= 8

    def test_oval_shape_detected(self):
        m = Measurements(
            stone_width_px=100,
            stone_height_px=75,
            stone_shape="oval",
        )
        result = normalize_to_parametric(m)
        assert result.center_stone.type.value == "oval"

    def test_pear_shape_detected(self):
        m = Measurements(stone_shape="pear")
        result = normalize_to_parametric(m)
        assert result.center_stone.type.value == "pear"

    def test_band_width_clamped_minimum(self):
        """Very thin band ratio should clamp to min 1.5mm."""
        m = Measurements(band_width_ratio=0.01)  # very thin
        result = normalize_to_parametric(m)
        assert result.band_width >= 1.5

    def test_band_width_clamped_maximum(self):
        """Very thick band ratio should clamp to max 6.0mm."""
        m = Measurements(band_width_ratio=0.9)  # huge
        result = normalize_to_parametric(m)
        assert result.band_width <= 6.0

    def test_stone_diameter_clamped_minimum(self):
        m = Measurements(stone_to_ring_ratio=0.01)  # tiny stone
        result = normalize_to_parametric(m)
        assert result.center_stone.diameter >= 3.0

    def test_stone_diameter_clamped_maximum(self):
        m = Measurements(stone_to_ring_ratio=2.0)  # huge stone
        result = normalize_to_parametric(m)
        assert result.center_stone.diameter <= 12.0

    def test_perspective_correction_widens_band(self):
        """Perspective factor < 1 should widen band estimate."""
        m_normal = Measurements(band_width_ratio=0.1, perspective_factor=1.0)
        m_persp = Measurements(band_width_ratio=0.1, perspective_factor=0.7)
        r_normal = normalize_to_parametric(m_normal)
        r_persp = normalize_to_parametric(m_persp)
        # Perspective-corrected band should be wider
        assert r_persp.band_width >= r_normal.band_width

    def test_thick_band_gets_proportional_thickness(self):
        """Band > 3mm → band_thickness estimated proportionally."""
        m = Measurements(band_width_ratio=0.25)
        result = normalize_to_parametric(m)
        if result.band_width > 3.0:
            assert result.band_thickness > 1.8  # thicker than default

    def test_setting_type_always_prong(self):
        """MVP: setting_type is always 'prong'."""
        m = Measurements()
        result = normalize_to_parametric(m)
        assert result.setting_type == "prong"

    def test_side_stones_empty(self):
        """MVP: no side stone detection."""
        m = Measurements()
        result = normalize_to_parametric(m)
        assert result.side_stones == []


# ── Confidence tests ───────────────────────────────────────────────

class TestConfidence:
    def test_no_detections_zero_confidence(self):
        det = DetectionResult()
        scores = compute_confidence(det)
        assert scores["confidence_score"] == 0.0

    def test_good_detections_high_confidence(self):
        det = DetectionResult(
            ring_band=Detection("ring_band", 0.9, (10, 10, 200, 200)),
            center_stone=Detection("center_stone", 0.85, (80, 80, 130, 130)),
            prongs=[
                Detection("prong", 0.7, (0, 0, 10, 10)),
                Detection("prong", 0.7, (0, 0, 10, 10)),
                Detection("prong", 0.7, (0, 0, 10, 10)),
                Detection("prong", 0.7, (0, 0, 10, 10)),
            ],
        )
        scores = compute_confidence(det)
        assert scores["confidence_score"] > 0.5

    def test_confidence_in_range(self):
        det = DetectionResult(
            ring_band=Detection("ring_band", 0.5, (0, 0, 100, 100)),
        )
        scores = compute_confidence(det)
        assert 0.0 <= scores["confidence_score"] <= 1.0

    def test_geometric_bonus_stone_inside_ring(self):
        """Stone inside ring bbox → confidence should include bonus."""
        det = DetectionResult(
            ring_band=Detection("ring_band", 0.7, (10, 10, 200, 200)),
            center_stone=Detection("center_stone", 0.6, (80, 50, 130, 100)),
        )
        scores = compute_confidence(det)
        assert scores["confidence_score"] > 0.3

    def test_geometric_penalty_stone_outside_ring(self):
        """Stone completely outside ring → lower confidence."""
        det_inside = DetectionResult(
            ring_band=Detection("ring_band", 0.7, (10, 10, 200, 200)),
            center_stone=Detection("center_stone", 0.6, (80, 80, 130, 130)),
        )
        det_outside = DetectionResult(
            ring_band=Detection("ring_band", 0.7, (10, 10, 200, 200)),
            center_stone=Detection("center_stone", 0.6, (300, 300, 400, 400)),
        )
        sc_in = compute_confidence(det_inside)["confidence_score"]
        sc_out = compute_confidence(det_outside)["confidence_score"]
        assert sc_in > sc_out

    def test_many_prongs_boost_setting_confidence(self):
        """4+ prongs should give higher setting confidence."""
        det = DetectionResult(
            ring_band=Detection("ring_band", 0.7, (0, 0, 200, 200)),
            prongs=[Detection("prong", 0.5, (0, 0, 10, 10)) for _ in range(6)],
        )
        scores = compute_confidence(det)
        assert scores["setting_confidence"] > 0.5

    def test_all_confidence_keys_present(self):
        det = DetectionResult()
        scores = compute_confidence(det)
        expected_keys = {"band_confidence", "stone_confidence", "setting_confidence",
                         "symmetry_confidence", "confidence_score"}
        assert set(scores.keys()) == expected_keys

    def test_circular_ring_high_symmetry(self):
        """Square bbox (circular ring) → high symmetry confidence."""
        det = DetectionResult(
            ring_band=Detection("ring_band", 0.5, (50, 50, 250, 250)),  # 200x200 = perfectly square
        )
        scores = compute_confidence(det)
        assert scores["symmetry_confidence"] == 1.0


# ── Detector data class tests ──────────────────────────────────────

class TestDetector:
    def test_detection_result_defaults(self):
        dr = DetectionResult()
        assert dr.ring_band is None
        assert dr.center_stone is None
        assert dr.prongs == []
        assert dr.raw_detections == []

    def test_detection_with_optional_fields(self):
        d = Detection(
            label="ring_band",
            confidence=0.8,
            bbox=(10, 10, 200, 200),
            center=(105, 105),
            radius=95,
        )
        assert d.center == (105, 105)
        assert d.radius == 95
        assert d.mask is None

    def test_detection_result_with_ellipse(self):
        dr = DetectionResult()
        dr.ring_ellipse = ((100, 100), (200, 190), 0)
        assert dr.ring_ellipse is not None


# ── Pipeline fallback tests ────────────────────────────────────────

class TestPipelineFallback:
    def test_fallback_params_valid(self):
        """FALLBACK_PARAMS must pass schema validation."""
        from app.skills.image_parser.pipeline import FALLBACK_PARAMS
        assert FALLBACK_PARAMS.ring_radius == 9.0
        assert FALLBACK_PARAMS.center_stone.prongs == 4
        assert FALLBACK_PARAMS.setting_type == "prong"
        assert FALLBACK_PARAMS.side_stones == []

    def test_fallback_result_factory(self):
        from app.skills.image_parser.pipeline import _make_fallback_result
        result = _make_fallback_result("test reason")
        assert result.confidence_score == 0.0
        assert result.params.ring_radius == 9.0
        assert result.params.center_stone.diameter == 6.0
