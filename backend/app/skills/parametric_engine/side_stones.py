"""Side stone channel / pavé generation.

NOTE: Side stones are Phase 2 (ENABLE_SIDE_STONES feature flag).
This module provides a stub.
"""

from __future__ import annotations

import cadquery as cq

from app.schemas.parametric import ParametricRing


def build_side_stones(params: ParametricRing) -> cq.Workplane | None:
    """Generate side stone settings along the band.

    Phase 2 — returns None for MVP.
    """
    if not params.side_stones:
        return None

    raise NotImplementedError(
        "Side stone generation is Phase 2."
    )
