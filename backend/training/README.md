# SYRUS Jewelry Detection — YOLOv8 Training Pipeline

This directory contains everything needed to fine-tune YOLOv8 for jewelry component detection.

## Classes

| ID | Label | Description |
|----|-------|-------------|
| 0 | `ring_band` | Ring band / shank |
| 1 | `center_stone` | Center gemstone |
| 2 | `prong` | Individual prong holding the stone |
| 3 | `bezel_rim` | Bezel setting rim (Phase 2) |
| 4 | `side_stone` | Side / accent stone (Phase 2) |
| 5 | `bail` | Pendant bail loop |
| 6 | `pendant_body` | Pendant base plate |
| 7 | `earring_stud` | Earring stud disc |

## Quick Start

### 1. Annotate Images
```bash
pip install labelimg
labelimg dataset/images/train dataset/labels/train dataset/jewelry.names
```
Or use [Roboflow](https://roboflow.com) / [CVAT](https://cvat.ai) for faster annotation.

### 2. Organize Dataset
```
dataset/
├── images/
│   ├── train/    # 70% of images
│   └── val/      # 30% of images
├── labels/
│   ├── train/    # YOLO-format .txt labels
│   └── val/
└── jewelry.yaml  # Dataset config
```

### 3. Train
```bash
cd backend
python -m training.train --epochs 100 --batch 16 --imgsz 640
```

### 4. Deploy
Trained weights are saved to `backend/models/jewelry_yolov8.pt`.
Update `config.py` → `YOLO_WEIGHTS = "jewelry_yolov8.pt"`.

## Synthetic Data

Run the synthetic data generator to create training images from parametric renders:
```bash
python -m training.generate_synthetic --count 200 --output dataset/images/train
```
