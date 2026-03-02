---
name: jewelry-image-parser
description: Deterministic rules for converting 2D jewelry images into structured parametric JSON for CAD generation.
---

# PURPOSE

This skill defines how 2D jewelry images are interpreted and converted into structured parametric data.

The objective is:
- Structured extraction
- Deterministic behavior
- Stable JSON output
- No artistic guessing

Output must strictly follow the jewelry parametric schema.

---

# INPUT ASSUMPTIONS

Input:
- Single jewelry item
- Front-facing or slight perspective
- Clean background preferred
- Ring, pendant, or earring

If multiple objects are detected:
→ Select the most central object.

If background noise exists:
→ Ignore background regions.

---

# OUTPUT FORMAT (MANDATORY)

{
  "ring_radius": float,
  "band_width": float,
  "band_thickness": float,
  "center_stone": {
    "type": string,
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
  ],
  "confidence_score": float
}

No extra fields allowed.
If uncertain → use fallback defaults.

---

# RING DETECTION RULES

1. Detect circular or elliptical band region.
2. Estimate inner and outer boundary.
3. Compute band_width as:
   outer_radius - inner_radius
4. Estimate ring_radius as:
   average(inner_diameter / 2)

If ellipse due to perspective:
→ Correct using vertical axis scaling.

If band is partially occluded:
→ Infer missing arc using symmetry assumption.

---

# CENTER STONE IDENTIFICATION LOGIC

1. Detect largest gemstone region inside ring boundary.
2. Must lie on central vertical axis.
3. Shape classification rules:

- Circular → "round"
- Elongated symmetric → "oval"
- Rectangular step-cut → "emerald"
- Teardrop → "pear"

If ambiguous:
→ Default to "round"

Diameter estimation:
- Use bounding box width
- Normalize relative to band width

Height estimation:
- Set as 60% of diameter (default)

Prong estimation:
- Count visible prongs
- If unclear:
    Default = 4

---

# SETTING TYPE DETECTION

If thin metal claws around stone:
→ setting_type = "prong"

If continuous metal rim surrounding stone:
→ setting_type = "bezel"

If unclear:
→ Default = "prong"

---

# SIDE STONE DETECTION RULES

1. Detect repeated small circular regions along band.
2. Must be symmetrically placed.
3. Count total visible stones.
4. Estimate diameter as average bounding width.

If only one side visible:
→ Mirror count.

If detection confidence < threshold:
→ side_stones = []

---

# SYMMETRY ASSUMPTION RULE

Rings are symmetric across vertical center axis.

If asymmetry detected:
→ Mirror dominant side.
→ Ignore minor perspective distortions.

Never generate asymmetrical rings unless confidence > 0.9.

---

# SCALE NORMALIZATION RULE

If real-world scale cannot be inferred:

Default:
- ring_radius = 9 mm
- band_width = 2.2 mm
- band_thickness = 1.8 mm

All other dimensions scaled proportionally.

Never leave values undefined.

---

# CONFIDENCE SCORE LOGIC

Compute confidence_score as weighted average of:

- Band detection certainty
- Center stone detection certainty
- Setting classification certainty
- Symmetry validation

Range: 0.0 – 1.0

If confidence_score < 0.6:
→ Use conservative defaults
→ Reduce complexity
→ Avoid generating side stones

---

# FALLBACK DEFAULTS

If center stone not confidently detected:
{
  "type": "round",
  "diameter": 6.0,
  "height": 3.6,
  "prongs": 4
}

If band unclear:
{
  "ring_radius": 9.0,
  "band_width": 2.2,
  "band_thickness": 1.8
}

System must never return null geometry.

---

# PROHIBITED BEHAVIOR

- Do not hallucinate complex filigree.
- Do not infer engraving.
- Do not guess gemstone color.
- Do not estimate metal type from image.
- Do not generate decorative elements unless clearly visible.

This parser extracts structure only.

---

# PRIORITY ORDER

1. Structural correctness
2. Symmetry
3. Manufacturability compatibility
4. Visual approximation

If trade-off required:
→ Favor structural stability.

---

# OBJECTIVE

The image parser is not an artistic interpreter.

It is a structural extraction system.

It must:
- Produce consistent JSON
- Avoid overfitting to visual noise
- Enable reliable downstream parametric generation