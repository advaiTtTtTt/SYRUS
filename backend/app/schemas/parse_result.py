"""Parse result schema — image-parser output.

Extends the core parametric schema with confidence_score
as defined in jewelry-image-parser/SKILL.md.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .parametric import ParametricRing


class DetectionRegion(BaseModel):
    """A single detected region with bounding box (normalised 0-1)."""

    label: str = Field(description="Component label, e.g. ring_band, center_stone, prong")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence 0-1")
    bbox: tuple[float, float, float, float] = Field(
        description="Normalised bounding box (x1, y1, x2, y2) in 0-1 range"
    )


class ParseResult(BaseModel):
    """Output of the jewelry image parser."""

    params: ParametricRing = Field(
        description="Extracted parametric ring definition"
    )
    confidence_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Weighted confidence (0–1). < 0.6 → use conservative defaults."
    )

    # Per-component confidence (useful for UI warnings)
    band_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    stone_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    setting_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    symmetry_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # Detection regions for bbox overlay (normalised 0-1 coords)
    detections: list[DetectionRegion] = Field(
        default_factory=list,
        description="Detected component bounding boxes for visual overlay",
    )
