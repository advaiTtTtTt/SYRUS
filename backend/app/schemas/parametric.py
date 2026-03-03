"""Core parametric JSON schema — authoritative jewelry definition.

Source of truth: jewelry-parametric-engine/SKILL.md
All dimensions in millimeters.

Supports: ring, pendant, earring
Backward-compatible: omitting 'type' defaults to "ring".
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


# ── Enums ──────────────────────────────────────────────────────────

class JewelryType(str, Enum):
    RING = "ring"
    PENDANT = "pendant"
    EARRING = "earring"


class StoneShape(str, Enum):
    ROUND = "round"
    OVAL = "oval"
    EMERALD = "emerald"
    PEAR = "pear"
    CUSHION = "cushion"


class SettingType(str, Enum):
    PRONG = "prong"
    BEZEL = "bezel"


class PendantBaseShape(str, Enum):
    CIRCULAR = "circular"
    OVAL = "oval"


class SettingStyle(str, Enum):
    """Ring setting style — drives shoulder and head geometry."""
    SOLITAIRE = "solitaire"
    PAVE_SHOULDER = "pave_shoulder"
    HALO = "halo"
    CATHEDRAL = "cathedral"


class SideStonePattern(str, Enum):
    """Layout pattern for structured side stone placement."""
    PAVE = "pave"
    CHANNEL = "channel"
    HALO = "halo"


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


class SideStoneLayout(BaseModel):
    """Structured side stone layout for pavé, channel, or halo patterns."""

    enabled: bool = Field(default=False, description="Master toggle for side stone layout")
    pattern: SideStonePattern = Field(
        default=SideStonePattern.PAVE,
        description="Layout pattern: pave, channel, or halo"
    )
    count: int = Field(
        default=0, ge=0, le=60,
        description="Total side stones (0 = auto-calculate from geometry)"
    )
    diameter: float = Field(
        default=1.5, ge=1.0, le=4.0,
        description="Individual side stone diameter in mm"
    )
    rows: int = Field(
        default=1, ge=1, le=3,
        description="Number of stone rows (for multi-row pavé)"
    )


# ── Type-specific sub-models ───────────────────────────────────────

class PendantParams(BaseModel):
    """Pendant-specific parametric fields."""

    base_shape: PendantBaseShape = Field(
        default=PendantBaseShape.CIRCULAR,
        description="Shape of the pendant base plate"
    )
    base_width: float = Field(
        default=15.0, ge=8.0, le=30.0,
        description="Base plate width in mm"
    )
    base_height: float = Field(
        default=15.0, ge=8.0, le=35.0,
        description="Base plate height in mm (for oval, may differ from width)"
    )
    base_thickness: float = Field(
        default=1.5, ge=1.0, le=3.5,
        description="Base plate thickness in mm"
    )
    bail_diameter: float = Field(
        default=4.0, ge=2.0, le=8.0,
        description="Bail loop outer diameter in mm"
    )
    bail_thickness: float = Field(
        default=1.2, ge=0.8, le=2.5,
        description="Bail wire thickness in mm (>= 0.8 per manufacturing)"
    )


class EarringParams(BaseModel):
    """Earring-specific parametric fields."""

    stud_diameter: float = Field(
        default=8.0, ge=4.0, le=15.0,
        description="Stud base diameter in mm"
    )
    stud_thickness: float = Field(
        default=1.2, ge=0.8, le=3.0,
        description="Stud base thickness in mm"
    )
    pin_length: float = Field(
        default=10.0, ge=8.0, le=12.0,
        description="Back pin length in mm"
    )
    pin_diameter: float = Field(
        default=0.8, ge=0.7, le=1.2,
        description="Back pin diameter in mm"
    )


# ── Main parametric schema ─────────────────────────────────────────

class ParametricRing(BaseModel):
    """Canonical jewelry parametric schema shared across all skills.

    Backward-compatible: omitting 'type' defaults to "ring".
    Type-specific params live in pendant_params / earring_params.

    Ring parameter ranges from jewelry-parametric-engine SKILL:
      ring_radius:    7.0 – 12.0 mm
      band_width:     1.5 –  6.0 mm
      band_thickness: 1.5 –  3.5 mm
    """

    type: JewelryType = Field(
        default=JewelryType.RING,
        description="Jewelry type: ring, pendant, or earring"
    )
    # ── Ring-specific (ignored for pendant/earring) ────────────────
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
    # ── Shared across all types ────────────────────────────────────
    center_stone: CenterStone = Field(default_factory=CenterStone)
    setting_type: SettingType = Field(default=SettingType.PRONG)
    setting_style: SettingStyle = Field(
        default=SettingStyle.SOLITAIRE,
        description="Ring setting style: solitaire, pave_shoulder, halo, cathedral"
    )
    side_stones: list[SideStone] = Field(default_factory=list)
    side_stone_layout: Optional[SideStoneLayout] = Field(
        default=None,
        description="Structured side stone layout (pavé/channel/halo generator input)"
    )
    # ── Type-specific sub-models ───────────────────────────────────
    pendant_params: Optional[PendantParams] = Field(
        default=None,
        description="Pendant-specific params (required when type='pendant')"
    )
    earring_params: Optional[EarringParams] = Field(
        default=None,
        description="Earring-specific params (required when type='earring')"
    )

    @model_validator(mode="after")
    def ensure_type_params(self) -> "ParametricRing":
        """Auto-populate sub-params when type requires them."""
        if self.type == JewelryType.PENDANT and self.pendant_params is None:
            self.pendant_params = PendantParams()
        if self.type == JewelryType.EARRING and self.earring_params is None:
            self.earring_params = EarringParams()
        return self

    def clamped(self) -> "ParametricRing":
        """Return a copy with all values clamped to skill-defined ranges."""
        data = self.model_dump()
        # Ring-specific clamps (only meaningful for rings, but always safe)
        data["ring_radius"] = max(7.0, min(12.0, data["ring_radius"]))
        data["band_width"] = max(1.5, min(6.0, data["band_width"]))
        data["band_thickness"] = max(1.5, min(3.5, data["band_thickness"]))
        # Center stone clamps
        cs = data["center_stone"]
        cs["diameter"] = max(3.0, min(12.0, cs["diameter"]))
        cs["prongs"] = max(3, min(8, cs["prongs"]))
        # Pendant clamps
        if data.get("pendant_params"):
            pp = data["pendant_params"]
            pp["base_width"] = max(8.0, min(30.0, pp["base_width"]))
            pp["base_height"] = max(8.0, min(35.0, pp["base_height"]))
            pp["base_thickness"] = max(1.0, min(3.5, pp["base_thickness"]))
            pp["bail_diameter"] = max(2.0, min(8.0, pp["bail_diameter"]))
            pp["bail_thickness"] = max(0.8, min(2.5, pp["bail_thickness"]))
        # Earring clamps
        if data.get("earring_params"):
            ep = data["earring_params"]
            ep["stud_diameter"] = max(4.0, min(15.0, ep["stud_diameter"]))
            ep["stud_thickness"] = max(0.8, min(3.0, ep["stud_thickness"]))
            ep["pin_length"] = max(8.0, min(12.0, ep["pin_length"]))
            ep["pin_diameter"] = max(0.7, min(1.2, ep["pin_diameter"]))
        # Side stone layout clamps
        if data.get("side_stone_layout"):
            ssl = data["side_stone_layout"]
            ssl["count"] = max(0, min(60, ssl["count"]))
            ssl["diameter"] = max(1.0, min(4.0, ssl["diameter"]))
            ssl["rows"] = max(1, min(3, ssl["rows"]))
        # Height is auto-corrected by validator
        return ParametricRing.model_validate(data)
