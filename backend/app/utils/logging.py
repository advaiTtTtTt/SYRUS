"""Structured logging for parameter corrections/ clamping events."""

from loguru import logger
import sys

# Remove default handler, add structured one
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | {message}",
    level="DEBUG",
)


def log_clamp(param: str, original: float, clamped: float) -> None:
    """Log a parameter clamping event (per parametric-engine SKILL error handling)."""
    if original != clamped:
        logger.warning(
            "CLAMPED {param}: {orig:.3f} → {clamped:.3f} mm",
            param=param,
            orig=original,
            clamped=clamped,
        )


def log_correction(source: str, description: str) -> None:
    """Log an auto-correction applied by the validator or engine."""
    logger.info("AUTO-CORRECT [{source}]: {desc}", source=source, desc=description)
