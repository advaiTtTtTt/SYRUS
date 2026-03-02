"""POST /api/budget/* — Cost estimation and budget adjustment.

Skill: jewelry-budget-logic
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.schemas.budget_result import BudgetAdjustment, BudgetEstimate, CostBreakdown
from app.schemas.customization import Customization
from app.schemas.parametric import ParametricRing
from app.skills.budget_logic.adjuster import adjust_to_budget
from app.skills.budget_logic.pricer import compute_cost

router = APIRouter(prefix="/api/budget", tags=["budget"])


class BudgetEstimateRequest(BaseModel):
    params: ParametricRing
    customization: Customization = Field(default_factory=Customization)


class BudgetAdjustRequest(BaseModel):
    params: ParametricRing
    customization: Customization = Field(default_factory=Customization)
    target_budget: float = Field(gt=0, description="Target budget in ₹")


@router.post("/estimate", response_model=BudgetEstimate)
async def estimate_cost(req: BudgetEstimateRequest):
    """Compute cost breakdown for a ring configuration.

    Performance target: < 100ms (no geometry generation).
    """
    try:
        breakdown = compute_cost(req.params, req.customization)
    except Exception as e:
        raise HTTPException(500, f"Cost estimation failed: {e}")

    return BudgetEstimate(breakdown=breakdown)


@router.post("/adjust", response_model=BudgetAdjustment)
async def adjust_budget(req: BudgetAdjustRequest):
    """Adjust ring parameters to fit within target budget.

    Applies the strict ordered adjustment sequence from budget-logic SKILL:
      1. Reduce center stone (max 20%)
      2. (Phase 2) Reduce side stone count
      3. Downgrade gemstone type
      4. Downgrade metal purity
      5. (Phase 2) Remove side stones entirely

    Returns modified params + changes log.
    """
    try:
        result = adjust_to_budget(req.params, req.customization, req.target_budget)
    except Exception as e:
        raise HTTPException(500, f"Budget adjustment failed: {e}")

    return result
