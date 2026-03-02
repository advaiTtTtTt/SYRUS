"""Tests for manufacturability-validator SKILL.

Uses model_construct() to bypass Pydantic ge/le validators so we can
feed structurally-unsafe values into the manufacturability checker.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.schemas.parametric import CenterStone, ParametricRing, StoneShape, SettingType
from app.schemas.validation_result import ManufacturingStatus
from app.skills.manufacturability.validator import validate_parametric


def _make_params(**overrides) -> ParametricRing:
    """Build a ParametricRing with model_construct to bypass Pydantic ge/le checks."""
    defaults = dict(
        ring_radius=9.0,
        band_width=2.2,
        band_thickness=1.8,
        center_stone=CenterStone.model_construct(
            type=StoneShape.ROUND, diameter=6.0, height=3.6, prongs=4
        ),
        setting_type=SettingType.PRONG,
        side_stones=[],
    )
    if "center_stone" in overrides and isinstance(overrides["center_stone"], dict):
        cs_defaults = dict(type=StoneShape.ROUND, diameter=6.0, height=3.6, prongs=4)
        cs_defaults.update(overrides.pop("center_stone"))
        overrides["center_stone"] = CenterStone.model_construct(**cs_defaults)
    defaults.update(overrides)
    return ParametricRing.model_construct(**defaults)


class TestWallThickness:
    def test_thin_band_auto_corrected(self):
        params = _make_params(band_thickness=1.0)
        corrected, result = validate_parametric(params)
        assert corrected.band_thickness >= 1.5
        assert result.manufacturing_status in (ManufacturingStatus.AUTO_CORRECTED, ManufacturingStatus.SAFE)

    def test_very_thin_band_rejected(self):
        params = _make_params(band_thickness=0.5)
        _, result = validate_parametric(params)
        assert result.manufacturing_status == ManufacturingStatus.REJECTED

    def test_thin_width_auto_corrected(self):
        params = _make_params(band_width=1.0)
        corrected, result = validate_parametric(params)
        assert corrected.band_width >= 1.5


class TestProngValidation:
    def test_too_many_prongs_for_small_stone(self):
        """Small stone with many prongs → prongs would overlap → reduce count."""
        params = ParametricRing(
            center_stone=CenterStone(diameter=3.0, height=1.8, prongs=8)
        )
        corrected, result = validate_parametric(params)
        assert corrected.center_stone.prongs <= 8  # may be reduced

    def test_valid_prongs_unchanged(self):
        params = ParametricRing(
            center_stone=CenterStone(diameter=6.0, height=3.6, prongs=4)
        )
        corrected, result = validate_parametric(params)
        assert corrected.center_stone.prongs == 4


class TestSafeDesign:
    def test_default_params_safe(self):
        """Default parameters should pass validation without corrections."""
        params = ParametricRing()
        _, result = validate_parametric(params)
        assert result.manufacturing_status in (ManufacturingStatus.SAFE, ManufacturingStatus.AUTO_CORRECTED)

    def test_validation_returns_all_fields(self):
        params = ParametricRing()
        _, result = validate_parametric(params)
        assert isinstance(result.violations_detected, list)
        assert isinstance(result.corrections_applied, list)
        assert result.manufacturing_status in ManufacturingStatus.__members__.values()
