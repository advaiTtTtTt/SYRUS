---
name: jewelry-parametric-engine
description: Strict rules and constraints for generating valid parametric jewelry geometry using CadQuery and OpenCascade.
---

# PURPOSE

This skill defines the authoritative rules for generating parametric jewelry geometry.

All geometry produced must:
- Be manufacturable
- Be structurally valid
- Use millimeters as the only unit
- Export clean STL and GLB files
- Be manifold and watertight

This skill overrides any default geometric assumptions.

---

# GLOBAL UNIT RULE

All dimensions are in millimeters (mm).

The system must:
- Never use inches
- Never mix units
- Never auto-scale silently

If unit uncertainty exists → default to millimeters.

---

# JEWELRY JSON SCHEMA (AUTHORITATIVE)

All geometry must be generated from this schema:

{
  "ring_radius": float,
  "band_width": float,
  "band_thickness": float,
  "center_stone": {
    "type": "round" | "oval" | "emerald" | "pear",
    "diameter": float,
    "height": float,
    "prongs": int
  },
  "setting_type": "prong" | "bezel",
  "side_stones": [
    {
      "type": string,
      "diameter": float,
      "count": int
    }
  ]
}

No geometry should be generated without structured parameters.

---

# PARAMETER RANGES (STRICT LIMITS)

## Ring

- ring_radius: 7.0 – 12.0 mm
- band_width: 1.5 – 6.0 mm
- band_thickness: 1.5 – 3.5 mm

## Center Stone

- diameter: 3.0 – 12.0 mm
- height: 40–70% of diameter
- prongs: 3–8 only

If values exceed limits → clamp safely.

---

# PRONG CONSTRAINT RULES

Minimum prong thickness: 0.8 mm  
Recommended prong thickness: 1.0–1.3 mm  

Rules:
- Prongs must taper toward the tip
- Prongs must intersect stone at crown level
- Prongs must extend at least 0.5 mm above stone girdle
- Prongs must not intersect each other

Prong base must be fused to band using fillet (≥ 0.3 mm radius).

---

# STONE SEAT DEPTH RULE

Seat depth must be:

15–25% of stone height.

Too shallow:
→ Stone instability

Too deep:
→ Light performance degradation

Auto-correct outside range.

---

# BEZEL SETTING RULES

If setting_type == "bezel":

- Bezel wall thickness: ≥ 0.8 mm
- Bezel height: 20–30% of stone height above girdle
- Must include internal seat lip
- No sharp internal corners

---

# SYMMETRY RULE

All rings must be symmetric across vertical center plane.

Side stones:
- Must be evenly distributed
- Must mirror across axis

No asymmetrical placement unless explicitly requested.

---

# MANUFACTURABILITY RULES

Minimum wall thickness anywhere: 1.0 mm  
Minimum structural support thickness: 0.8 mm  

Disallowed:
- Floating geometry
- Self-intersections
- Zero-thickness surfaces
- Non-manifold edges
- Inverted normals

All edges joining structural components must use fillet radius ≥ 0.2 mm.

---

# MESH EXPORT RULES

Before STL export:

- Validate solid is closed
- Remove internal faces
- Recompute normals outward
- Confirm watertight mesh
- Confirm single solid body

If invalid:
→ Auto-correct where possible
→ Otherwise reject generation

---

# CAD GENERATION RULES

- Use parametric construction only
- No freeform sculpting
- No mesh boolean hacks
- All geometry must be built from solids
- Always maintain feature tree logic

Preferred operations:
- revolve()
- extrude()
- loft()
- fillet()
- boolean union (clean only)

---

# ERROR HANDLING

If parameters are invalid:

1. Clamp to safe manufacturing value
2. Log correction
3. Continue generation

Never silently produce invalid geometry.

---

# OBJECTIVE

The goal is not artistic approximation.

The goal is:
- Manufacturable
- Constraint-valid
- Parametric
- Customizable
- Cleanly exportable geometry

Accuracy > aesthetics.
Structural validity > visual exaggeration.