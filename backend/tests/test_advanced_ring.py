"""Tests for advanced ring intelligence (Steps 1–7).

Covers:
  - Schema extensions (SettingStyle, SideStoneLayout)
  - Pavé shoulder generator math
  - Halo layout generator math
  - Cathedral support builder
  - Stone realism constants
  - Budget logic (volume delta, classifier multiplier, layout gem pricing)
  - Validator checks (pavé seat depth, halo spacing, cathedral thickness)
"""

import sys
import os
import math
from types import ModuleType
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Mock cadquery before any engine imports ────────────────────────
def _make_mock_cq():
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
        def sphere(self, *a, **kw):    return self
        def spline(self, *a, **kw):    return self
        def sweep(self, *a, **kw):     return self
        def val(self):
            obj = MagicMock()
            obj.transformShape.return_value = self
            return obj

    cq.Workplane = FakeWorkplane
    return cq


sys.modules["cadquery"] = _make_mock_cq()


from app.schemas.parametric import (
    CenterStone,
    ParametricRing,
    SettingStyle,
    SettingType,
    SideStoneLayout,
    SideStonePattern,
    StoneShape,
)
from app.skills.parametric_engine.constraints import LIMITS, apply_constraints
from app.skills.parametric_engine.pave import (
    MIN_SPACING_MM as PAVE_MIN_SPACING,
    _angular_pitch,
    _max_stones_per_shoulder,
    build_pave_shoulder,
)
from app.skills.parametric_engine.halo import (
    _auto_count,
    build_halo,
)
from app.skills.parametric_engine.cathedral import build_cathedral_supports
from app.skills.parametric_engine.stone import (
    GIRDLE_THICKNESS_RATIO,
    CROWN_BREAK_RATIO,
    PAVILION_BREAK_RATIO,
)
from app.skills.budget_logic.classifier import setting_complexity_multiplier
from app.skills.budget_logic.pricer import (
    _ring_setting_volume_delta,
    _estimate_metal_volume,
    estimate_band_volume_mm3,
)
from app.skills.manufacturability.setting_checks import (
    check_ring_setting,
    CATHEDRAL_MIN_THICKNESS,
    MIN_STONE_SPACING,
)
from app.skills.manufacturability.validator import validate_parametric


# ── Helpers ────────────────────────────────────────────────────────

def _ring(**kw):
    """Build a ring ParametricRing with optional overrides."""
    defaults = dict(
        type="ring",
        ring_radius=9.0,
        band_width=2.2,
        band_thickness=1.8,
        center_stone=CenterStone(type="round", diameter=6.0, height=3.6, prongs=4),
        setting_type=SettingType.PRONG,
        setting_style=SettingStyle.SOLITAIRE,
        side_stones=[],
    )
    defaults.update(kw)
    return ParametricRing.model_construct(**defaults)


def _layout(**kw):
    """Build a SideStoneLayout with overrides."""
    defaults = dict(enabled=True, pattern=SideStonePattern.PAVE, count=0,
                    diameter=1.5, rows=1)
    defaults.update(kw)
    return SideStoneLayout.model_construct(**defaults)


# ════════════════════════════════════════════════════════════════════
#  STEP 1 — Schema extension tests
# ════════════════════════════════════════════════════════════════════

class TestSettingStyleEnum:
    def test_all_values(self):
        assert SettingStyle.SOLITAIRE.value == "solitaire"
        assert SettingStyle.PAVE_SHOULDER.value == "pave_shoulder"
        assert SettingStyle.HALO.value == "halo"
        assert SettingStyle.CATHEDRAL.value == "cathedral"

    def test_default_is_solitaire(self):
        p = ParametricRing()
        assert p.setting_style == SettingStyle.SOLITAIRE

    def test_side_stone_layout_none_by_default(self):
        p = ParametricRing()
        assert p.side_stone_layout is None


class TestSideStoneLayout:
    def test_defaults(self):
        ssl = SideStoneLayout()
        assert ssl.enabled is False
        assert ssl.pattern == SideStonePattern.PAVE
        assert ssl.count == 0
        assert ssl.diameter == 1.5
        assert ssl.rows == 1

    def test_clamp_in_parametric(self):
        """clamped() clamps layout values."""
        p = ParametricRing.model_construct(
            type="ring", ring_radius=9.0, band_width=2.2, band_thickness=1.8,
            center_stone=CenterStone.model_construct(
                type=StoneShape.ROUND, diameter=6.0, height=3.6, prongs=4),
            setting_type=SettingType.PRONG,
            setting_style=SettingStyle.PAVE_SHOULDER,
            side_stones=[],
            side_stone_layout=SideStoneLayout.model_construct(
                enabled=True, pattern=SideStonePattern.PAVE,
                count=999, diameter=0.1, rows=10),
        )
        c = p.clamped()
        assert c.side_stone_layout.count <= 60
        assert c.side_stone_layout.diameter >= 1.0
        assert c.side_stone_layout.rows <= 3


class TestConstraintsLimits:
    def test_ssl_limits_in_dict(self):
        assert "ssl_count" in LIMITS
        assert "ssl_diameter" in LIMITS
        assert "ssl_rows" in LIMITS

    def test_ssl_clamping(self):
        p = _ring(
            setting_style=SettingStyle.PAVE_SHOULDER,
            side_stone_layout=_layout(count=999, diameter=0.5, rows=10),
        )
        result = apply_constraints(p)
        ssl = result.side_stone_layout
        assert ssl.count == 60
        assert ssl.diameter == 1.0
        assert ssl.rows == 3


# ════════════════════════════════════════════════════════════════════
#  STEP 2 — Pavé shoulder tests
# ════════════════════════════════════════════════════════════════════

class TestPaveAngularPitch:
    def test_pitch_decreases_with_larger_radius(self):
        p1 = _angular_pitch(1.5, 0.3, 10.0)
        p2 = _angular_pitch(1.5, 0.3, 20.0)
        assert p2 < p1

    def test_pitch_increases_with_larger_stone(self):
        p1 = _angular_pitch(1.0, 0.3, 10.0)
        p2 = _angular_pitch(2.0, 0.3, 10.0)
        assert p2 > p1


class TestPaveMaxStones:
    def test_returns_nonneg(self):
        n = _max_stones_per_shoulder(1.5, 0.3, 10.0)
        assert n >= 0

    def test_more_room_with_smaller_stones(self):
        n1 = _max_stones_per_shoulder(2.0, 0.3, 10.0)
        n2 = _max_stones_per_shoulder(1.0, 0.3, 10.0)
        assert n2 > n1


class TestPaveBuild:
    def test_disabled_returns_zero(self):
        p = _ring(side_stone_layout=_layout(enabled=False))
        result = build_pave_shoulder(p)
        assert result.stone_count == 0

    def test_none_layout_returns_zero(self):
        p = _ring()
        result = build_pave_shoulder(p)
        assert result.stone_count == 0

    def test_enabled_returns_stones(self):
        p = _ring(
            setting_style=SettingStyle.PAVE_SHOULDER,
            side_stone_layout=_layout(enabled=True, diameter=1.5, rows=1),
        )
        result = build_pave_shoulder(p)
        assert result.stone_count > 0

    def test_stones_are_even_bilateral(self):
        """Stone count should be even (symmetric shoulders)."""
        p = _ring(
            setting_style=SettingStyle.PAVE_SHOULDER,
            side_stone_layout=_layout(enabled=True, diameter=1.5, rows=1),
        )
        result = build_pave_shoulder(p)
        assert result.stone_count % 2 == 0

    def test_multi_row_more_stones(self):
        p1 = _ring(side_stone_layout=_layout(rows=1))
        p2 = _ring(side_stone_layout=_layout(rows=2))
        r1 = build_pave_shoulder(p1)
        r2 = build_pave_shoulder(p2)
        assert r2.stone_count >= r1.stone_count


# ════════════════════════════════════════════════════════════════════
#  STEP 3 — Halo layout tests
# ════════════════════════════════════════════════════════════════════

class TestHaloAutoCount:
    def test_count_positive_for_reasonable_radius(self):
        n = _auto_count(4.0, 1.5, 0.3)
        assert n > 0

    def test_smaller_stones_more_count(self):
        n1 = _auto_count(4.0, 2.0, 0.3)
        n2 = _auto_count(4.0, 1.0, 0.3)
        assert n2 > n1


class TestHaloBuild:
    def test_disabled_returns_zero(self):
        p = _ring(side_stone_layout=_layout(enabled=False, pattern=SideStonePattern.HALO))
        result = build_halo(p)
        assert result.stone_count == 0

    def test_enabled_returns_stones(self):
        p = _ring(
            setting_style=SettingStyle.HALO,
            side_stone_layout=_layout(enabled=True, pattern=SideStonePattern.HALO,
                                      diameter=1.5),
        )
        result = build_halo(p)
        assert result.stone_count >= 3

    def test_stone_count_scales_with_center(self):
        """Larger center stone → more halo stones."""
        p_small = _ring(
            center_stone=CenterStone.model_construct(
                type=StoneShape.ROUND, diameter=4.0, height=2.4, prongs=4),
            side_stone_layout=_layout(pattern=SideStonePattern.HALO, diameter=1.0),
        )
        p_large = _ring(
            center_stone=CenterStone.model_construct(
                type=StoneShape.ROUND, diameter=10.0, height=6.0, prongs=4),
            side_stone_layout=_layout(pattern=SideStonePattern.HALO, diameter=1.0),
        )
        r_small = build_halo(p_small)
        r_large = build_halo(p_large)
        assert r_large.stone_count > r_small.stone_count


# ════════════════════════════════════════════════════════════════════
#  STEP 4 — Cathedral support tests
# ════════════════════════════════════════════════════════════════════

class TestCathedralBuild:
    def test_returns_result(self):
        p = _ring(setting_style=SettingStyle.CATHEDRAL)
        result = build_cathedral_supports(p)
        assert result.supports is not None


# ════════════════════════════════════════════════════════════════════
#  STEP 5 — Stone realism constants
# ════════════════════════════════════════════════════════════════════

class TestStoneRealismConstants:
    def test_girdle_thickness_ratio(self):
        assert GIRDLE_THICKNESS_RATIO == 0.03

    def test_crown_break_ratio(self):
        assert CROWN_BREAK_RATIO == 0.55

    def test_pavilion_break_ratio(self):
        assert PAVILION_BREAK_RATIO == 0.60


# ════════════════════════════════════════════════════════════════════
#  STEP 6 — Budget logic tests
# ════════════════════════════════════════════════════════════════════

class TestClassifierMultiplier:
    def test_solitaire(self):
        p = _ring(setting_style=SettingStyle.SOLITAIRE)
        assert setting_complexity_multiplier(p) == 1.0

    def test_pave_shoulder(self):
        p = _ring(setting_style=SettingStyle.PAVE_SHOULDER)
        assert setting_complexity_multiplier(p) == 1.15

    def test_halo(self):
        p = _ring(setting_style=SettingStyle.HALO)
        assert setting_complexity_multiplier(p) == 1.2

    def test_cathedral(self):
        p = _ring(setting_style=SettingStyle.CATHEDRAL)
        assert setting_complexity_multiplier(p) == 1.1

    def test_intricate_prong_addon(self):
        p = _ring(
            setting_style=SettingStyle.PAVE_SHOULDER,
            center_stone=CenterStone.model_construct(
                type=StoneShape.ROUND, diameter=6.0, height=3.6, prongs=7),
        )
        m = setting_complexity_multiplier(p)
        assert m == pytest.approx(1.15 * 1.1, rel=0.01)


class TestVolumeDeltas:
    def test_solitaire_no_delta(self):
        p = _ring(setting_style=SettingStyle.SOLITAIRE)
        delta = _ring_setting_volume_delta(p)
        assert delta == 0.0

    def test_halo_adds_plate(self):
        p = _ring(setting_style=SettingStyle.HALO)
        delta = _ring_setting_volume_delta(p)
        assert delta > 0  # plate addition > 0 (no seat cuts without layout)

    def test_cathedral_adds_volume(self):
        p = _ring(setting_style=SettingStyle.CATHEDRAL)
        delta = _ring_setting_volume_delta(p)
        assert delta > 0

    def test_pave_with_layout_subtracts_seats(self):
        p = _ring(
            setting_style=SettingStyle.PAVE_SHOULDER,
            side_stone_layout=_layout(enabled=True, count=20, diameter=1.5),
        )
        delta = _ring_setting_volume_delta(p)
        assert delta < 0  # seat cuts remove metal

    def test_ring_volume_includes_delta(self):
        p_plain = _ring()
        p_cathedral = _ring(setting_style=SettingStyle.CATHEDRAL)
        v_plain = _estimate_metal_volume(p_plain)
        v_cathedral = _estimate_metal_volume(p_cathedral)
        assert v_cathedral > v_plain


# ════════════════════════════════════════════════════════════════════
#  STEP 7 — Validator checks
# ════════════════════════════════════════════════════════════════════

class TestPaveValidation:
    def test_seat_depth_autocorrect(self):
        """Stone too large for thin band → diameter reduced."""
        p = _ring(
            band_thickness=1.5,
            setting_style=SettingStyle.PAVE_SHOULDER,
            side_stone_layout=_layout(enabled=True, diameter=4.0),
        )
        v, c = [], []
        check_ring_setting(p, v, c)
        assert any("Pavé stone diameter" in x for x in c)
        assert p.side_stone_layout.diameter < 4.0

    def test_pave_count_clamped(self):
        """Too many stones for arc → count reduced."""
        p = _ring(
            setting_style=SettingStyle.PAVE_SHOULDER,
            side_stone_layout=_layout(enabled=True, count=200, diameter=1.5),
        )
        v, c = [], []
        check_ring_setting(p, v, c)
        assert p.side_stone_layout.count < 200


class TestHaloValidation:
    def test_count_clamped_to_max(self):
        p = _ring(
            setting_style=SettingStyle.HALO,
            side_stone_layout=_layout(enabled=True, pattern=SideStonePattern.HALO,
                                      count=200, diameter=1.5),
        )
        v, c = [], []
        check_ring_setting(p, v, c)
        assert p.side_stone_layout.count < 200

    def test_impossible_halo_flagged(self):
        """Tiny center stone + huge halo stones → violation."""
        p = _ring(
            center_stone=CenterStone.model_construct(
                type=StoneShape.ROUND, diameter=3.0, height=1.8, prongs=4),
            setting_style=SettingStyle.HALO,
            side_stone_layout=_layout(enabled=True, pattern=SideStonePattern.HALO,
                                      diameter=4.0),
        )
        v, c = [], []
        check_ring_setting(p, v, c)
        # Should either flag a violation or auto-correct the diameter
        assert len(v) > 0 or len(c) > 0


class TestCathedralValidation:
    def test_thin_band_autocorrected(self):
        """Band too thin for cathedral → band_thickness increased."""
        p = _ring(
            band_thickness=1.8,
            setting_style=SettingStyle.CATHEDRAL,
        )
        v, c = [], []
        check_ring_setting(p, v, c)
        # 1.8 × 0.4 = 0.72 < 1.2 → should increase
        assert any("band_thickness" in x for x in c)
        assert p.band_thickness >= CATHEDRAL_MIN_THICKNESS / 0.4


class TestValidatorOrchestrator:
    def test_solitaire_default_safe(self):
        """Default solitaire ring passes all checks."""
        p = ParametricRing()
        _, result = validate_parametric(p)
        assert result.manufacturing_status.value in ("SAFE", "AUTO-CORRECTED")

    def test_pave_ring_passes(self):
        """Pavé ring with valid layout passes."""
        p = _ring(
            setting_style=SettingStyle.PAVE_SHOULDER,
            side_stone_layout=_layout(enabled=True, diameter=1.5, count=10),
        )
        _, result = validate_parametric(p)
        assert result.manufacturing_status.value != "REJECTED"

    def test_halo_ring_passes(self):
        """Halo ring with valid layout passes."""
        p = _ring(
            setting_style=SettingStyle.HALO,
            side_stone_layout=_layout(enabled=True, pattern=SideStonePattern.HALO,
                                      diameter=1.5, count=10),
        )
        _, result = validate_parametric(p)
        assert result.manufacturing_status.value != "REJECTED"

    def test_cathedral_ring_passes(self):
        """Cathedral ring with adequate band passes."""
        p = _ring(
            band_thickness=3.5,
            setting_style=SettingStyle.CATHEDRAL,
        )
        _, result = validate_parametric(p)
        assert result.manufacturing_status.value != "REJECTED"
