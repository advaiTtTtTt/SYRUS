"""Setting complexity classifier.

Uses explicit setting_style when available, falls back to inference
from side_stones data for backward compatibility.

Multipliers:
  solitaire      = 1.0
  pave_shoulder   = 1.15
  halo            = 1.2
  cathedral       = 1.1

Add-on: prongs > 6 → ×1.1
"""

from __future__ import annotations

from app.schemas.parametric import ParametricRing, SettingStyle

# Explicit lookup table
_STYLE_MULTIPLIERS: dict[SettingStyle, float] = {
    SettingStyle.SOLITAIRE: 1.0,
    SettingStyle.PAVE_SHOULDER: 1.15,
    SettingStyle.HALO: 1.2,
    SettingStyle.CATHEDRAL: 1.1,
}


def setting_complexity_multiplier(params: ParametricRing) -> float:
    """Return the setting complexity multiplier.

    Prefers explicit setting_style lookup.  Falls back to inference
    from side_stones for legacy payloads without setting_style.
    """
    # Explicit style takes priority
    multiplier = _STYLE_MULTIPLIERS.get(params.setting_style, 1.0)

    # If style is solitaire but side_stones are present (legacy path),
    # fall back to inference so old behavior is preserved.
    if params.setting_style == SettingStyle.SOLITAIRE:
        total_side = sum(s.count for s in params.side_stones)
        if total_side > 10:
            multiplier = 1.2
        elif total_side > 6 and all(s.diameter < 2.0 for s in params.side_stones):
            multiplier = 1.15

    # Intricate prongs add-on
    if params.center_stone.prongs > 6:
        multiplier *= 1.1

    return round(multiplier, 3)
