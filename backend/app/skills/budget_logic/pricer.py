"""Pricing engine — computes metal cost, gemstone cost, total.

Source of truth: jewelry-budget-logic/SKILL.md

Cost Model:
  Total Cost = (Metal Cost + Gemstone Cost) × Setting Complexity Multiplier
  Metal Cost = (Volume_mm3 / 1000) × density × price_per_gram
  Gemstone Cost = carat × price_per_carat
  Carat ≈ (diameter_mm³ × shape_factor) × 0.0000061
"""

from __future__ import annotations

import math

from app.schemas.budget_result import CostBreakdown
from app.schemas.customization import Customization, GemstoneMaterial
from app.schemas.parametric import ParametricRing, SideStone
from app.utils.units import mm3_to_cm3

from .classifier import setting_complexity_multiplier
from .tables import GEMSTONE_TABLE, METAL_TABLE, SHAPE_FACTORS


# ── Volume estimation (analytical for a torus-like band) ──────────

def estimate_band_volume_mm3(params: ParametricRing) -> float:
    """Estimate ring band volume using torus cross-section.

    Torus volume = 2π²Rr² where R = ring_radius, r = half of cross-section.
    We model the cross-section as a rectangle (band_width × band_thickness)
    and compute: V = 2πR × (band_width × band_thickness)
    This is a reasonable first-order approximation.
    """
    R = params.ring_radius  # center radius of band
    w = params.band_width
    t = params.band_thickness
    return 2.0 * math.pi * R * w * t


# ── Carat estimation ──────────────────────────────────────────────

def estimate_carat(diameter_mm: float, shape: str) -> float:
    """Carat ≈ (diameter³ × shape_factor) × 0.0000061"""
    factor = SHAPE_FACTORS.get(shape, 1.0)
    return (diameter_mm ** 3) * factor * 0.0000061


# ── Public API ────────────────────────────────────────────────────

def compute_cost(params: ParametricRing, custom: Customization) -> CostBreakdown:
    """Compute full cost breakdown for a ring configuration."""
    metal = METAL_TABLE[custom.metal_type]

    # Metal cost
    volume_mm3 = estimate_band_volume_mm3(params)
    volume_cm3 = mm3_to_cm3(volume_mm3)
    mass_grams = volume_cm3 * metal["density"]
    metal_cost = mass_grams * metal["price_per_gram"]

    # Center stone cost
    carat = estimate_carat(params.center_stone.diameter, params.center_stone.type.value)
    gem_price = GEMSTONE_TABLE[custom.gemstone_material]
    gemstone_cost = carat * gem_price

    # Side stones cost
    side_cost = 0.0
    for ss in params.side_stones:
        ss_carat = estimate_carat(ss.diameter, ss.type.value)
        ss_gem_price = GEMSTONE_TABLE[custom.side_stone_material]
        side_cost += ss_carat * ss_gem_price * ss.count

    # Setting complexity
    multiplier = setting_complexity_multiplier(params)

    total = (metal_cost + gemstone_cost + side_cost) * multiplier

    return CostBreakdown(
        metal_cost=round(metal_cost, 2),
        gemstone_cost=round(gemstone_cost, 2),
        side_stones_cost=round(side_cost, 2),
        setting_multiplier=multiplier,
        total_cost=round(total, 2),
    )
