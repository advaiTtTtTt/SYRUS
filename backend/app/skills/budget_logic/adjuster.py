"""Budget-aware adjustment engine.

Source of truth: jewelry-budget-logic/SKILL.md

When target_budget is set and cost > budget, apply adjustments in STRICT order:
  1. Reduce center stone carat (max 20% diameter reduction)
  2. Reduce side stone count            (Phase 2 — skipped in MVP)
  3. Downgrade gemstone type
  4. Downgrade metal purity (18k → 14k)
  5. Remove side stones entirely        (Phase 2 — skipped in MVP)

NEVER reduce below manufacturing safety limits.
"""

from __future__ import annotations

from app.schemas.budget_result import BudgetAdjustment
from app.schemas.customization import Customization
from app.schemas.parametric import ParametricRing

from .pricer import compute_cost
from .tables import GEMSTONE_DOWNGRADE, METAL_DOWNGRADE


# Minimum center stone diameter (cannot go below 3.0 mm per parametric SKILL)
_MIN_STONE_DIAMETER = 3.0
# Maximum diameter reduction fraction (20% per budget SKILL)
_MAX_STONE_REDUCTION = 0.20


def adjust_to_budget(
    params: ParametricRing,
    custom: Customization,
    target_budget: float,
) -> BudgetAdjustment:
    """Try to fit the design within target_budget using the ordered adjustment steps."""

    original_cost = compute_cost(params, custom).total_cost
    changes: list[str] = []

    # Work on copies
    adj_params = params.model_copy(deep=True)
    adj_custom = custom.model_copy(deep=True)

    def _current_cost() -> float:
        return compute_cost(adj_params, adj_custom).total_cost

    # ── Hard limit check ───────────────────────────────────────────
    # Build the cheapest possible version to see if budget is feasible at all
    cheapest_custom = custom.model_copy(deep=True)
    cheapest_custom.gemstone_material = GEMSTONE_DOWNGRADE[-1]
    cheapest_custom.metal_type = METAL_DOWNGRADE[-1]
    cheapest_params = params.model_copy(deep=True)
    cheapest_params.center_stone.diameter = _MIN_STONE_DIAMETER
    # Re-validate height ratio
    cheapest_params.center_stone.height = round(cheapest_params.center_stone.diameter * 0.6, 2)
    cheapest_params.side_stones = []
    min_possible = compute_cost(cheapest_params, cheapest_custom).total_cost

    if target_budget < min_possible:
        return BudgetAdjustment(
            original_cost=round(original_cost, 2),
            adjusted_cost=round(min_possible, 2),
            changes_applied=["Budget too low for safe manufacturing."],
            budget_fit=False,
            adjusted_params=adj_params,
        )

    # ── Step 1: Reduce center stone diameter (max 20%) ─────────────
    if _current_cost() > target_budget:
        original_dia = adj_params.center_stone.diameter
        min_dia = max(_MIN_STONE_DIAMETER, original_dia * (1 - _MAX_STONE_REDUCTION))

        # Binary search for smallest diameter that fits
        lo, hi = min_dia, original_dia
        for _ in range(20):  # converge quickly
            mid = (lo + hi) / 2
            adj_params.center_stone.diameter = round(mid, 2)
            adj_params.center_stone.height = round(mid * 0.6, 2)
            if _current_cost() <= target_budget:
                lo = mid
            else:
                hi = mid

        adj_params.center_stone.diameter = round(hi, 2)
        adj_params.center_stone.height = round(hi * 0.6, 2)

        if adj_params.center_stone.diameter < original_dia:
            pct = round((1 - adj_params.center_stone.diameter / original_dia) * 100, 1)
            changes.append(f"Reduced center stone diameter by {pct}% ({original_dia}→{adj_params.center_stone.diameter} mm)")

    # ── Step 2: Reduce side stone count (Phase 2 — skip in MVP) ────

    # ── Step 3: Downgrade gemstone type ────────────────────────────
    if _current_cost() > target_budget:
        current_idx = GEMSTONE_DOWNGRADE.index(adj_custom.gemstone_material)
        for i in range(current_idx + 1, len(GEMSTONE_DOWNGRADE)):
            adj_custom.gemstone_material = GEMSTONE_DOWNGRADE[i]
            changes.append(f"Downgraded gemstone to {adj_custom.gemstone_material.value}")
            if _current_cost() <= target_budget:
                break

    # ── Step 4: Downgrade metal purity ─────────────────────────────
    if _current_cost() > target_budget:
        current_idx = METAL_DOWNGRADE.index(adj_custom.metal_type)
        for i in range(current_idx + 1, len(METAL_DOWNGRADE)):
            adj_custom.metal_type = METAL_DOWNGRADE[i]
            changes.append(f"Downgraded metal to {adj_custom.metal_type.value}")
            if _current_cost() <= target_budget:
                break

    # ── Step 5: Remove side stones (Phase 2 — skip in MVP) ────────

    final_cost = _current_cost()
    return BudgetAdjustment(
        original_cost=round(original_cost, 2),
        adjusted_cost=round(final_cost, 2),
        changes_applied=changes,
        budget_fit=final_cost <= target_budget,
        adjusted_params=adj_params,
    )
