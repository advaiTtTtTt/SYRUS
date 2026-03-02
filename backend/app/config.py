"""Application configuration — paths, feature flags, defaults."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Paths ──────────────────────────────────────────────────────
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOADS_DIR: Path = BASE_DIR / "uploads"
    EXPORTS_DIR: Path = BASE_DIR / "exports"
    MODELS_DIR: Path = BASE_DIR / "models"
    DB_PATH: Path = BASE_DIR / "db" / "syrus.db"

    # ── Server ─────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ── Defaults (mm) ──────────────────────────────────────────────
    DEFAULT_RING_RADIUS: float = 9.0
    DEFAULT_BAND_WIDTH: float = 2.2
    DEFAULT_BAND_THICKNESS: float = 1.8

    # ── Image Parser ───────────────────────────────────────────────
    CONFIDENCE_THRESHOLD: float = 0.6
    YOLO_WEIGHTS: str = "yolov8n.pt"  # placeholder until fine-tuned

    # ── Build ──────────────────────────────────────────────────────
    STL_TOLERANCE: float = 0.01  # mm
    STL_ANGULAR_TOLERANCE: float = 0.1  # degrees

    # ── Feature Flags ──────────────────────────────────────────────
    ENABLE_SIDE_STONES: bool = False  # Phase 2
    ENABLE_BEZEL_SETTING: bool = False  # Phase 2

    model_config = {"env_prefix": "SYRUS_", "env_file": ".env"}


settings = Settings()

# Ensure directories exist
for d in (settings.UPLOADS_DIR, settings.EXPORTS_DIR, settings.MODELS_DIR, settings.DB_PATH.parent):
    d.mkdir(parents=True, exist_ok=True)
