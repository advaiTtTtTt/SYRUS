"""Synthetic jewelry image generator for YOLO training data.

Generates annotated training images by compositing ring-like shapes
with known bounding boxes. This bootstraps the dataset before real
images are annotated.

Usage:
    python -m training.generate_synthetic --count 200 --output dataset/images/train

Each image gets a matching YOLO-format .txt label file in the
corresponding labels/ directory.

Output format (YOLO):
    <class_id> <x_center> <y_center> <width> <height>
    All values normalized to [0, 1].
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

try:
    import cv2
    import numpy as np
except ImportError:
    raise SystemExit("OpenCV + NumPy required: pip install opencv-python-headless numpy")


# ── Constants ──────────────────────────────────────────────────────

CLASS_RING_BAND = 0
CLASS_CENTER_STONE = 1
CLASS_PRONG = 2

# Background colors (jewelry is often on white, grey, or dark velvet)
BACKGROUNDS = [
    (255, 255, 255),  # white
    (240, 240, 240),  # light grey
    (30, 30, 30),     # dark
    (20, 15, 25),     # dark velvet
    (180, 170, 160),  # beige
    (200, 200, 210),  # light blue-grey
]

# Metal colors (BGR for OpenCV)
METALS = [
    (55, 175, 212),   # gold (BGR)
    (192, 192, 192),  # silver
    (226, 228, 229),  # platinum
    (40, 160, 195),   # rose gold
]

# Gem colors (BGR)
GEMS = [
    (255, 242, 185),  # diamond (clear/blue tint)
    (95, 17, 224),    # ruby
    (186, 82, 15),    # sapphire
    (120, 200, 80),   # emerald
    (200, 230, 245),  # moissanite
]


def _random_ring_image(
    img_size: int = 640,
) -> tuple[np.ndarray, list[tuple[int, float, float, float, float]]]:
    """Generate a synthetic ring image with YOLO annotations.

    Returns:
        (image, annotations) where annotations are (class_id, xc, yc, w, h) normalized.
    """
    bg_color = random.choice(BACKGROUNDS)
    img = np.full((img_size, img_size, 3), bg_color, dtype=np.uint8)

    # Add subtle noise
    noise = np.random.randint(-8, 9, img.shape, dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    annotations: list[tuple[int, float, float, float, float]] = []

    # Ring parameters
    cx = img_size // 2 + random.randint(-40, 40)
    cy = img_size // 2 + random.randint(-30, 30)
    outer_r = random.randint(int(img_size * 0.18), int(img_size * 0.38))
    inner_ratio = random.uniform(0.65, 0.88)
    inner_r = int(outer_r * inner_ratio)
    thickness = max(3, outer_r - inner_r)

    metal_color = random.choice(METALS)

    # Slight perspective (ellipse instead of circle)
    perspective = random.uniform(0.75, 1.0)
    axes_outer = (outer_r, int(outer_r * perspective))
    axes_inner = (inner_r, int(inner_r * perspective))

    # Draw ring band
    angle = random.uniform(-10, 10)
    cv2.ellipse(img, (cx, cy), axes_outer, angle, 0, 360, metal_color, -1, cv2.LINE_AA)
    cv2.ellipse(img, (cx, cy), axes_inner, angle, 0, 360, bg_color, -1, cv2.LINE_AA)

    # Add metallic sheen (gradient overlay)
    for i in range(3):
        highlight_angle = random.uniform(0, 360)
        h_x = int(cx + (outer_r * 0.7) * math.cos(math.radians(highlight_angle)))
        h_y = int(cy + (axes_outer[1] * 0.7) * math.sin(math.radians(highlight_angle)))
        bright = tuple(min(255, c + 40) for c in metal_color)
        cv2.circle(img, (h_x, h_y), thickness // 2, bright, -1, cv2.LINE_AA)

    # Ring band bounding box
    band_w = outer_r * 2 / img_size
    band_h = axes_outer[1] * 2 / img_size
    annotations.append((CLASS_RING_BAND, cx / img_size, cy / img_size, band_w, band_h))

    # Center stone
    gem_color = random.choice(GEMS)
    stone_r = random.randint(int(outer_r * 0.15), int(outer_r * 0.45))
    stone_cy = cy - int(axes_outer[1] * random.uniform(0.85, 1.05))

    shape = random.choice(["round", "oval", "emerald"])
    if shape == "round":
        cv2.circle(img, (cx, stone_cy), stone_r, gem_color, -1, cv2.LINE_AA)
        # Gem highlight
        cv2.circle(img, (cx - stone_r // 4, stone_cy - stone_r // 4),
                   stone_r // 3, tuple(min(255, c + 60) for c in gem_color), -1, cv2.LINE_AA)
        s_w = stone_r * 2 / img_size
        s_h = stone_r * 2 / img_size
    elif shape == "oval":
        s_rx = stone_r
        s_ry = int(stone_r * random.uniform(0.6, 0.85))
        cv2.ellipse(img, (cx, stone_cy), (s_rx, s_ry), 0, 0, 360, gem_color, -1, cv2.LINE_AA)
        s_w = s_rx * 2 / img_size
        s_h = s_ry * 2 / img_size
    else:  # emerald (rectangle with rounded corners)
        s_rx = stone_r
        s_ry = int(stone_r * 0.7)
        pts = np.array([
            [cx - s_rx, stone_cy - s_ry],
            [cx + s_rx, stone_cy - s_ry],
            [cx + s_rx, stone_cy + s_ry],
            [cx - s_rx, stone_cy + s_ry],
        ], np.int32)
        cv2.fillConvexPoly(img, pts, gem_color, cv2.LINE_AA)
        s_w = s_rx * 2 / img_size
        s_h = s_ry * 2 / img_size

    annotations.append((CLASS_CENTER_STONE, cx / img_size, stone_cy / img_size, s_w, s_h))

    # Prongs
    n_prongs = random.choice([3, 4, 5, 6])
    prong_len = max(2, int(stone_r * 0.4))
    prong_w = max(1, int(stone_r * 0.12))
    for i in range(n_prongs):
        a = (i / n_prongs) * 2 * math.pi - math.pi / 2
        px = int(cx + stone_r * 1.05 * math.cos(a))
        py = int(stone_cy + stone_r * 1.05 * math.sin(a))
        px2 = int(cx + stone_r * 0.65 * math.cos(a))
        py2 = int(stone_cy + stone_r * 0.65 * math.sin(a))
        cv2.line(img, (px, py), (px2, py2), metal_color, prong_w, cv2.LINE_AA)

        # Prong tip
        cv2.circle(img, (px2, py2), prong_w, metal_color, -1, cv2.LINE_AA)

        # Prong bounding box
        pw = max(prong_len, abs(px - px2))
        ph = max(prong_len, abs(py - py2))
        pcx = (px + px2) / 2 / img_size
        pcy = (py + py2) / 2 / img_size
        annotations.append((CLASS_PRONG, pcx, pcy, pw / img_size, ph / img_size))

    # Optional: add subtle shadow below ring
    if random.random() > 0.3:
        shadow_cy = cy + int(axes_outer[1] * 0.6)
        shadow_color = tuple(max(0, c - 30) for c in bg_color)
        cv2.ellipse(img, (cx, shadow_cy), (outer_r, int(outer_r * 0.15)),
                    0, 0, 360, shadow_color, -1, cv2.LINE_AA)

    # Optional: slight Gaussian blur for realism
    if random.random() > 0.4:
        ksize = random.choice([3, 5])
        img = cv2.GaussianBlur(img, (ksize, ksize), 0)

    return img, annotations


def generate(count: int, output_dir: str, img_size: int = 640) -> None:
    """Generate synthetic jewelry images + YOLO label files."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Infer labels dir from images dir structure (images/train → labels/train)
    labels_dir = out.parent.parent / "labels" / out.name
    labels_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating {count} synthetic jewelry images...")
    print(f"  Images → {out}")
    print(f"  Labels → {labels_dir}")

    for i in range(count):
        img, annotations = _random_ring_image(img_size)

        # Save image
        fname = f"synthetic_{i:04d}.jpg"
        cv2.imwrite(str(out / fname), img, [cv2.IMWRITE_JPEG_QUALITY, 92])

        # Save YOLO label
        label_fname = f"synthetic_{i:04d}.txt"
        with open(labels_dir / label_fname, "w") as f:
            for cls, xc, yc, w, h in annotations:
                # Clamp to valid range
                xc = max(0.0, min(1.0, xc))
                yc = max(0.0, min(1.0, yc))
                w = max(0.001, min(1.0, w))
                h = max(0.001, min(1.0, h))
                f.write(f"{cls} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")

        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{count} generated")

    print(f"✅ Done! {count} images + labels generated.")
    print(f"   Next: Run training with `python -m training.train`")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic jewelry training data")
    parser.add_argument("--count", type=int, default=200, help="Number of images")
    parser.add_argument("--output", type=str, default="training/dataset/images/train",
                        help="Output directory for images")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    args = parser.parse_args()
    generate(args.count, args.output, args.imgsz)


if __name__ == "__main__":
    main()
