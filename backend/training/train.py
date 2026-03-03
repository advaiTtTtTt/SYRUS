"""SYRUS YOLO Fine-Tuning Script — Transfer-learn YOLOv8 for jewelry detection.

Usage:
    python -m training.train --epochs 100 --batch 16 --imgsz 640

Prerequisites:
    pip install ultralytics

Output:
    Trained weights → backend/models/jewelry_yolov8.pt
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT.parent
DATASET_YAML = ROOT / "jewelry.yaml"
MODELS_DIR = BACKEND / "models"


def train(
    epochs: int = 100,
    batch: int = 16,
    imgsz: int = 640,
    base_model: str = "yolov8n.pt",
    device: str = "",
    patience: int = 20,
) -> Path:
    """Fine-tune YOLOv8 on the jewelry dataset.

    Args:
        epochs: Number of training epochs (default 100)
        batch: Batch size (default 16, reduce for low VRAM)
        imgsz: Input image size (default 640)
        base_model: Pre-trained base model to transfer-learn from
        device: CUDA device ('0', '0,1', 'cpu', '' for auto)
        patience: Early stopping patience (epochs without improvement)

    Returns:
        Path to the best trained weights file.
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        raise SystemExit(
            "ultralytics is required: pip install ultralytics\n"
            "GPU training also needs: pip install torch torchvision"
        )

    if not DATASET_YAML.exists():
        raise FileNotFoundError(
            f"Dataset config not found: {DATASET_YAML}\n"
            "Create your dataset first — see training/README.md"
        )

    # Verify dataset has images
    dataset_root = ROOT / "dataset"
    train_images = dataset_root / "images" / "train"
    if not train_images.exists() or not list(train_images.glob("*")):
        raise FileNotFoundError(
            f"No training images found in {train_images}\n"
            "Annotate images first — see training/README.md"
        )

    val_images = dataset_root / "images" / "val"
    if not val_images.exists() or not list(val_images.glob("*")):
        print("⚠  No validation images found — training without validation split")

    print(f"🔧 SYRUS YOLO Fine-Tuning")
    print(f"   Base model:  {base_model}")
    print(f"   Dataset:     {DATASET_YAML}")
    print(f"   Epochs:      {epochs}")
    print(f"   Batch size:  {batch}")
    print(f"   Image size:  {imgsz}")
    print(f"   Device:      {device or 'auto'}")
    print()

    # Load pre-trained model
    model = YOLO(base_model)

    # Train with augmentation
    results = model.train(
        data=str(DATASET_YAML),
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device=device or None,
        patience=patience,
        # Augmentation (aggressive for small datasets)
        hsv_h=0.015,       # Hue shift
        hsv_s=0.5,         # Saturation shift
        hsv_v=0.3,         # Value/brightness shift
        degrees=15.0,       # Random rotation ±15°
        translate=0.1,      # Random translate ±10%
        scale=0.3,          # Random scale ±30%
        shear=2.0,          # Random shear ±2°
        flipud=0.0,         # No vertical flip (jewelry has fixed orientation)
        fliplr=0.5,         # Horizontal flip 50%
        mosaic=1.0,         # Mosaic augmentation
        mixup=0.1,          # MixUp augmentation
        # Training config
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,           # Final LR = lr0 × lrf
        warmup_epochs=3,
        cos_lr=True,
        # Logging
        project=str(ROOT / "runs"),
        name="jewelry_detect",
        save=True,
        plots=True,
        verbose=True,
    )

    # Copy best weights to models/ directory
    best_weights = Path(results.save_dir) / "weights" / "best.pt"
    if best_weights.exists():
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        dest = MODELS_DIR / "jewelry_yolov8.pt"
        shutil.copy2(best_weights, dest)
        print(f"\n✅ Best weights copied to: {dest}")
        print(f"   Update config.py → YOLO_WEIGHTS = 'jewelry_yolov8.pt'")
        return dest
    else:
        print(f"\n⚠  Training completed but best.pt not found at {best_weights}")
        return best_weights


def main():
    parser = argparse.ArgumentParser(description="Fine-tune YOLOv8 for SYRUS jewelry detection")
    parser.add_argument("--epochs", type=int, default=100, help="Training epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    parser.add_argument("--base-model", type=str, default="yolov8n.pt", help="Base model")
    parser.add_argument("--device", type=str, default="", help="CUDA device")
    parser.add_argument("--patience", type=int, default=20, help="Early stopping patience")
    args = parser.parse_args()

    train(
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        base_model=args.base_model,
        device=args.device,
        patience=args.patience,
    )


if __name__ == "__main__":
    main()
