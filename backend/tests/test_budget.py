"""Tests for jewelry-budget-logic SKILL pricing engine."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.schemas.customization import Customization, GemstoneMaterial, MetalType
from app.schemas.parametric import CenterStone, ParametricRing
from app.skills.budget_logic.pricer import compute_cost, estimate_carat
from app.skills.budget_logic.adjuster import adjust_to_budget
from app.skills.budget_logic.classifier import setting_complexity_multiplier


class TestCaratEstimation:
    """Verify carat formula: (diameter³ × shape_factor) × 0.0000061"""

    def test_round_6mm(self):
        carat = estimate_carat(6.0, "round")
        # 6³ × 1.0 × 0.0000061 = 216 × 0.0000061 ≈ 0.001318
        assert abs(carat - 0.001318) < 0.0001

    def test_oval_factor(self):
        round_carat = estimate_carat(6.0, "round")
        oval_carat = estimate_carat(6.0, "oval")
        assert oval_carat < round_carat  # oval factor = 0.95


class TestCostComputation:
    def test_basic_gold_diamond_ring(self):
        params = ParametricRing()
        custom = Customization()
        result = compute_cost(params, custom)

        assert result.metal_cost > 0
        assert result.gemstone_cost > 0
        assert result.total_cost > 0
        assert result.total_cost == pytest.approx(
            (result.metal_cost + result.gemstone_cost + result.side_stones_cost) * result.setting_multiplier,
            rel=0.01,
        )

    def test_silver_cheaper_than_gold(self):
        params = ParametricRing()
        gold = compute_cost(params, Customization(metal_type=MetalType.GOLD_18K))
        silver = compute_cost(params, Customization(metal_type=MetalType.SILVER))
        assert silver.metal_cost < gold.metal_cost

    def test_moissanite_cheaper_than_diamond(self):
        params = ParametricRing()
        diamond = compute_cost(params, Customization(gemstone_material=GemstoneMaterial.DIAMOND))
        moissanite = compute_cost(params, Customization(gemstone_material=GemstoneMaterial.MOISSANITE))
        assert moissanite.gemstone_cost < diamond.gemstone_cost


class TestSettingComplexity:
    def test_solitaire(self):
        params = ParametricRing(side_stones=[])
        assert setting_complexity_multiplier(params) == 1.0

    def test_intricate_prongs(self):
        params = ParametricRing(
            center_stone=CenterStone(prongs=7),
            side_stones=[],
        )
        assert setting_complexity_multiplier(params) == pytest.approx(1.1, rel=0.01)


class TestBudgetAdjustment:
    def test_adjustment_reduces_cost(self):
        params = ParametricRing()
        custom = Customization()
        original = compute_cost(params, custom).total_cost

        # Set budget to 50% of original
        result = adjust_to_budget(params, custom, original * 0.5)
        assert result.adjusted_cost <= result.original_cost
        assert len(result.changes_applied) > 0

    def test_impossible_budget_rejected(self):
        params = ParametricRing()
        custom = Customization()
        # Budget of ₹1 — impossible
        result = adjust_to_budget(params, custom, 1.0)
        assert result.budget_fit is False
        assert "Budget too low" in result.changes_applied[0]

    def test_generous_budget_no_changes(self):
        params = ParametricRing()
        custom = Customization()
        original = compute_cost(params, custom).total_cost
        # Budget well above cost
        result = adjust_to_budget(params, custom, original * 10)
        assert result.budget_fit is True
        assert len(result.changes_applied) == 0
