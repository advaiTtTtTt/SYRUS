"""Ring / stone / setting detection – 3-tier strategy.

Tier 1: YOLOv8 fine-tuned model (highest quality, optional)
Tier 2: OpenCV heuristic – Hough circles + adaptive contour analysis
Tier 3: Bbox-only fallback (if OpenCV partially fails)

Class map for YOLO:
  0: ring_band
  1: center_stone
  2: prong
  3: bezel_rim   (Phase 2)
  4: side_stone  (Phase 2)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None  # type: ignore
    np = None   # type: ignore

log = logging.getLogger(__name__)


# ── Data classes ──────────────────────────────────────────────────

@dataclass
class Detection:
    """A detected region in the image."""
    label: str
    confidence: float
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2
    mask: Optional["np.ndarray"] = None
    # Extra geometry (filled by heuristic path)
    center: Optional[tuple[int, int]] = None
    radius: Optional[int] = None


@dataclass
class DetectionResult:
    """All detections from one image."""
    ring_band: Optional[Detection] = None
    center_stone: Optional[Detection] = None
    prongs: list[Detection] = field(default_factory=list)
    raw_detections: list[Detection] = field(default_factory=list)
    # Ellipse data for measurer (heuristic path)
    ring_ellipse: Optional[tuple] = None     # ((cx,cy),(MA,ma),angle)
    stone_ellipse: Optional[tuple] = None


# ── Public entry point ────────────────────────────────────────────

def detect_jewelry(image_path: Path) -> DetectionResult:
    """Run detection on a jewelry image.

    Strategy order:
      1. YOLO fine-tuned model (if weights exist)
      2. Heuristic: Hough circles + morphological contour analysis
    """
    if cv2 is None:
        raise ImportError("OpenCV (cv2) is required for image parsing")

    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")

    # ── Tier 1: YOLO ──────────────────────────────────────────────
    try:
        return _detect_yolo(img, image_path)
    except Exception as exc:
        log.debug("YOLO unavailable (%s), falling back to heuristic", exc)

    # ── Tier 2: Heuristic ─────────────────────────────────────────
    return _detect_heuristic(img)


# ── Tier 1 – YOLO ────────────────────────────────────────────────

def _detect_yolo(img: "np.ndarray", image_path: Path) -> DetectionResult:
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


# ── Tier 2 – Heuristic (Hough + morphological analysis) ──────────

def _detect_heuristic(img: "np.ndarray") -> DetectionResult:
    """Robust heuristic detection pipeline:

    1. Convert to grayscale, CLAHE histogram equalization
    2. Morphological close to fill gaps
    3. HoughCircles to find the ring band circle
    4. Canny + contour analysis to find the center stone
    5. Prong detection via small-contour clustering around stone
    """
    h, w = img.shape[:2]
    result = DetectionResult()

    # ── Pre-processing ─────────────────────────────────────────
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    blurred = cv2.GaussianBlur(enhanced, (9, 9), 2)

    # ── 1. Ring band detection via Hough Circles ───────────────
    min_r = int(min(h, w) * 0.10)
    max_r = int(min(h, w) * 0.48)
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=int(min(h, w) * 0.3),
        param1=100,
        param2=40,
        minRadius=min_r,
        maxRadius=max_r,
    )

    ring_cx, ring_cy, ring_r = w // 2, h // 2, min(h, w) // 4  # fallback

    if circles is not None:
        circles = np.uint16(np.around(circles))
        # Pick the circle closest to image center with the largest radius
        best = None
        best_score = -1
        for c in circles[0]:
            cx, cy, r = int(c[0]), int(c[1]), int(c[2])
            dist_to_center = np.sqrt((cx - w / 2) ** 2 + (cy - h / 2) ** 2)
            # Favour large, centered circles
            score = r - dist_to_center * 0.5
            if score > best_score:
                best_score = score
                best = (cx, cy, r)
        if best is not None:
            ring_cx, ring_cy, ring_r = best
            conf = min(1.0, 0.55 + (best_score / (min(h, w) * 0.5)) * 0.4)
        else:
            conf = 0.3
    else:
        # No Hough circles → try ellipse fitting on largest contour
        conf = 0.3
        morph = cv2.morphologyEx(blurred, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
        edges = cv2.Canny(morph, 30, 100)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            if len(largest) >= 5:
                ellipse = cv2.fitEllipse(largest)
                (ecx, ecy), (ma, mi), angle = ellipse
                ring_cx, ring_cy = int(ecx), int(ecy)
                ring_r = int((ma + mi) / 4)
                result.ring_ellipse = ellipse
                conf = 0.45

    # Create ring band detection
    x1 = max(0, ring_cx - ring_r)
    y1 = max(0, ring_cy - ring_r)
    x2 = min(w, ring_cx + ring_r)
    y2 = min(h, ring_cy + ring_r)
    result.ring_band = Detection(
        label="ring_band",
        confidence=round(conf, 3),
        bbox=(x1, y1, x2, y2),
        center=(ring_cx, ring_cy),
        radius=ring_r,
    )

    # ── 2. Center stone detection ──────────────────────────────
    # Look for bright / high-contrast region in upper portion of ring
    stone_roi_y1 = max(0, ring_cy - ring_r)
    stone_roi_y2 = ring_cy
    stone_roi_x1 = max(0, ring_cx - int(ring_r * 0.6))
    stone_roi_x2 = min(w, ring_cx + int(ring_r * 0.6))

    if stone_roi_y2 > stone_roi_y1 and stone_roi_x2 > stone_roi_x1:
        roi = enhanced[stone_roi_y1:stone_roi_y2, stone_roi_x1:stone_roi_x2]

        # Adaptive threshold to find bright regions (gemstones are usually bright)
        thresh = cv2.adaptiveThreshold(
            roi, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 21, -10
        )

        # Morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # Find the largest enclosed region
            largest_stone = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_stone)
            min_stone_area = (ring_r * 0.15) ** 2 * 3.14  # at least 15% of ring radius

            if area >= min_stone_area:
                sx, sy, sw, sh = cv2.boundingRect(largest_stone)
                # Convert back to image coordinates
                abs_x1 = stone_roi_x1 + sx
                abs_y1 = stone_roi_y1 + sy

                stone_conf = min(0.8, 0.35 + (area / (ring_r * ring_r * 3.14)) * 0.6)

                result.center_stone = Detection(
                    label="center_stone",
                    confidence=round(stone_conf, 3),
                    bbox=(abs_x1, abs_y1, abs_x1 + sw, abs_y1 + sh),
                    center=(abs_x1 + sw // 2, abs_y1 + sh // 2),
                )

                # Try fitting an ellipse for shape classification
                if len(largest_stone) >= 5:
                    stone_ell = cv2.fitEllipse(largest_stone)
                    result.stone_ellipse = stone_ell

    # ── 3. Prong detection ─────────────────────────────────────
    if result.center_stone is not None:
        sc = result.center_stone
        scx = (sc.bbox[0] + sc.bbox[2]) // 2
        scy = (sc.bbox[1] + sc.bbox[3]) // 2
        stone_w = sc.bbox[2] - sc.bbox[0]
        stone_h = sc.bbox[3] - sc.bbox[1]
        search_r = int(max(stone_w, stone_h) * 0.9)

        prong_y1 = max(0, scy - search_r)
        prong_y2 = min(h, scy + search_r)
        prong_x1 = max(0, scx - search_r)
        prong_x2 = min(w, scx + search_r)

        if prong_y2 > prong_y1 and prong_x2 > prong_x1:
            prong_roi = enhanced[prong_y1:prong_y2, prong_x1:prong_x2]
            edges = cv2.Canny(prong_roi, 80, 200)
            kernel_sm = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            edges = cv2.dilate(edges, kernel_sm, iterations=1)

            p_contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Prongs are small, elongated contours near the stone
            min_prong_area = (stone_w * 0.05) ** 2
            max_prong_area = stone_w * stone_h * 0.25

            for pc in p_contours:
                pa = cv2.contourArea(pc)
                if min_prong_area < pa < max_prong_area:
                    px, py, pw, ph = cv2.boundingRect(pc)
                    aspect = max(pw, ph) / max(min(pw, ph), 1)
                    if aspect > 1.5:  # Prongs are elongated
                        abs_px = prong_x1 + px
                        abs_py = prong_y1 + py
                        result.prongs.append(Detection(
                            label="prong",
                            confidence=0.3,
                            bbox=(abs_px, abs_py, abs_px + pw, abs_py + ph),
                        ))

    result.raw_detections = [d for d in [result.ring_band, result.center_stone] if d is not None]
    result.raw_detections.extend(result.prongs)

    return result
