"""GET /api/export/{build_id}/{format} — Serve exported model files.
GET /api/build/{build_id}/model.glb — Serve GLB model.
GET /api/build/{build_id}/model.stl — Serve STL model.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import settings
from app.db.models import get_build

router = APIRouter(prefix="/api", tags=["export"])


@router.get("/build/{build_id}/model.glb")
async def get_glb(build_id: str):
    """Serve the GLB model file for a build."""
    build = await get_build(build_id)
    if build and build.get("glb_path"):
        path = Path(build["glb_path"])
        if path.exists():
            return FileResponse(path, media_type="model/gltf-binary", filename="model.glb")

    # Fallback: check filesystem directly
    path = settings.EXPORTS_DIR / build_id / "model.glb"
    if path.exists():
        return FileResponse(path, media_type="model/gltf-binary", filename="model.glb")

    raise HTTPException(404, "GLB model not found")


@router.get("/build/{build_id}/model.stl")
async def get_stl(build_id: str):
    """Serve the STL model file for a build."""
    build = await get_build(build_id)
    if build and build.get("stl_path"):
        path = Path(build["stl_path"])
        if path.exists():
            return FileResponse(path, media_type="model/stl", filename="model.stl")

    path = settings.EXPORTS_DIR / build_id / "model.stl"
    if path.exists():
        return FileResponse(path, media_type="model/stl", filename="model.stl")

    raise HTTPException(404, "STL model not found")


@router.get("/export/{build_id}/{fmt}")
async def export_model(build_id: str, fmt: str):
    """Generic export endpoint. Supports 'stl' and 'glb' formats."""
    if fmt == "glb":
        return await get_glb(build_id)
    elif fmt == "stl":
        return await get_stl(build_id)
    else:
        raise HTTPException(400, f"Unsupported format: {fmt}. Use 'stl' or 'glb'.")
