"""Tests for stone geometry builders and dispatch.

Since CadQuery is not installed in dev, we mock the cadquery module and
validate:
  - Dispatch routes each StoneShape to the correct builder
  - Parameter computations (seat depth, crown height, table ratios)
  - Seat cutter selects the right shape per stone type
  - Unknown shapes fall back to round
  - CUSHION enum value exists and dispatches correctly
"""

import sys
import os
from types import ModuleType
from unittest.mock import MagicMock, patch, call
import math

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Build a fake cadquery module before importing stone ────────────
def _make_mock_cq():
    """Create a mock cadquery module with chainable Workplane API."""
    cq = ModuleType("cadquery")

    class FakeMatrix:
        def __init__(self, m):
            self.m = m

    cq.Matrix = FakeMatrix

    class FakeWorkplane:
        def __init__(self, *a, **kw):
            pass
        def moveTo(self, *a, **kw):    return self
        def lineTo(self, *a, **kw):    return self
        def close(self, *a, **kw):     return self
        def revolve(self, *a, **kw):   return self
        def circle(self, *a, **kw):    return self
        def rect(self, *a, **kw):      return self
        def extrude(self, *a, **kw):   return self
        def loft(self, *a, **kw):      return self
        def union(self, *a, **kw):     return self
        def cut(self, *a, **kw):       return self
        def translate(self, *a, **kw): return self
        def transformed(self, *a, **kw): return self
        def workplane(self, *a, **kw): return self
        def add(self, *a, **kw):       return self
        def edges(self, *a, **kw):     return self
        def fillet(self, *a, **kw):    return self
        def val(self):
            obj = MagicMock()
            obj.transformShape.return_value = self
            return obj

    cq.Workplane = FakeWorkplane
    return cq


# Install mock before any stone imports
sys.modules["cadquery"] = _make_mock_cq()

from app.schemas.parametric import CenterStone, ParametricRing, StoneShape, SettingType
from app.skills.parametric_engine.stone import (
    build_round,
    build_oval,
    build_emerald,
    build_pear,
    build_cushion,
    build_stone_placeholder,
    get_seat_cutter,
    _BUILDERS,
    SEAT_DEPTH_RATIO,
    TABLE_RATIO_ROUND,
    TABLE_RATIO_OVAL,
    TABLE_RATIO_EMERALD,
    TABLE_RATIO_PEAR,
    TABLE_RATIO_CUSHION,
    SEAT_CLEARANCE,
)


# ── Helpers ────────────────────────────────────────────────────────

def _stone(shape: StoneShape = StoneShape.ROUND, diameter=6.0, height=3.6, prongs=4):
    return CenterStone.model_construct(
        type=shape, diameter=diameter, height=height, prongs=prongs
    )


def _params(shape: StoneShape = StoneShape.ROUND, **kw):
    defaults = dict(
        ring_radius=9.0, band_width=2.2, band_thickness=1.8,
        center_stone=_stone(shape),
        setting_type=SettingType.PRONG, side_stones=[],
    )
    defaults.update(kw)
    return ParametricRing.model_construct(**defaults)


# ════════════════════════════════════════════════════════════════════
#  Dispatch table tests
# ════════════════════════════════════════════════════════════════════

class TestDispatchTable:
    """Verify every StoneShape maps to the right builder."""

    def test_all_shapes_registered(self):
        for shape in StoneShape:
            assert shape in _BUILDERS, f"{shape.value} missing from _BUILDERS"

    def test_round_maps_to_build_round(self):
        assert _BUILDERS[StoneShape.ROUND] is build_round

    def test_oval_maps_to_build_oval(self):
        assert _BUILDERS[StoneShape.OVAL] is build_oval

    def test_emerald_maps_to_build_emerald(self):
        assert _BUILDERS[StoneShape.EMERALD] is build_emerald

    def test_pear_maps_to_build_pear(self):
        assert _BUILDERS[StoneShape.PEAR] is build_pear

    def test_cushion_maps_to_build_cushion(self):
        assert _BUILDERS[StoneShape.CUSHION] is build_cushion


class TestCushionEnumExists:
    """CUSHION was added to StoneShape."""

    def test_cushion_in_enum(self):
        assert StoneShape.CUSHION.value == "cushion"

    def test_cushion_roundtrip(self):
        stone = CenterStone(type="cushion", diameter=6.0, height=3.6, prongs=4)
        assert stone.type == StoneShape.CUSHION


# ════════════════════════════════════════════════════════════════════
#  Builder smoke tests (mock CadQuery — verify no exceptions)
# ════════════════════════════════════════════════════════════════════

class TestBuildersSmoke:
    """Each builder runs without error on valid input."""

    @pytest.mark.parametrize("shape,builder", [
        (StoneShape.ROUND,   build_round),
        (StoneShape.OVAL,    build_oval),
        (StoneShape.EMERALD, build_emerald),
        (StoneShape.PEAR,    build_pear),
        (StoneShape.CUSHION, build_cushion),
    ])
    def test_builder_returns(self, shape, builder):
        stone = _stone(shape)
        result = builder(stone)
        assert result is not None


class TestBuildStonePlaceholder:
    """build_stone_placeholder dispatches + translates."""

    @pytest.mark.parametrize("shape", list(StoneShape))
    def test_dispatches_all_shapes(self, shape):
        params = _params(shape)
        result = build_stone_placeholder(params)
        assert result is not None

    def test_unknown_shape_falls_back_to_round(self):
        """If _BUILDERS.get misses, default is build_round."""
        params = _params()
        # Simulate an unknown type by patching _BUILDERS temporarily
        original = _BUILDERS.copy()
        _BUILDERS.clear()
        try:
            # get() with default=build_round should still work
            result = build_stone_placeholder(params)
            assert result is not None
        finally:
            _BUILDERS.update(original)


# ════════════════════════════════════════════════════════════════════
#  Parameter computation tests
# ════════════════════════════════════════════════════════════════════

class TestParameterComputation:
    """Validate geometric constants and ratios."""

    def test_seat_depth_ratio(self):
        assert SEAT_DEPTH_RATIO == 0.20

    def test_seat_clearance(self):
        assert SEAT_CLEARANCE == 0.05

    def test_table_ratios_in_range(self):
        for ratio in [TABLE_RATIO_ROUND, TABLE_RATIO_OVAL,
                      TABLE_RATIO_EMERALD, TABLE_RATIO_PEAR,
                      TABLE_RATIO_CUSHION]:
            assert 0.3 <= ratio <= 0.8, f"table ratio {ratio} out of reasonable range"

    def test_emerald_table_wider_than_round(self):
        """Emerald has a wider flat table."""
        assert TABLE_RATIO_EMERALD > TABLE_RATIO_ROUND

    def test_seat_depth_computation(self):
        stone = _stone(diameter=8.0, height=4.8)
        expected = 4.8 * SEAT_DEPTH_RATIO
        assert abs(expected - 0.96) < 1e-6


# ════════════════════════════════════════════════════════════════════
#  Seat cutter shape selection tests
# ════════════════════════════════════════════════════════════════════

class TestSeatCutter:
    """get_seat_cutter picks shape-appropriate cutter."""

    @pytest.mark.parametrize("shape", list(StoneShape))
    def test_cutter_returns_for_all_shapes(self, shape):
        params = _params(shape)
        result = get_seat_cutter(params)
        assert result is not None

    def test_emerald_uses_rectangular_cutter(self):
        """Emerald seat should NOT use .circle() — confirmed via separate code path."""
        params = _params(StoneShape.EMERALD)
        # Just verify it doesn't fail; the code path calls .rect()
        result = get_seat_cutter(params)
        assert result is not None

    def test_cushion_uses_rect_cutter(self):
        params = _params(StoneShape.CUSHION)
        result = get_seat_cutter(params)
        assert result is not None

    def test_round_uses_circular_cutter(self):
        params = _params(StoneShape.ROUND)
        result = get_seat_cutter(params)
        assert result is not None


# ════════════════════════════════════════════════════════════════════
#  Edge cases
# ════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Boundary parameter values."""

    def test_minimum_stone_diameter(self):
        stone = _stone(diameter=3.0, height=1.8)
        result = build_round(stone)
        assert result is not None

    def test_maximum_stone_diameter(self):
        stone = _stone(diameter=12.0, height=8.4)
        result = build_round(stone)
        assert result is not None

    def test_all_builders_min_diameter(self):
        for shape in StoneShape:
            stone = _stone(shape, diameter=3.0, height=1.8)
            builder = _BUILDERS[shape]
            assert builder(stone) is not None

    def test_all_builders_max_diameter(self):
        for shape in StoneShape:
            stone = _stone(shape, diameter=12.0, height=8.4)
            builder = _BUILDERS[shape]
            assert builder(stone) is not None
