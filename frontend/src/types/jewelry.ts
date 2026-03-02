/**
 * TypeScript mirrors of backend Pydantic schemas.
 * Keep in sync with backend/app/schemas/*.py
 */

// ── Enums ──────────────────────────────────────────────────────

export type StoneShape = "round" | "oval" | "emerald" | "pear";
export type SettingType = "prong" | "bezel";
export type MetalType = "18k_gold" | "14k_gold" | "platinum" | "silver";
export type GemstoneMaterial = "diamond" | "ruby" | "sapphire" | "emerald" | "moissanite";
export type ManufacturingStatus = "SAFE" | "AUTO-CORRECTED" | "REJECTED";

// ── Core parametric schema ─────────────────────────────────────

export interface CenterStone {
  type: StoneShape;
  diameter: number;
  height: number;
  prongs: number;
}

export interface SideStone {
  type: StoneShape;
  diameter: number;
  count: number;
}

export interface ParametricRing {
  ring_radius: number;
  band_width: number;
  band_thickness: number;
  center_stone: CenterStone;
  setting_type: SettingType;
  side_stones: SideStone[];
}

// ── Customization layer ────────────────────────────────────────

export interface Customization {
  metal_type: MetalType;
  gemstone_material: GemstoneMaterial;
  side_stone_material: GemstoneMaterial;
  target_budget: number | null;
}

// ── Parse result ───────────────────────────────────────────────

export interface ParseResult {
  params: ParametricRing;
  confidence_score: number;
  band_confidence: number;
  stone_confidence: number;
  setting_confidence: number;
  symmetry_confidence: number;
}

// ── Budget result ──────────────────────────────────────────────

export interface CostBreakdown {
  metal_cost: number;
  gemstone_cost: number;
  side_stones_cost: number;
  setting_multiplier: number;
  total_cost: number;
}

export interface BudgetEstimate {
  breakdown: CostBreakdown;
  currency: string;
}

export interface BudgetAdjustment {
  original_cost: number;
  adjusted_cost: number;
  changes_applied: string[];
  budget_fit: boolean;
  adjusted_params: ParametricRing;
}

// ── Validation result ──────────────────────────────────────────

export interface ValidationResult {
  violations_detected: string[];
  corrections_applied: string[];
  manufacturing_status: ManufacturingStatus;
}

// ── Build result ───────────────────────────────────────────────

export interface BuildResponse {
  build_id: string;
  params_used: ParametricRing;
  validation: ValidationResult;
  model_glb_url: string | null;
  model_stl_url: string | null;
}

// ── Parameter limits (from jewelry-parametric-engine SKILL) ────

export const PARAM_LIMITS = {
  ring_radius: { min: 7.0, max: 12.0, step: 0.1 },
  band_width: { min: 1.5, max: 6.0, step: 0.1 },
  band_thickness: { min: 1.5, max: 3.5, step: 0.1 },
  stone_diameter: { min: 3.0, max: 12.0, step: 0.1 },
  stone_prongs: { min: 3, max: 8, step: 1 },
} as const;
