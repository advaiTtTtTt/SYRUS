/**
 * TypeScript mirrors of backend Pydantic schemas.
 * Keep in sync with backend/app/schemas/*.py
 */

// ── Enums ──────────────────────────────────────────────────────

export type JewelryType = "ring" | "pendant" | "earring";
export type StoneShape = "round" | "oval" | "emerald" | "pear" | "cushion";
export type SettingType = "prong" | "bezel";
export type SettingStyle = "solitaire" | "pave_shoulder" | "halo" | "cathedral";
export type SideStonePattern = "pave" | "channel" | "halo";
export type MetalType = "18k_gold" | "14k_gold" | "platinum" | "silver";
export type GemstoneMaterial = "diamond" | "ruby" | "sapphire" | "emerald" | "moissanite";
export type ManufacturingStatus = "SAFE" | "AUTO-CORRECTED" | "REJECTED";
export type PendantBaseShape = "circular" | "oval";

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

export interface PendantParams {
  base_shape: PendantBaseShape;
  base_width: number;
  base_height: number;
  base_thickness: number;
  bail_diameter: number;
  bail_thickness: number;
}

export interface EarringParams {
  stud_diameter: number;
  stud_thickness: number;
  pin_length: number;
  pin_diameter: number;
}

export interface SideStoneLayout {
  enabled: boolean;
  pattern: SideStonePattern;
  count: number;
  diameter: number;
  rows: number;
}

export interface ParametricRing {
  type?: JewelryType;
  ring_radius: number;
  band_width: number;
  band_thickness: number;
  center_stone: CenterStone;
  setting_type: SettingType;
  setting_style?: SettingStyle;
  side_stones: SideStone[];
  side_stone_layout?: SideStoneLayout | null;
  pendant_params?: PendantParams | null;
  earring_params?: EarringParams | null;
}

// ── Customization layer ────────────────────────────────────────

export interface Customization {
  metal_type: MetalType;
  gemstone_material: GemstoneMaterial;
  side_stone_material: GemstoneMaterial;
  target_budget: number | null;
}

// ── Parse result ───────────────────────────────────────────────

export interface DetectionRegion {
  label: string;
  confidence: number;
  /** Normalised bounding box [x1, y1, x2, y2] in 0-1 range */
  bbox: [number, number, number, number];
}

export interface ParseResult {
  params: ParametricRing;
  confidence_score: number;
  band_confidence: number;
  stone_confidence: number;
  setting_confidence: number;
  symmetry_confidence: number;
  /** Detected component bounding boxes for visual overlay */
  detections: DetectionRegion[];
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
  // Pendant limits
  pendant_base_width: { min: 8.0, max: 30.0, step: 0.5 },
  pendant_base_height: { min: 8.0, max: 40.0, step: 0.5 },
  pendant_base_thickness: { min: 1.0, max: 4.0, step: 0.1 },
  pendant_bail_diameter: { min: 3.0, max: 8.0, step: 0.5 },
  pendant_bail_thickness: { min: 1.0, max: 3.0, step: 0.1 },
  // Earring limits
  earring_stud_diameter: { min: 4.0, max: 12.0, step: 0.5 },
  earring_stud_thickness: { min: 1.0, max: 3.0, step: 0.1 },
  earring_pin_length: { min: 8.0, max: 14.0, step: 0.5 },
  earring_pin_diameter: { min: 0.6, max: 1.2, step: 0.1 },
  // Side stone layout limits
  ssl_count: { min: 0, max: 60, step: 1 },
  ssl_diameter: { min: 1.0, max: 4.0, step: 0.1 },
  ssl_rows: { min: 1, max: 3, step: 1 },
} as const;
