---
name: manufacturability-validator
description: Hard engineering validation and auto-correction rules to ensure all generated jewelry geometry is manufacturable and structurally safe.
---

# PURPOSE

This skill enforces manufacturing safety and structural validity.

It runs AFTER geometry generation and BEFORE export.

It has authority to:
- Reject unsafe geometry
- Auto-correct minor violations
- Clamp unsafe parameters
- Block export if necessary

Aesthetic intent never overrides structural integrity.

---

# GLOBAL STRUCTURAL RULES

All geometry must:

- Be manifold
- Be watertight
- Be a single solid body
- Have outward-facing normals
- Contain no self-intersections
- Contain no zero-thickness surfaces

If violation detected:
→ Attempt auto-repair
→ If repair fails, block export

---

# MINIMUM WALL THICKNESS

Minimum wall thickness anywhere: 1.0 mm  
Recommended structural thickness: 1.2–1.8 mm  

If wall thickness < 1.0 mm:

1. Increase local thickness automatically
2. Preserve outer profile when possible
3. Log correction

If < 0.6 mm:
→ Reject design as structurally unsafe

---

# BAND STRUCTURAL RULES

Minimum band thickness: 1.5 mm  
Minimum band width: 1.5 mm  

If violated:
→ Clamp to minimum safe value

Band must maintain continuous curvature.
No sharp interior corners (fillet ≥ 0.2 mm).

---

# PRONG VALIDATION RULES

Minimum prong thickness: 0.8 mm  
Recommended: 1.0–1.3 mm  

Minimum prong height above girdle: 0.5 mm  
Minimum prong base fusion depth into band: 0.4 mm  

Prongs must:
- Not intersect each other
- Not float disconnected
- Be fused to base geometry
- Have tapered profile (no cylindrical rods)

If prong too thin:
→ Increase to 0.8 mm minimum
→ Preserve visual symmetry

If prongs intersect:
→ Recalculate angular spacing

---

# STONE SEATING VALIDATION

Seat depth must be:
15–25% of stone height.

Seat clearance tolerance:
+0.05 mm (manufacturing tolerance)
-0.00 mm (no negative interference)

Stone must not:
- Penetrate band bottom
- Float above seat
- Clip through prongs

If interference detected:
→ Adjust seat depth automatically

---

# BEZEL STRUCTURAL RULES

Minimum bezel wall thickness: 0.8 mm  
Minimum bezel lip coverage: 0.3 mm above girdle  

Bezel must:
- Fully encircle stone
- Have internal support seat
- Avoid razor-thin edges

If lip too thin:
→ Increase thickness
→ Maintain symmetry

---

# SIDE STONE CHANNEL RULES

Minimum spacing between stones: 0.4 mm  
Minimum metal between pavé stones: 0.5 mm  

If stones overlap:
→ Reduce diameter slightly
→ Or reduce count evenly

Never allow:
- Overlapping stone meshes
- Zero-gap configurations

---

# OVERHANG & PRINTABILITY RULES

For 3D printing compatibility:

Maximum unsupported overhang angle: 60°  
Minimum support contact area: 0.8 mm²  

If unsupported overhang detected:
→ Add structural support thickening
→ Or slightly modify curvature

Do not distort primary design silhouette.

---

# MASS & STABILITY CHECK

Compute:

- Center of mass
- Base support footprint

Ring must:
- Balance evenly
- Not tip excessively forward
- Maintain uniform weight distribution

If unstable:
→ Slightly thicken lower band interior

---

# SHARP EDGE RULE

No external edge sharper than 0.1 mm radius.

All load-bearing junctions must include fillet ≥ 0.2 mm.

If sharp edge detected:
→ Auto-apply fillet

---

# BOOLEAN & SOLID VALIDATION

After all geometry operations:

1. Validate single solid
2. Remove internal faces
3. Check for duplicate vertices
4. Recalculate normals
5. Confirm watertight STL

If failure:
→ Attempt rebuild
→ If still failing, reject export

---

# AUTO-CORRECTION POLICY

Allowed auto-corrections:

- Increase thickness
- Adjust seat depth
- Slightly reduce stone size (≤5%)
- Increase prong thickness
- Add fillets

Not allowed:

- Removing center stone
- Changing ring size drastically
- Downgrading structure without logging
- Silent geometry deletion

All corrections must produce:

{
  "violations_detected": [string],
  "corrections_applied": [string],
  "manufacturing_status": "SAFE" | "AUTO-CORRECTED" | "REJECTED"
}

---

# REJECTION CONDITIONS

Immediately reject if:

- Non-manifold solid cannot be repaired
- Wall thickness < 0.6 mm
- Prongs structurally disconnected
- Stone fully unsupported
- Budget constraints forced unsafe geometry

Return explicit reason.

---

# PERFORMANCE REQUIREMENT

Validation must complete under 300ms for standard ring models.

Validation must not trigger full pipeline rebuild unless required.

---

# PRIORITY ORDER

1. Structural integrity
2. Manufacturability
3. Printability
4. Visual similarity

If trade-off required:
→ Always favor structural safety.

---

# OBJECTIVE

This validator exists to ensure:

- The 3D model is production-ready
- No manual CAD cleanup is required
- The design can realistically be cast or printed
- The system behaves like a professional jewelry CAD assistant

Safety and manufacturability are non-negotiable.