"""Tests for jewelry-parametric-engine SKILL constraints.

Uses model_construct() to bypass Pydantic field validators so we can
feed out-of-range values into apply_constraints() and verify clamping.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.schemas.parametric import CenterStone, ParametricRing, StoneShape, SettingType
from app.skills.parametric_engine.constraints import apply_constraints


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
    # Allow overriding center_stone sub-fields via nested dict
    if "center_stone" in overrides and isinstance(overrides["center_stone"], dict):
        cs_defaults = dict(type=StoneShape.ROUND, diameter=6.0, height=3.6, prongs=4)
        cs_defaults.update(overrides.pop("center_stone"))
        overrides["center_stone"] = CenterStone.model_construct(**cs_defaults)
    defaults.update(overrides)
    return ParametricRing.model_construct(**defaults)


class TestConstraintClamping:
    """Verify all SKILL-defined parameter ranges are enforced."""

    def test_ring_radius_clamped_low(self):
        params = _make_params(ring_radius=5.0)
        result = apply_constraints(params)
        assert result.ring_radius == 7.0

    def test_ring_radius_clamped_high(self):
        params = _make_params(ring_radius=15.0)
        result = apply_constraints(params)
        assert result.ring_radius == 12.0

    def test_band_width_clamped(self):
        params = _make_params(band_width=0.5)
        result = apply_constraints(params)
        assert result.band_width == 1.5

    def test_band_thickness_clamped(self):
        params = _make_params(band_thickness=5.0)
        result = apply_constraints(params)
        assert result.band_thickness == 3.5

    def test_stone_diameter_clamped(self):
        params = _make_params(center_stone={"diameter": 1.0, "height": 0.6, "prongs": 4})
        result = apply_constraints(params)
        assert result.center_stone.diameter == 3.0

    def test_stone_height_auto_corrected(self):
        """Height must be 40–70% of diameter."""
        params = _make_params(center_stone={"diameter": 6.0, "height": 1.0, "prongs": 4})
        result = apply_constraints(params)
        # Min height = 6.0 * 0.4 = 2.4
        assert result.center_stone.height >= 2.4

    def test_prong_count_clamped(self):
        params = _make_params(center_stone={"prongs": 12})
        result = apply_constraints(params)
        assert result.center_stone.prongs == 8

    def test_valid_params_unchanged(self):
        params = ParametricRing(
            ring_radius=9.0,
            band_width=2.2,
            band_thickness=1.8,
            center_stone=CenterStone(
                type="round", diameter=6.0, height=3.6, prongs=4
            ),
        )
        result = apply_constraints(params)
        assert result.ring_radius == 9.0
        assert result.band_width == 2.2
        assert result.band_thickness == 1.8
        assert result.center_stone.diameter == 6.0
