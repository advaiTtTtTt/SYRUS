"""Auto-correction policy enforcement.

Source of truth: manufacturability-validator/SKILL.md

Allowed auto-corrections:
  ✓ Increase thickness
  ✓ Adjust seat depth
  ✓ Reduce stone size ≤ 5%
  ✓ Increase prong thickness
  ✓ Add fillets

NOT allowed:
  ✗ Remove center stone
  ✗ Change ring size drastically
  ✗ Downgrade structure without logging
  ✗ Silent geometry deletion
"""

from __future__ import annotations

# Maximum stone size reduction allowed by validator (5%)
MAX_STONE_REDUCTION_FRACTION = 0.05

# All allowed correction tags (for audit trail filtering)
ALLOWED_CORRECTIONS = frozenset({
    "increase_thickness",
    "adjust_seat_depth",
    "reduce_stone_size",
    "increase_prong_thickness",
    "add_fillet",
    "adjust_prong_count",
    "adjust_stone_height",
    "increase_band_thickness",
})
