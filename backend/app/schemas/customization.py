"""Customization wrapper — user-selected material & budget preferences.

These fields are NOT extracted from the image (per jewelry-image-parser SKILL:
'Do not estimate metal type from image', 'Do not guess gemstone color').
They come from user input exclusively.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MetalType(str, Enum):
    GOLD_18K = "18k_gold"
    GOLD_14K = "14k_gold"
    PLATINUM = "platinum"
    SILVER = "silver"


class GemstoneMaterial(str, Enum):
    DIAMOND = "diamond"
    RUBY = "ruby"
    SAPPHIRE = "sapphire"
    EMERALD = "emerald"
    MOISSANITE = "moissanite"


class Customization(BaseModel):
    """User-selected material and budget preferences (Layer 2)."""

    metal_type: MetalType = Field(
        default=MetalType.GOLD_18K,
        description="Metal type — default 18k Gold per budget-logic SKILL"
    )
    gemstone_material: GemstoneMaterial = Field(
        default=GemstoneMaterial.DIAMOND,
        description="Center stone material — default Diamond per budget-logic SKILL"
    )
    side_stone_material: GemstoneMaterial = Field(
        default=GemstoneMaterial.DIAMOND,
        description="Side stone material"
    )
    target_budget: Optional[float] = Field(
        default=None, ge=0,
        description="Target budget in ₹ (INR). None = no budget constraint."
    )
