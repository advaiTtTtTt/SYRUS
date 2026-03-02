"""Setting complexity classifier.

Resolves SKILL ambiguity: 'halo' and 'solitaire' are not explicit
in the parametric schema. We infer from side_stones data.

Rules (from plan):
  - No side stones           → Solitaire (×1.0)
  - Side stones ≤ 10, small  → potential Halo (×1.15) if count > 6 & diameter < 2mm
  - Side stones total > 10   → Multi-stone (×1.2)
  - Prongs > 6               → additional Intricate prong (×1.1)
"""

from __future__ import annotations

from app.schemas.parametric import ParametricRing


def setting_complexity_multiplier(params: ParametricRing) -> float:
    """Return the setting complexity multiplier per budget-logic SKILL."""
    total_side = sum(s.count for s in params.side_stones)
    multiplier = 1.0

    if total_side == 0:
        # Solitaire
        multiplier = 1.0
    elif total_side > 10:
        # Multi-stone
        multiplier = 1.2
    else:
        # Check for halo pattern: many small stones
        is_halo = total_side > 6 and all(s.diameter < 2.0 for s in params.side_stones)
        multiplier = 1.15 if is_halo else 1.0

    # Intricate prongs add-on
    if params.center_stone.prongs > 6:
        multiplier *= 1.1

    return round(multiplier, 3)
