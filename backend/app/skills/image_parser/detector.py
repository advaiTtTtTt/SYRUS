"""Ring / stone / setting detection using YOLO.

Uses YOLOv8 for object detection with classes:
  0: ring_band
  1: center_stone
  2: prong
  3: bezel_rim (Phase 2)
  4: side_stone (Phase 2)

For MVP, we detect ring_band and center_stone.
If no fine-tuned model is available, falls back to generic
object detection + heuristics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None  # type: ignore
    np = None  # type: ignore


@dataclass
class Detection:
    """A detected region in the image."""
    label: str
    confidence: float
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2
    mask: Optional[np.ndarray] = None


@dataclass
class DetectionResult:
    """All detections from one image."""
    ring_band: Optional[Detection] = None
    center_stone: Optional[Detection] = None
    prongs: list[Detection] = field(default_factory=list)
    raw_detections: list[Detection] = field(default_factory=list)


def detect_jewelry(image_path: Path) -> DetectionResult:
    """Run detection on a jewelry image.

    Strategy:
      1. Try YOLO fine-tuned model if available
      2. Fall back to contour-based heuristic detection
    """
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")

    # Try YOLO first
    try:
        return _detect_yolo(img, image_path)
    except Exception:
        pass

    # Fallback: contour-based heuristic
    return _detect_heuristic(img)


def _detect_yolo(img: np.ndarray, image_path: Path) -> DetectionResult:
    """YOLO-based detection (requires fine-tuned weights)."""
    from ultralytics import YOLO

    from app.config import settings

    model_path = settings.MODELS_DIR / settings.YOLO_WEIGHTS
    if not model_path.exists():
        raise FileNotFoundError(f"YOLO weights not found: {model_path}")

    model = YOLO(str(model_path))
    results = model(img, verbose=False)

    result = DetectionResult()

    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

            label_map = {0: "ring_band", 1: "center_stone", 2: "prong"}
            label = label_map.get(cls_id, "unknown")

            det = Detection(label=label, confidence=conf, bbox=(x1, y1, x2, y2))
            result.raw_detections.append(det)

            if label == "ring_band" and (result.ring_band is None or conf > result.ring_band.confidence):
                result.ring_band = det
            elif label == "center_stone" and (result.center_stone is None or conf > result.center_stone.confidence):
                result.center_stone = det
            elif label == "prong":
                result.prongs.append(det)

    return result


def _detect_heuristic(img: np.ndarray) -> DetectionResult:
    """Fallback heuristic detection using contours and edge analysis.

    This finds the largest elliptical contour (ring band) and the
    largest enclosed region (center stone).
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    result = DetectionResult()

    if not contours:
        return result

    # Sort contours by area (largest first)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    # Largest contour = likely ring band
    if len(contours) >= 1:
        c = contours[0]
        x, y, w, h = cv2.boundingRect(c)
        result.ring_band = Detection(
            label="ring_band",
            confidence=0.5,  # heuristic — lower confidence
            bbox=(x, y, x + w, y + h),
        )

    # Find enclosed contours (potential center stone)
    inner_contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if len(inner_contours) >= 2:
        # Second largest might be the stone
        inner_sorted = sorted(inner_contours, key=cv2.contourArea, reverse=True)
        c = inner_sorted[1]
        x, y, w, h = cv2.boundingRect(c)
        result.center_stone = Detection(
            label="center_stone",
            confidence=0.4,
            bbox=(x, y, x + w, y + h),
        )

    return result
