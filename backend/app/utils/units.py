"""Millimeter unit enforcement utilities.

GLOBAL RULE (jewelry-parametric-engine SKILL):
  All dimensions MUST be in millimeters. Never inches, never mix units.
"""

from __future__ import annotations

MM_MIN = 0.001  # smallest meaningful dimension in mm


def mm(value: float) -> float:
    """Identity wrapper — documents that a value is in millimeters."""
    return float(value)


def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp *value* into [lo, hi].  All values assumed mm."""
    return max(lo, min(hi, float(value)))


def mm3_to_cm3(volume_mm3: float) -> float:
    """Convert mm³ → cm³  (1 cm³ = 1000 mm³)."""
    return volume_mm3 / 1000.0


def validate_positive_mm(value: float, name: str = "dimension") -> float:
    """Raise if value is not a positive mm dimension."""
    v = float(value)
    if v < MM_MIN:
        raise ValueError(f"{name} must be > {MM_MIN} mm, got {v}")
    return v
