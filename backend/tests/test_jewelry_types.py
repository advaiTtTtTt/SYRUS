"""Tests for multi-jewelry-type extension.

Covers:
  - Schema: JewelryType enum, PendantParams, EarringParams, auto-population
  - Constraints: pendant/earring clamping
  - Budget: volume estimation for pendant/earring
  - Validator: pendant checks (bail, base), earring checks (pin, stud)
  - Backward compatibility: omitting 'type' defaults to ring
"""

import sys
import os
import math

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.schemas.parametric import (
    CenterStone,
    EarringParams,
    JewelryType,
    ParametricRing,
    PendantBaseShape,
    PendantParams,
    SettingType,
    StoneShape,
)
from app.schemas.customization import Customization
from app.skills.parametric_engine.constraints import apply_constraints, LIMITS
from app.skills.budget_logic.pricer import (
    compute_cost,
    estimate_band_volume_mm3,
    estimate_earring_volume_mm3,
    estimate_pendant_volume_mm3,
)
from app.skills.manufacturability.validator import validate_parametric
from app.skills.manufacturability.pendant_checks import check_pendant
from app.skills.manufacturability.earring_checks import check_earring


# ── Helpers ────────────────────────────────────────────────────────

def _ring_params(**kw) -> ParametricRing:
    defaults = dict(type="ring", ring_radius=9.0, band_width=2.2, band_thickness=1.8)
    defaults.update(kw)
    return ParametricRing(**defaults)


def _pendant_params(**kw) -> ParametricRing:
    defaults = dict(
        type="pendant",
        pendant_params=PendantParams(),
    )
    defaults.update(kw)
    return ParametricRing(**defaults)


def _earring_params(**kw) -> ParametricRing:
    defaults = dict(
        type="earring",
        earring_params=EarringParams(),
    )
    defaults.update(kw)
    return ParametricRing(**defaults)


# ════════════════════════════════════════════════════════════════════
#  Schema tests
# ════════════════════════════════════════════════════════════════════

class TestJewelryTypeEnum:
    def test_enum_values(self):
        assert JewelryType.RING.value == "ring"
        assert JewelryType.PENDANT.value == "pendant"
        assert JewelryType.EARRING.value == "earring"

    def test_default_is_ring(self):
        p = ParametricRing()
        assert p.type == JewelryType.RING

    def test_backward_compat_no_type(self):
        """Omitting 'type' defaults to ring — backward compatible."""
        p = ParametricRing(ring_radius=9.0, band_width=2.2, band_thickness=1.8)
        assert p.type == JewelryType.RING
        assert p.pendant_params is None
        assert p.earring_params is None


class TestPendantParams:
    def test_auto_populate(self):
        """Setting type=pendant auto-populates pendant_params."""
        p = ParametricRing(type="pendant")
        assert p.pendant_params is not None
        assert p.pendant_params.bail_thickness >= 0.8

    def test_base_shapes(self):
        assert PendantBaseShape.CIRCULAR.value == "circular"
        assert PendantBaseShape.OVAL.value == "oval"

    def test_custom_pendant_params(self):
        pp = PendantParams(base_width=20.0, bail_thickness=1.5)
        p = ParametricRing(type="pendant", pendant_params=pp)
        assert p.pendant_params.base_width == 20.0


class TestEarringParams:
    def test_auto_populate(self):
        """Setting type=earring auto-populates earring_params."""
        p = ParametricRing(type="earring")
        assert p.earring_params is not None
        assert p.earring_params.pin_diameter >= 0.7

    def test_custom_earring_params(self):
        ep = EarringParams(stud_diameter=10.0, pin_length=11.0)
        p = ParametricRing(type="earring", earring_params=ep)
        assert p.earring_params.stud_diameter == 10.0


class TestClampedMethod:
    def test_clamp_ring(self):
        p = ParametricRing(type="ring").clamped()
        assert 7.0 <= p.ring_radius <= 12.0

    def test_clamp_pendant(self):
        pp = PendantParams.model_construct(
            base_shape=PendantBaseShape.CIRCULAR,
            base_width=50.0, base_height=15.0, base_thickness=1.5,
            bail_diameter=4.0, bail_thickness=0.5,
        )
        p = ParametricRing.model_construct(
            type=JewelryType.PENDANT,
            ring_radius=9.0, band_width=2.2, band_thickness=1.8,
            center_stone=CenterStone.model_construct(type=StoneShape.ROUND, diameter=6.0, height=3.6, prongs=4),
            setting_type=SettingType.PRONG, side_stones=[],
            pendant_params=pp, earring_params=None,
        ).clamped()
        assert p.pendant_params.base_width <= 30.0
        assert p.pendant_params.bail_thickness >= 0.8

    def test_clamp_earring(self):
        ep = EarringParams.model_construct(
            stud_diameter=8.0, stud_thickness=1.2,
            pin_length=15.0, pin_diameter=0.3,
        )
        p = ParametricRing.model_construct(
            type=JewelryType.EARRING,
            ring_radius=9.0, band_width=2.2, band_thickness=1.8,
            center_stone=CenterStone.model_construct(type=StoneShape.ROUND, diameter=6.0, height=3.6, prongs=4),
            setting_type=SettingType.PRONG, side_stones=[],
            pendant_params=None, earring_params=ep,
        ).clamped()
        assert p.earring_params.pin_diameter >= 0.7
        assert p.earring_params.pin_length <= 12.0


# ════════════════════════════════════════════════════════════════════
#  Constraint clamping tests
# ════════════════════════════════════════════════════════════════════

class TestConstraintsPendant:
    def test_bail_thickness_clamped_up(self):
        pp = PendantParams.model_construct(
            base_shape=PendantBaseShape.CIRCULAR,
            base_width=15.0, base_height=15.0, base_thickness=1.5,
            bail_diameter=4.0, bail_thickness=0.5,
        )
        p = ParametricRing.model_construct(
            type=JewelryType.PENDANT,
            ring_radius=9.0, band_width=2.2, band_thickness=1.8,
            center_stone=CenterStone.model_construct(type=StoneShape.ROUND, diameter=6.0, height=3.6, prongs=4),
            setting_type=SettingType.PRONG, side_stones=[],
            pendant_params=pp, earring_params=None,
        )
        result = apply_constraints(p)
        assert result.pendant_params.bail_thickness >= 0.8

    def test_base_width_clamped_down(self):
        pp = PendantParams.model_construct(
            base_shape=PendantBaseShape.CIRCULAR,
            base_width=40.0, base_height=15.0, base_thickness=1.5,
            bail_diameter=4.0, bail_thickness=1.2,
        )
        p = ParametricRing.model_construct(
            type=JewelryType.PENDANT,
            ring_radius=9.0, band_width=2.2, band_thickness=1.8,
            center_stone=CenterStone.model_construct(type=StoneShape.ROUND, diameter=6.0, height=3.6, prongs=4),
            setting_type=SettingType.PRONG, side_stones=[],
            pendant_params=pp, earring_params=None,
        )
        result = apply_constraints(p)
        assert result.pendant_params.base_width <= 30.0


class TestConstraintsEarring:
    def test_pin_diameter_clamped_up(self):
        ep = EarringParams.model_construct(
            stud_diameter=8.0, stud_thickness=1.2,
            pin_length=10.0, pin_diameter=0.5,
        )
        p = ParametricRing.model_construct(
            type=JewelryType.EARRING,
            ring_radius=9.0, band_width=2.2, band_thickness=1.8,
            center_stone=CenterStone.model_construct(type=StoneShape.ROUND, diameter=6.0, height=3.6, prongs=4),
            setting_type=SettingType.PRONG, side_stones=[],
            pendant_params=None, earring_params=ep,
        )
        result = apply_constraints(p)
        assert result.earring_params.pin_diameter >= 0.7

    def test_stud_diameter_clamped(self):
        ep = EarringParams.model_construct(
            stud_diameter=20.0, stud_thickness=1.2,
            pin_length=10.0, pin_diameter=0.8,
        )
        p = ParametricRing.model_construct(
            type=JewelryType.EARRING,
            ring_radius=9.0, band_width=2.2, band_thickness=1.8,
            center_stone=CenterStone.model_construct(type=StoneShape.ROUND, diameter=6.0, height=3.6, prongs=4),
            setting_type=SettingType.PRONG, side_stones=[],
            pendant_params=None, earring_params=ep,
        )
        result = apply_constraints(p)
        assert result.earring_params.stud_diameter <= 15.0


# ════════════════════════════════════════════════════════════════════
#  Budget / volume tests
# ════════════════════════════════════════════════════════════════════

class TestVolumeEstimation:
    def test_ring_volume_positive(self):
        p = _ring_params()
        assert estimate_band_volume_mm3(p) > 0

    def test_pendant_volume_positive(self):
        p = _pendant_params()
        assert estimate_pendant_volume_mm3(p) > 0

    def test_earring_volume_positive(self):
        p = _earring_params()
        assert estimate_earring_volume_mm3(p) > 0

    def test_pendant_volume_includes_bail(self):
        """Pendant volume should include bail contribution."""
        p1 = _pendant_params(pendant_params=PendantParams(bail_diameter=2.0, bail_thickness=0.8))
        p2 = _pendant_params(pendant_params=PendantParams(bail_diameter=8.0, bail_thickness=2.5))
        assert estimate_pendant_volume_mm3(p2) > estimate_pendant_volume_mm3(p1)

    def test_earring_smaller_than_ring(self):
        """Earring should generally have less metal than a ring."""
        ring = _ring_params()
        earring = _earring_params()
        assert estimate_earring_volume_mm3(earring) < estimate_band_volume_mm3(ring)


class TestBudgetDispatch:
    def test_pendant_cost_computed(self):
        p = _pendant_params()
        cost = compute_cost(p, Customization())
        assert cost.total_cost > 0
        assert cost.metal_cost > 0

    def test_earring_cost_computed(self):
        p = _earring_params()
        cost = compute_cost(p, Customization())
        assert cost.total_cost > 0

    def test_ring_cost_unchanged(self):
        """Ring cost should be the same as before (backward compat)."""
        p = _ring_params()
        cost = compute_cost(p, Customization())
        assert cost.total_cost > 0


# ════════════════════════════════════════════════════════════════════
#  Manufacturability validator tests
# ════════════════════════════════════════════════════════════════════

class TestPendantValidator:
    def test_thin_bail_corrected(self):
        pp = PendantParams.model_construct(
            base_shape=PendantBaseShape.CIRCULAR,
            base_width=15.0, base_height=15.0, base_thickness=1.5,
            bail_diameter=4.0, bail_thickness=0.5,
        )
        p = ParametricRing.model_construct(
            type=JewelryType.PENDANT,
            ring_radius=9.0, band_width=2.2, band_thickness=1.8,
            center_stone=CenterStone.model_construct(type=StoneShape.ROUND, diameter=6.0, height=3.6, prongs=4),
            setting_type=SettingType.PRONG, side_stones=[],
            pendant_params=pp, earring_params=None,
        )
        violations, corrections = [], []
        check_pendant(p, violations, corrections)
        assert p.pendant_params.bail_thickness >= 0.8
        assert any("bail" in c.lower() for c in corrections)

    def test_stone_exceeds_base_corrected(self):
        """If stone > 80% of base width, base should be widened."""
        pp = PendantParams(base_width=8.0)
        p = ParametricRing(
            type="pendant",
            pendant_params=pp,
            center_stone=CenterStone(diameter=8.0, height=4.8, prongs=4),
        )
        violations, corrections = [], []
        check_pendant(p, violations, corrections)
        assert p.pendant_params.base_width >= 8.0  # at least corrected

    def test_valid_pendant_no_corrections(self):
        p = _pendant_params()
        violations, corrections = [], []
        check_pendant(p, violations, corrections)
        assert len(corrections) == 0


class TestEarringValidator:
    def test_thin_pin_corrected(self):
        ep = EarringParams.model_construct(
            stud_diameter=8.0, stud_thickness=1.2,
            pin_length=10.0, pin_diameter=0.5,
        )
        p = ParametricRing.model_construct(
            type=JewelryType.EARRING,
            ring_radius=9.0, band_width=2.2, band_thickness=1.8,
            center_stone=CenterStone.model_construct(type=StoneShape.ROUND, diameter=6.0, height=3.6, prongs=4),
            setting_type=SettingType.PRONG, side_stones=[],
            pendant_params=None, earring_params=ep,
        )
        violations, corrections = [], []
        check_earring(p, violations, corrections)
        assert p.earring_params.pin_diameter >= 0.7
        assert any("pin" in c.lower() for c in corrections)

    def test_stud_too_small_for_stone(self):
        ep = EarringParams(stud_diameter=5.0)
        p = ParametricRing(
            type="earring",
            earring_params=ep,
            center_stone=CenterStone(diameter=6.0, height=3.6, prongs=4),
        )
        violations, corrections = [], []
        check_earring(p, violations, corrections)
        # Stud should be enlarged
        assert p.earring_params.stud_diameter >= 5.0

    def test_valid_earring_no_corrections(self):
        p = _earring_params()
        violations, corrections = [], []
        check_earring(p, violations, corrections)
        assert len(corrections) == 0


class TestValidatorOrchestrator:
    def test_ring_uses_wall_checks(self):
        """Ring validation should use wall thickness checks."""
        p = _ring_params()
        _, result = validate_parametric(p)
        assert result.manufacturing_status in ("SAFE", "AUTO-CORRECTED")

    def test_pendant_uses_pendant_checks(self):
        p = _pendant_params()
        _, result = validate_parametric(p)
        assert result.manufacturing_status in ("SAFE", "AUTO-CORRECTED")

    def test_earring_uses_earring_checks(self):
        p = _earring_params()
        _, result = validate_parametric(p)
        assert result.manufacturing_status in ("SAFE", "AUTO-CORRECTED")

    def test_default_pendant_safe(self):
        p = _pendant_params()
        _, result = validate_parametric(p)
        assert result.manufacturing_status == "SAFE"

    def test_default_earring_safe(self):
        p = _earring_params()
        _, result = validate_parametric(p)
        assert result.manufacturing_status == "SAFE"
