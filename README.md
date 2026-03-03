# SYRUS — AI-Driven 2D to 3D Jewelry Generation

> **PS-01 Hackathon Submission** | Real-time parametric jewelry engine with AI image parsing, budget intelligence, and manufacturing validation.

![Ring](https://img.shields.io/badge/type-Ring-a78bfa) ![Pendant](https://img.shields.io/badge/type-Pendant-a78bfa) ![Earring](https://img.shields.io/badge/type-Earring-a78bfa) ![Tests](https://img.shields.io/badge/tests-166%20passed-4ade80)

---

## What It Does

Upload a **2D jewelry image** → SYRUS extracts dimensions via AI → generates a **real-time 3D model** → lets you customize every parameter → validates for **real-world manufacturing** → provides **instant cost estimates** → exports production-ready **STL/GLB** files.

**One image in. A manufacturable 3D design out.**

---

## Architecture

```
 ┌─────────────┐     POST /api/parse      ┌─────────────────────────┐
 │  2D Image   │ ────────────────────────→ │   AI Image Parser       │
 │  (Upload)   │                           │  YOLO → Hough → Defaults│
 └─────────────┘                           └──────────┬──────────────┘
                                                      │ ParseResult JSON
                                                      │ (params + confidence)
       ┌──────────────────────────────────────────────┘
       ▼
 ┌─────────────┐     POST /api/build      ┌─────────────────────────┐
 │  Parametric  │ ────────────────────────→│   CadQuery 3D Engine    │
 │  JSON +      │                          │  band → stone → prongs  │
 │  Sliders     │                          │  pavé → halo → cathedral│
 └──────┬───────┘                          └──────────┬──────────────┘
        │                                             │
        │  POST /api/budget/estimate                  │ Manufacturability
        ▼                                             │ Validator
 ┌─────────────┐                                      ▼
 │ Budget Logic │                            ┌────────────────┐
 │ ₹ Pricing   │                            │ STL + GLB      │
 │ Adjustment   │                            │ Multi-material │
 └─────────────┘                            └────────────────┘
                                                      │
       ┌──────────────────────────────────────────────┘
       ▼
 ┌────────────────────────────────────────────────────────────┐
 │                   React + Three.js Frontend                │
 │  ┌──────────────┐  ┌────────────┐  ┌───────────────────┐  │
 │  │ 3D Viewport  │  │ Customizer │  │ Budget + Validate │  │
 │  │ WebGL render │  │ Real-time  │  │ Live cost + badge │  │
 │  │ Multi-matl   │  │ sliders    │  │ SAFE/CORRECTED/   │  │
 │  └──────────────┘  └────────────┘  │ REJECTED          │  │
 │                                    └───────────────────┘  │
 └────────────────────────────────────────────────────────────┘
```

---

## Key Features

| Feature | Description |
|---------|-------------|
| **AI Image Parsing** | 3-tier detection: YOLO → OpenCV Hough → smart defaults. Per-component confidence scoring (band, stone, setting, symmetry). |
| **Parametric 3D Engine** | CadQuery/OpenCascade B-rep modeling. Supports ring, pendant, earring with type-specific geometry builders. |
| **4 Ring Setting Styles** | Solitaire, Pavé Shoulder, Halo, Cathedral — each with full geometry + pricing + validation. |
| **Real-time Customization** | Debounced sliders update 3D preview instantly. Material changes are shader-only (no rebuild). |
| **Multi-Material GLB** | Named mesh parts (band, center_stone, prongs, pave_stones, halo_stones) → distinct metal/gem materials. |
| **Budget Intelligence** | Deterministic INR pricing: metal volume × density × rate + carat pricing. 5-step auto-adjustment to fit budget. |
| **Manufacturing Validation** | 20+ engineering checks (wall thickness, prong integrity, stone seating, balance). Auto-correct or reject. |
| **Undo / Redo** | Full history stack on all parameter changes. |
| **STL + GLB Export** | Production-ready mesh export. Blocked when validation = REJECTED. |
| **3 Jewelry Types** | Ring, Pendant, Earring — each with type-specific sliders, validation, and 3D fallback previews. |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18 · TypeScript · Vite 6 · Three.js / R3F · Zustand 5 |
| **Backend** | Python 3.12 · FastAPI · Pydantic v2 · CadQuery · trimesh |
| **AI/CV** | YOLOv8 · OpenCV · NumPy |
| **Database** | SQLite (aiosqlite) |
| **Export** | STL (CadQuery) · GLB (trimesh Scene) |
| **Infra** | Docker Compose · Nginx reverse proxy |

---

## Quick Start

### Prerequisites
- Python 3.11+ with pip
- Node.js 18+ with npm

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev    # → http://localhost:5173
```

### Docker (Production)
```bash
docker-compose up --build
# → http://localhost:80
```

---

## Tests

```bash
cd backend && source .venv/bin/activate
python -m pytest tests/ -v
# 166 passed ✓
```

---

## Project Structure

```
Syrus/
├── skills/              # Domain knowledge (SKILL.md specifications)
│   ├── jewelry-image-parser/
│   ├── jewelry-parametric-engine/
│   ├── jewelry-budget-logic/
│   └── manufacturability-validator/
├── backend/             # FastAPI + CadQuery + Budget + Validation
│   ├── app/api/         # REST endpoints (parse, build, budget, export)
│   ├── app/skills/      # 4 skill implementations
│   ├── app/schemas/     # Pydantic models
│   └── tests/           # 166 tests, 1,679 LOC
└── frontend/            # React + Three.js
    └── src/
        ├── components/  # Viewport, Customizer, Budget, Validation
        ├── hooks/       # useBuild (debounced), useBudget
        ├── store/       # Zustand state + undo/redo middleware
        └── api/         # Typed API clients
```

---

## Team

**SYRUS** — Built for PS-01: AI-Driven 2D to 3D Jewelry Generation with Real-Time Customization.
