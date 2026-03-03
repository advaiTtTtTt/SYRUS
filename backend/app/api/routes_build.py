"""POST /api/build — Generate 3D ring from parametric JSON.

Skills: jewelry-parametric-engine + manufacturability-validator
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.schemas.customization import Customization
from app.schemas.parametric import ParametricRing
from app.schemas.validation_result import ManufacturingStatus, ValidationResult
from app.db.models import create_build, update_project

router = APIRouter(prefix="/api", tags=["build"])


class BuildRequest(BaseModel):
    project_id: Optional[str] = None
    params: ParametricRing
    customization: Customization = Field(default_factory=Customization)


class BuildResponse(BaseModel):
    build_id: str
    params_used: ParametricRing
    validation: ValidationResult
    model_glb_url: Optional[str] = None
    model_stl_url: Optional[str] = None


@router.post("/build", response_model=BuildResponse)
async def build_ring(req: BuildRequest):
    """Build a 3D ring model from parametric JSON.

    Runs the full pipeline:
      1. Constraint clamping (parametric-engine)
      2. Manufacturability pre-validation
      3. CadQuery geometry generation
      4. Post-build mesh validation
      5. STL + GLB export

    Returns build_id + model URLs + validation result.
    """
    build_id = str(uuid.uuid4())

    try:
        from app.skills.parametric_engine.engine import build_jewelry as do_build

        result = do_build(
            params=req.params,
            output_dir=settings.EXPORTS_DIR,
            build_id=build_id,
        )
    except ImportError:
        # CadQuery not installed — return a mock response for development
        return BuildResponse(
            build_id=build_id,
            params_used=req.params.clamped(),
            validation=ValidationResult(
                manufacturing_status=ManufacturingStatus.SAFE,
                violations_detected=["CadQuery not installed — mock response"],
                corrections_applied=[],
            ),
            model_glb_url=None,
            model_stl_url=None,
        )
    except Exception as e:
        raise HTTPException(500, f"Build failed: {e}")

    # Determine URLs
    glb_url = f"/api/build/{build_id}/model.glb" if result.glb_path else None
    stl_url = f"/api/build/{build_id}/model.stl" if result.stl_path else None

    # Persist build record
    try:
        await create_build(
            build_id=build_id,
            project_id=req.project_id or "standalone",
            params_json=result.params_used.model_dump_json(),
            validation_json=result.validation.model_dump_json(),
            stl_path=str(result.stl_path) if result.stl_path else None,
            glb_path=str(result.glb_path) if result.glb_path else None,
        )

        if req.project_id:
            await update_project(
                req.project_id,
                latest_build_id=build_id,
                current_params_json=result.params_used.model_dump_json(),
                validation_result_json=result.validation.model_dump_json(),
            )
    except Exception:
        pass  # DB persistence failure is non-fatal

    return BuildResponse(
        build_id=build_id,
        params_used=result.params_used,
        validation=result.validation,
        model_glb_url=glb_url,
        model_stl_url=stl_url,
    )
