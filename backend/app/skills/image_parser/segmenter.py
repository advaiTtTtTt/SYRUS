"""SAM-based segmentation for precise region boundaries.

Uses Segment Anything Model to refine detection bounding boxes
into precise masks for accurate geometric measurement.

For MVP, this is optional — if SAM is not available, measurements
fall back to bbox-based approximations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None  # type: ignore
    np = None  # type: ignore

from .detector import Detection


def segment_region(
    image: np.ndarray,
    detection: Detection,
) -> Optional[np.ndarray]:
    """Refine a detection bbox into a precise binary mask using SAM.

    Returns:
        Binary mask (same size as image) or None if SAM unavailable.
    """
    try:
        return _segment_sam(image, detection)
    except (ImportError, FileNotFoundError):
        # SAM not available — return bbox-based mask
        return _bbox_mask(image.shape[:2], detection.bbox)


def _segment_sam(image: np.ndarray, detection: Detection) -> np.ndarray:
    """Run SAM segmentation. Requires SAM checkpoint."""
    # SAM integration placeholder — will be implemented when
    # fine-tuned SAM checkpoint is available
    raise ImportError("SAM not configured yet")


def _bbox_mask(shape: tuple[int, int], bbox: tuple[int, int, int, int]) -> np.ndarray:
    """Create a simple rectangular mask from bounding box."""
    mask = np.zeros(shape, dtype=np.uint8)
    x1, y1, x2, y2 = bbox
    mask[y1:y2, x1:x2] = 255
    return mask
