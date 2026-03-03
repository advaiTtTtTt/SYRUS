"""Advanced ring-setting manufacturability checks.

Validates pavé shoulder, halo layout, and cathedral support geometry
for structural integrity and manufacturing feasibility.

Source of truth: manufacturability-validator/SKILL.md

Checks:
  1. Pavé seat depth — stone embedment must not exceed 50 % of band thickness.
  2. Halo spacing — adjacent halo stones must have ≥ 0.3 mm gap.
  3. Cathedral support thickness ≥ 1.2 mm.
  4. Overlapping stone prevention — arc/circumference vs count validation.

Auto-corrects where possible; rejects only for irrecoverable geometry.
"""

from __future__ import annotations

import math

from app.schemas.parametric import ParametricRing, SettingStyle


# ── Thresholds ─────────────────────────────────────────────────────

MIN_STONE_SPACING = 0.3          # mm gap between adjacent stones
MAX_SEAT_DEPTH_RATIO = 0.50      # seat must not exceed 50 % of band thickness
CATHEDRAL_MIN_THICKNESS = 1.2    # mm structural minimum
CATHEDRAL_BAND_FACTOR = 0.4      # support thickness = band_thickness × factor
MIN_BAND_FOR_CATHEDRAL = 3.0     # band_thickness must be ≥ this for cathedral
HALO_MIN_STONES = 3              # fewer than 3 stones is a degenerate halo
EMBED_RATIO = 0.40               # stone embedded 40 % into surface


def check_ring_setting(
    params: ParametricRing,
    violations: list[str],
    corrections: list[str],
) -> ParametricRing:
    """Dispatch setting-specific checks based on setting_style.

    Only called for rings.  Solitaire has no additional checks.
    """
    style = params.setting_style

    if style == SettingStyle.PAVE_SHOULDER:
        params = _check_pave(params, violations, corrections)
    elif style == SettingStyle.HALO:
        params = _check_halo(params, violations, corrections)
    elif style == SettingStyle.CATHEDRAL:
        params = _check_cathedral(params, violations, corrections)

    return params


# ── Pavé checks ────────────────────────────────────────────────────

def _check_pave(
    params: ParametricRing,
    violations: list[str],
    corrections: list[str],
) -> ParametricRing:
    """Validate pavé shoulder layout for manufacturing feasibility."""
    ssl = params.side_stone_layout
    if ssl is None or not ssl.enabled:
        return params

    stone_r = ssl.diameter / 2.0
    embed_depth = stone_r * EMBED_RATIO

    # 1. Seat depth vs band thickness
    max_allow = params.band_thickness * MAX_SEAT_DEPTH_RATIO
    if embed_depth > max_allow:
        # Auto-correct: reduce stone diameter so embed fits
        safe_r = max_allow / EMBED_RATIO
        safe_d = round(safe_r * 2.0, 2)
        safe_d = max(1.0, safe_d)  # floor at 1.0 mm
        corrections.append(
            f"Pavé stone diameter {ssl.diameter} → {safe_d} mm "
            f"(seat depth {embed_depth:.2f} exceeded {max_allow:.2f} mm)"
        )
        ssl.diameter = safe_d

    # 2. Overlapping prevention: check arc fits
    r_outer = params.ring_radius + params.band_thickness
    available_arc = 2.0 * (math.radians(75) * r_outer)  # ~150° per shoulder
    per_shoulder = ssl.count // 2 if ssl.count > 0 else 0

    if per_shoulder > 0:
        needed_arc = per_shoulder * (ssl.diameter + MIN_STONE_SPACING)
        if needed_arc > available_arc:
            max_count = int(available_arc / (ssl.diameter + MIN_STONE_SPACING))
            safe_total = max_count * 2 * ssl.rows
            corrections.append(
                f"Pavé count {ssl.count} → {safe_total} "
                f"(exceeds arc capacity of {max_count}/shoulder)"
            )
            ssl.count = safe_total

    # 3. Minimum spacing check
    if ssl.diameter < 1.0:
        corrections.append(f"Pavé stone diameter {ssl.diameter} → 1.0 mm (below minimum)")
        ssl.diameter = 1.0

    return params


# ── Halo checks ────────────────────────────────────────────────────

def _check_halo(
    params: ParametricRing,
    violations: list[str],
    corrections: list[str],
) -> ParametricRing:
    """Validate halo layout spacing and stone count."""
    ssl = params.side_stone_layout
    if ssl is None or not ssl.enabled:
        return params

    stone_r = ssl.diameter / 2.0
    center_r = params.center_stone.diameter / 2.0

    # Halo radius
    gap = 0.3  # mm metal wall between center stone and halo
    r_halo = center_r + gap + stone_r

    # 1. Auto-calculate max count from circumference
    circumference = 2.0 * math.pi * r_halo
    max_count = int(circumference / (ssl.diameter + MIN_STONE_SPACING))

    if max_count < HALO_MIN_STONES:
        violations.append(
            f"Halo impossible: only {max_count} stones fit "
            f"(min {HALO_MIN_STONES}) around {params.center_stone.diameter} mm center stone"
        )
        return params

    # 2. If explicit count exceeds maximum, clamp down
    if ssl.count > max_count:
        corrections.append(
            f"Halo count {ssl.count} → {max_count} "
            f"(circumference only fits {max_count} × {ssl.diameter} mm stones)"
        )
        ssl.count = max_count

    # 3. Verify actual spacing after count is set
    actual_count = ssl.count if ssl.count > 0 else max_count
    if actual_count > 0:
        actual_spacing = (circumference / actual_count) - ssl.diameter
        if actual_spacing < MIN_STONE_SPACING:
            safe_count = int(circumference / (ssl.diameter + MIN_STONE_SPACING))
            if ssl.count > 0 and ssl.count != safe_count:
                corrections.append(
                    f"Halo spacing too tight ({actual_spacing:.2f} mm < {MIN_STONE_SPACING} mm), "
                    f"count adjusted {ssl.count} → {safe_count}"
                )
                ssl.count = safe_count

    # 4. Halo stones must not overlap center stone
    stone_outer = center_r + gap
    if stone_r > gap:
        safe_d = round(gap * 0.9 * 2.0, 2)  # 90% of gap
        safe_d = max(1.0, safe_d)
        corrections.append(
            f"Halo stones too large ({ssl.diameter} mm) for gap — "
            f"reduced to {safe_d} mm"
        )
        ssl.diameter = safe_d

    return params


# ── Cathedral checks ───────────────────────────────────────────────

def _check_cathedral(
    params: ParametricRing,
    violations: list[str],
    corrections: list[str],
) -> ParametricRing:
    """Validate cathedral support structural requirements."""

    # 1. Support thickness = band_thickness × 0.4, must be ≥ 1.2 mm
    support_thickness = params.band_thickness * CATHEDRAL_BAND_FACTOR
    if support_thickness < CATHEDRAL_MIN_THICKNESS:
        # Auto-correct: increase band_thickness so support meets minimum
        needed_band = CATHEDRAL_MIN_THICKNESS / CATHEDRAL_BAND_FACTOR
        needed_band = round(max(needed_band, params.band_thickness), 2)
        # Clamp to schema max (3.5 mm)
        if needed_band > 3.5:
            violations.append(
                f"Cathedral requires band_thickness ≥ {needed_band:.1f} mm "
                f"(exceeds max 3.5 mm) — REJECTED"
            )
            return params
        corrections.append(
            f"Increased band_thickness {params.band_thickness} → {needed_band} mm "
            f"(cathedral support needs ≥ {CATHEDRAL_MIN_THICKNESS} mm)"
        )
        params.band_thickness = needed_band

    # 2. Band width should be reasonable for arch visual proportion
    if params.band_width < 2.0:
        corrections.append(
            f"Increased band_width {params.band_width} → 2.0 mm "
            f"(cathedral needs adequate shoulder width)"
        )
        params.band_width = 2.0

    # 3. Center stone must be elevated enough for arches
    min_stone_height = params.band_width * 0.5
    if params.center_stone.height < min_stone_height:
        violations.append(
            f"Center stone height {params.center_stone.height:.2f} mm too low "
            f"for cathedral arches (need ≥ {min_stone_height:.2f} mm)"
        )

    return params
