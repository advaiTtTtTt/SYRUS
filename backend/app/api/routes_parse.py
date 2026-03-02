"""POST /api/parse — Upload 2D image & extract parametric JSON.

Skill: jewelry-image-parser
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import settings
from app.schemas.customization import Customization
from app.schemas.parse_result import ParseResult
from app.db.models import create_project

router = APIRouter(prefix="/api", tags=["parse"])


@router.post("/parse", response_model=dict)
async def parse_jewelry_image(file: UploadFile = File(...)):
    """Upload a 2D jewelry image.

    Returns:
      - project_id
      - Parametric JSON extracted from image
      - Confidence scores
    """
    # Validate file type
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(400, "Only JPEG, PNG, or WebP images are accepted")

    # Save upload
    project_id = str(uuid.uuid4())
    ext = Path(file.filename or "image.jpg").suffix or ".jpg"
    upload_path = settings.UPLOADS_DIR / f"{project_id}{ext}"

    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Run image parser pipeline (lazy import to avoid startup crash when cv2 not installed)
    try:
        from app.skills.image_parser.pipeline import parse_image
        result: ParseResult = parse_image(upload_path)
    except ImportError:
        # CV packages not installed — return fallback defaults
        from app.schemas.parametric import ParametricRing
        result = ParseResult(
            params=ParametricRing(),
            confidence_score=0.0,
            band_confidence=0.0,
            stone_confidence=0.0,
            setting_confidence=0.0,
            symmetry_confidence=0.0,
        )
    except Exception as e:
        raise HTTPException(500, f"Image parsing failed: {e}")

    # Create project in DB
    default_custom = Customization()
    await create_project(
        project_id=project_id,
        source_image=str(upload_path),
        parse_result_json=result.model_dump_json(),
        current_params_json=result.params.model_dump_json(),
        customization_json=default_custom.model_dump_json(),
    )

    return {
        "project_id": project_id,
        "parse_result": result.model_dump(),
        "customization": default_custom.model_dump(),
    }
