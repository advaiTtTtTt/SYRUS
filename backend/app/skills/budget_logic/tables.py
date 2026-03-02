"""Material property tables — metal densities, prices, gemstone prices.

Source of truth: jewelry-budget-logic/SKILL.md
Currency: ₹ (INR)
"""

from __future__ import annotations

from app.schemas.customization import GemstoneMaterial, MetalType

# ── Metal properties ───────────────────────────────────────────────
# density in g/cm³, price in ₹/gram

METAL_TABLE: dict[MetalType, dict] = {
    MetalType.GOLD_18K: {"density": 15.6, "price_per_gram": 5_500},
    MetalType.GOLD_14K: {"density": 13.1, "price_per_gram": 4_300},
    MetalType.PLATINUM: {"density": 21.4, "price_per_gram": 3_800},
    MetalType.SILVER:   {"density": 10.5, "price_per_gram": 70},
}

# ── Gemstone properties ───────────────────────────────────────────
# price per carat in ₹

GEMSTONE_TABLE: dict[GemstoneMaterial, float] = {
    GemstoneMaterial.DIAMOND:    60_000,
    GemstoneMaterial.RUBY:       40_000,
    GemstoneMaterial.SAPPHIRE:   35_000,
    GemstoneMaterial.EMERALD:    30_000,
    GemstoneMaterial.MOISSANITE:  8_000,
}

# ── Shape factors for carat estimation ─────────────────────────────
# Carat ≈ (diameter³ × shape_factor) × 0.0000061
# diameter in mm

SHAPE_FACTORS: dict[str, float] = {
    "round":   1.00,
    "oval":    0.95,
    "emerald": 0.90,
    "pear":    0.92,
}

# ── Downgrade hierarchies (budget-logic SKILL) ─────────────────────

GEMSTONE_DOWNGRADE: list[GemstoneMaterial] = [
    GemstoneMaterial.DIAMOND,
    GemstoneMaterial.SAPPHIRE,
    GemstoneMaterial.RUBY,
    GemstoneMaterial.EMERALD,
    GemstoneMaterial.MOISSANITE,
]

METAL_DOWNGRADE: list[MetalType] = [
    MetalType.PLATINUM,
    MetalType.GOLD_18K,
    MetalType.GOLD_14K,
    MetalType.SILVER,
]
