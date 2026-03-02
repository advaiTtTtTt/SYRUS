"""Budget result schemas — pricing & adjustment outputs.

Source of truth: jewelry-budget-logic/SKILL.md
Currency: ₹ (INR)
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .parametric import ParametricRing


class CostBreakdown(BaseModel):
    """Itemised cost estimate."""

    metal_cost: float = Field(description="Metal material cost in ₹")
    gemstone_cost: float = Field(description="Center stone cost in ₹")
    side_stones_cost: float = Field(default=0.0, description="Side stones total cost in ₹")
    setting_multiplier: float = Field(default=1.0, description="Setting complexity multiplier")
    total_cost: float = Field(description="Final total cost in ₹")


class BudgetEstimate(BaseModel):
    """Response for /api/budget/estimate."""

    breakdown: CostBreakdown
    currency: str = "INR"


class BudgetAdjustment(BaseModel):
    """Response for /api/budget/adjust — per SKILL smart suggestion output."""

    original_cost: float
    adjusted_cost: float
    changes_applied: list[str] = Field(default_factory=list)
    budget_fit: bool
    adjusted_params: ParametricRing = Field(
        description="Modified parametric JSON after budget adjustments"
    )
