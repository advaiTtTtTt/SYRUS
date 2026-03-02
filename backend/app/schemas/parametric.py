"""Core parametric JSON schema — authoritative ring definition.

Source of truth: jewelry-parametric-engine/SKILL.md
All dimensions in millimeters.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


# ── Enums ──────────────────────────────────────────────────────────

class StoneShape(str, Enum):
    ROUND = "round"
    OVAL = "oval"
    EMERALD = "emerald"
    PEAR = "pear"


class SettingType(str, Enum):
    PRONG = "prong"
    BEZEL = "bezel"


# ── Sub-models ─────────────────────────────────────────────────────

class CenterStone(BaseModel):
    """Center gemstone parametric definition."""

    type: StoneShape = Field(default=StoneShape.ROUND, description="Stone cut shape")
    diameter: float = Field(
        default=6.0, ge=3.0, le=12.0,
        description="Stone diameter in mm (3.0–12.0)"
    )
    height: float = Field(
        default=3.6,
        description="Stone height in mm (40–70% of diameter)"
    )
    prongs: int = Field(
        default=4, ge=3, le=8,
        description="Number of prongs (3–8)"
    )

    @model_validator(mode="after")
    def validate_height_ratio(self) -> "CenterStone":
        """Enforce stone height = 40–70% of diameter (SKILL rule)."""
        lo = self.diameter * 0.40
        hi = self.diameter * 0.70
        if self.height < lo:
            self.height = round(lo, 2)
        elif self.height > hi:
            self.height = round(hi, 2)
        return self


class SideStone(BaseModel):
    """Side stone group definition."""

    type: StoneShape = Field(default=StoneShape.ROUND)
    diameter: float = Field(default=2.0, ge=1.0, le=4.0, description="mm")
    count: int = Field(default=2, ge=1, le=20)


# ── Main parametric schema ─────────────────────────────────────────

class ParametricRing(BaseModel):
    """Canonical ring parametric schema shared across all skills.

    Parameter ranges from jewelry-parametric-engine SKILL:
      ring_radius:    7.0 – 12.0 mm
      band_width:     1.5 –  6.0 mm
      band_thickness: 1.5 –  3.5 mm
    """

    ring_radius: float = Field(
        default=9.0, ge=7.0, le=12.0,
        description="Inner ring radius in mm"
    )
    band_width: float = Field(
        default=2.2, ge=1.5, le=6.0,
        description="Band width in mm"
    )
    band_thickness: float = Field(
        default=1.8, ge=1.5, le=3.5,
        description="Band thickness in mm"
    )
    center_stone: CenterStone = Field(default_factory=CenterStone)
    setting_type: SettingType = Field(default=SettingType.PRONG)
    side_stones: list[SideStone] = Field(default_factory=list)

    def clamped(self) -> "ParametricRing":
        """Return a copy with all values clamped to skill-defined ranges."""
        data = self.model_dump()
        # Top-level clamps
        data["ring_radius"] = max(7.0, min(12.0, data["ring_radius"]))
        data["band_width"] = max(1.5, min(6.0, data["band_width"]))
        data["band_thickness"] = max(1.5, min(3.5, data["band_thickness"]))
        # Center stone clamps
        cs = data["center_stone"]
        cs["diameter"] = max(3.0, min(12.0, cs["diameter"]))
        cs["prongs"] = max(3, min(8, cs["prongs"]))
        # Height is auto-corrected by validator
        return ParametricRing.model_validate(data)
