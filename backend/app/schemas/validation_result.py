"""Manufacturability validation result schema.

Source of truth: manufacturability-validator/SKILL.md
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ManufacturingStatus(str, Enum):
    SAFE = "SAFE"
    AUTO_CORRECTED = "AUTO-CORRECTED"
    REJECTED = "REJECTED"


class ValidationResult(BaseModel):
    """Output of the manufacturability validator."""

    violations_detected: list[str] = Field(default_factory=list)
    corrections_applied: list[str] = Field(default_factory=list)
    manufacturing_status: ManufacturingStatus = Field(
        default=ManufacturingStatus.SAFE
    )
