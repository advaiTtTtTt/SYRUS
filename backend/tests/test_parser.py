"""Tests for jewelry-image-parser SKILL (unit tests without actual images).

Mocks cv2/numpy imports since those heavy packages aren't installed in test env.
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

    def test_oval_shape_detected(self):
        m = Measurements(
            stone_width_px=100,
            stone_height_px=75,  # aspect = 1.33, > 1.15 → oval
            stone_shape="oval",
        )
        result = normalize_to_parametric(m)
        assert result.center_stone.type.value == "oval"  # normalizer preserves measurer's shape


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
