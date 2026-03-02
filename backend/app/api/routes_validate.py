"""POST /api/validate — Standalone manufacturability validation.

Skill: manufacturability-validator
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.schemas.parametric import ParametricRing
from app.schemas.validation_result import ValidationResult
from app.skills.manufacturability.validator import validate_parametric

router = APIRouter(prefix="/api", tags=["validate"])


class ValidateRequest(BaseModel):
    params: ParametricRing


class ValidateResponse(BaseModel):
    params_corrected: ParametricRing
    validation: ValidationResult


@router.post("/validate", response_model=ValidateResponse)
async def validate_ring(req: ValidateRequest):
    """Run manufacturability validation on parametric JSON.

    Useful for frontend pre-checks before triggering a full build.
    Does not generate geometry — only checks parameter constraints.
    """
    corrected, result = validate_parametric(req.params)

    return ValidateResponse(
        params_corrected=corrected,
        validation=result,
    )
