"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_budget import router as budget_router
from app.api.routes_build import router as build_router
from app.api.routes_export import router as export_router
from app.api.routes_parse import router as parse_router
from app.api.routes_validate import router as validate_router
from app.config import settings
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — initialize DB on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Syrus — AI Jewelry 2D→3D Engine",
    description="Parametric jewelry generation with real-time customization",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────
app.include_router(parse_router)
app.include_router(build_router)
app.include_router(budget_router)
app.include_router(validate_router)
app.include_router(export_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
