---
name: jewelry-budget-logic
description: Deterministic pricing engine and budget-aware substitution logic for jewelry customization.
---

# PURPOSE

This skill defines all pricing calculations and budget-adjustment logic.

It ensures:
- Transparent cost calculation
- Real-time budget adaptation
- Controlled gemstone substitution
- Predictable behavior

This skill governs business logic only.
It does NOT modify geometric constraints directly.

---

# COST MODEL STRUCTURE

Total Cost = Metal Cost + Gemstone Cost + Setting Complexity Multiplier

All values must be explicitly computed.
No hidden heuristics.

---

# METAL COST CALCULATION

Metal Cost = (Volume in mm³ × Density) × Price per gram

## Default Densities

- Gold (18k): 15.6 g/cm³
- Gold (14k): 13.1 g/cm³
- Platinum: 21.4 g/cm³
- Silver: 10.5 g/cm³

Convert mm³ → cm³ before multiplying density.

## Default Metal Prices (Editable Constants)

- 18k Gold: ₹5,500 / gram
- 14k Gold: ₹4,300 / gram
- Platinum: ₹3,800 / gram
- Silver: ₹70 / gram

Metal type must be explicitly selected.
If unspecified → default = 18k Gold.

---

# GEMSTONE COST CALCULATION

Gemstone Cost = Carat Weight × Price per Carat

## Carat Weight Estimation

Carat ≈ (Diameter³ × Shape Factor) × 0.0000061

Shape Factors:
- Round: 1.0
- Oval: 0.95
- Emerald: 0.9
- Pear: 0.92

## Default Price Per Carat

- Diamond: ₹60,000
- Ruby: ₹40,000
- Sapphire: ₹35,000
- Emerald: ₹30,000
- Moissanite: ₹8,000

If gemstone unspecified → default = Diamond.

Side stones follow same pricing model.

---

# SETTING COMPLEXITY MULTIPLIER

Apply multiplier to total gemstone cost:

- Solitaire: ×1.0
- Halo setting: ×1.15
- Multi-stone (>10 stones): ×1.2
- Intricate prong count (>6): ×1.1

This accounts for labor complexity.

---

# BUDGET ADJUSTMENT LOGIC

If user provides `target_budget`:

System must:

1. Calculate current total cost.
2. Compare against budget.
3. Apply adjustments in controlled hierarchy.

---

# ADJUSTMENT HIERARCHY (STRICT ORDER)

When cost > budget:

1️⃣ Reduce center stone carat (max reduction 20%)
2️⃣ Reduce side stone count (if present)
3️⃣ Downgrade gemstone type
4️⃣ Downgrade metal purity (18k → 14k)
5️⃣ Remove side stones entirely

Never:
- Reduce band thickness below manufacturing limits
- Reduce prong thickness
- Compromise structural integrity

Structural rules override budget rules.

---

# GEMSTONE DOWNGRADE HIERARCHY

Diamond → Sapphire → Ruby → Emerald → Moissanite

Downgrades must preserve stone shape.

---

# METAL DOWNGRADE HIERARCHY

Platinum → 18k Gold → 14k Gold → Silver

Metal change must not affect geometry dimensions.
Only density and pricing update.

---

# SMART SUGGESTION MODE

If reduction required:

System must output:

{
  "original_cost": float,
  "adjusted_cost": float,
  "changes_applied": [string],
  "budget_fit": true | false
}

Never silently modify parameters.
All changes must be logged.

---

# HARD LIMITS

System must reject design if:

- Budget < minimum structural safe build cost
- Budget < cost of smallest allowed center stone
- Budget < minimum metal mass requirement

Return:
"Budget too low for safe manufacturing."

---

# PERFORMANCE RULE

Budget recalculation must complete under 100ms.

No re-running full geometry generation required
unless stone size changes.

Material swaps must update pricing instantly.

---

# OBJECTIVE

This budget engine must:

- Be transparent
- Be predictable
- Preserve structural integrity
- Maintain user trust
- Provide real-time adjustments

Business logic must never break engineering constraints.