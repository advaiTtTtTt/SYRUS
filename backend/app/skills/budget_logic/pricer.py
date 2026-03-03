"""Pricing engine — computes metal cost, gemstone cost, total.

Source of truth: jewelry-budget-logic/SKILL.md

Cost Model:
  Total Cost = (Metal Cost + Gemstone Cost) × Setting Complexity Multiplier
  Metal Cost = (Volume_mm3 / 1000) × density × price_per_gram
  Gemstone Cost = carat × price_per_carat
  Carat ≈ (diameter_mm³ × shape_factor) × 0.0000061

Supports: ring (incl. pavé/halo/cathedral add-ons), pendant, earring
"""

from __future__ import annotations

import math

from app.schemas.budget_result import CostBreakdown
from app.schemas.customization import Customization, GemstoneMaterial
from app.schemas.parametric import (
    JewelryType,
    ParametricRing,
    SettingStyle,
    SideStone,
)
from app.utils.units import mm3_to_cm3

from .classifier import setting_complexity_multiplier
from .tables import GEMSTONE_TABLE, METAL_TABLE, SHAPE_FACTORS


# ── Volume estimation ─────────────────────────────────────────────

def estimate_band_volume_mm3(params: ParametricRing) -> float:
    """Estimate ring band volume using torus cross-section.

    V = 2πR × (band_width × band_thickness)
    """
    R = params.ring_radius
    w = params.band_width
    t = params.band_thickness
    return 2.0 * math.pi * R * w * t


def estimate_pendant_volume_mm3(params: ParametricRing) -> float:
    """Estimate pendant metal volume: base plate + bail.

    Base: cylinder/ellipse disc ≈ π × (w/2) × (h/2) × thickness
    Bail: half-torus  ≈ π² × bail_r × wire_r²
    """
    pp = params.pendant_params
    if pp is None:
        return 0.0

    # Base plate (ellipse disc)
    base_vol = math.pi * (pp.base_width / 2.0) * (pp.base_height / 2.0) * pp.base_thickness

    # Bail (half torus)
    bail_r = pp.bail_diameter / 2.0
    wire_r = pp.bail_thickness / 2.0
    bail_vol = math.pi**2 * bail_r * wire_r**2  # half of 2π²Rr²

    return base_vol + bail_vol


def estimate_earring_volume_mm3(params: ParametricRing) -> float:
    """Estimate single earring metal volume: stud disc + back pin.

    Stud: cylinder ≈ π × (d/2)² × thickness
    Pin: tapered cone ≈ π/3 × L × (r₁² + r₁r₂ + r₂²)
    """
    ep = params.earring_params
    if ep is None:
        return 0.0

    # Stud disc
    stud_r = ep.stud_diameter / 2.0
    stud_vol = math.pi * stud_r**2 * ep.stud_thickness

    # Tapered pin (frustum)
    pin_r = ep.pin_diameter / 2.0
    tip_r = pin_r * 0.5
    pin_vol = (math.pi / 3.0) * ep.pin_length * (pin_r**2 + pin_r * tip_r + tip_r**2)

    return stud_vol + pin_vol


def _estimate_metal_volume(params: ParametricRing) -> float:
    """Dispatch volume estimation by jewelry type.

    For rings, adds setting-specific volume adjustments:
      - Pavé/halo seat cuts (metal removed)
      - Halo base plate (metal added)
      - Cathedral supports (metal added)
    """
    if params.type == JewelryType.PENDANT:
        return estimate_pendant_volume_mm3(params)
    elif params.type == JewelryType.EARRING:
        return estimate_earring_volume_mm3(params)
    else:
        vol = estimate_band_volume_mm3(params)
        vol += _ring_setting_volume_delta(params)
        return max(0.0, vol)


def _ring_setting_volume_delta(params: ParametricRing) -> float:
    """Extra metal added or removed by advanced ring settings."""
    delta = 0.0
    ssl = params.side_stone_layout

    if ssl is not None and ssl.enabled:
        stone_r = ssl.diameter / 2.0
        embed_ratio = 0.40
        seat_vol_each = (4.0 / 3.0) * math.pi * (stone_r + 0.05) ** 3 * embed_ratio

        # Determine count: explicit or estimate from geometry
        count = ssl.count if ssl.count > 0 else 0

        if params.setting_style == SettingStyle.PAVE_SHOULDER and count == 0:
            # Rough auto-estimate: arc ~150° each side, 2 shoulders
            r_outer = params.ring_radius + params.band_thickness
            arc_len = 2.0 * (math.radians(75) * r_outer)
            count = max(0, int(arc_len / (ssl.diameter + 0.3))) * ssl.rows

        if params.setting_style == SettingStyle.HALO and count == 0:
            center_r = params.center_stone.diameter / 2.0
            r_halo = center_r + 0.3 + stone_r
            circ = 2.0 * math.pi * r_halo
            count = max(0, int(circ / (ssl.diameter + 0.3)))

        # Subtract seat cuts
        delta -= count * seat_vol_each

    # Halo base plate addition
    if params.setting_style == SettingStyle.HALO:
        center_r = params.center_stone.diameter / 2.0
        ssl_d = ssl.diameter if ssl is not None and ssl.enabled else 1.5
        inner_r = center_r + 0.15
        outer_r = center_r + 0.3 + ssl_d + 0.3
        plate_thickness = 0.8
        delta += math.pi * (outer_r ** 2 - inner_r ** 2) * plate_thickness

    # Cathedral supports addition
    if params.setting_style == SettingStyle.CATHEDRAL:
        thickness = max(1.2, params.band_thickness * 0.4)
        depth = max(1.0, params.band_width * 0.30)
        # Approximate arc length of one support
        r_outer = params.ring_radius + params.band_thickness
        cx = params.ring_radius + params.band_thickness / 2.0
        rise = (params.center_stone.height * 0.85 - params.band_width / 2.0)
        arc_len = math.sqrt((r_outer - cx) ** 2 + rise ** 2) * 1.15  # ~15% arc curve
        delta += 2.0 * thickness * depth * arc_len  # two supports

    return delta


# ── Carat estimation ──────────────────────────────────────────────

def estimate_carat(diameter_mm: float, shape: str) -> float:
    """Carat ≈ (diameter³ × shape_factor) × 0.0000061"""
    factor = SHAPE_FACTORS.get(shape, 1.0)
    return (diameter_mm ** 3) * factor * 0.0000061


# ── Public API ────────────────────────────────────────────────────

def compute_cost(params: ParametricRing, custom: Customization) -> CostBreakdown:
    """Compute full cost breakdown for a jewelry configuration."""
    metal = METAL_TABLE[custom.metal_type]

    # Metal cost — type-aware volume estimation
    volume_mm3 = _estimate_metal_volume(params)
    volume_cm3 = mm3_to_cm3(volume_mm3)
    mass_grams = volume_cm3 * metal["density"]
    metal_cost = mass_grams * metal["price_per_gram"]

    # Center stone cost
    carat = estimate_carat(params.center_stone.diameter, params.center_stone.type.value)
    gem_price = GEMSTONE_TABLE[custom.gemstone_material]
    gemstone_cost = carat * gem_price

    # Side stones cost (manual list)
    side_cost = 0.0
    for ss in params.side_stones:
        ss_carat = estimate_carat(ss.diameter, ss.type.value)
        ss_gem_price = GEMSTONE_TABLE[custom.side_stone_material]
        side_cost += ss_carat * ss_gem_price * ss.count

    # Side stone layout gems (pavé / halo / channel generated stones)
    ssl = params.side_stone_layout
    if ssl is not None and ssl.enabled and ssl.count > 0:
        ssl_carat = estimate_carat(ssl.diameter, "round")  # layout stones are round
        ssl_gem_price = GEMSTONE_TABLE[custom.side_stone_material]
        side_cost += ssl_carat * ssl_gem_price * ssl.count

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
