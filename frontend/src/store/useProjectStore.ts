/**
 * Zustand store — single source of truth for project state.
 *
 * Key invariant: After initial parse, the image parser is never re-invoked.
 * All customizations mutate currentParams and trigger rebuild/budget only.
 */

import { create } from "zustand";
import { temporal } from "zundo";
import type {
  BudgetEstimate,
  Customization,
  ParametricRing,
  ParseResult,
  ValidationResult,
} from "../types/jewelry";

export interface ProjectState {
  // ── Identity ────────────────────────────────────────────────
  projectId: string | null;
  sourceImage: File | null;

  // ── Parse result (immutable after parse) ────────────────────
  parseResult: ParseResult | null;

  // ── Mutable working copy ────────────────────────────────────
  currentParams: ParametricRing;
  customization: Customization;

  // ── Async results ───────────────────────────────────────────
  buildId: string | null;
  modelUrl: string | null; // GLB URL loaded in viewport
  budgetResult: BudgetEstimate | null;
  validationResult: ValidationResult | null;

  // ── UI state ────────────────────────────────────────────────
  isParsing: boolean;
  isBuilding: boolean;
  buildError: string | null;

  // ── Actions ─────────────────────────────────────────────────
  setProject: (id: string, parse: ParseResult, custom: Customization) => void;
  setSourceImage: (file: File) => void;
  updateParams: (partial: Partial<ParametricRing>) => void;
  updateStone: (partial: Partial<ParametricRing["center_stone"]>) => void;
  updateCustomization: (partial: Partial<Customization>) => void;
  setBuildResult: (buildId: string, glbUrl: string | null, validation: ValidationResult) => void;
  setBudgetResult: (result: BudgetEstimate | null) => void;
  setIsParsing: (v: boolean) => void;
  setIsBuilding: (v: boolean) => void;
  setBuildError: (e: string | null) => void;
  replaceParams: (params: ParametricRing) => void;
  setParseFailure: () => void;
  reset: () => void;
}

const DEFAULT_PARAMS: ParametricRing = {
  type: "ring",
  ring_radius: 9.0,
  band_width: 2.2,
  band_thickness: 1.8,
  center_stone: { type: "round", diameter: 6.0, height: 3.6, prongs: 4 },
  setting_type: "prong",
  setting_style: "solitaire",
  side_stones: [],
  side_stone_layout: null,
  pendant_params: {
    base_shape: "circular",
    base_width: 15.0,
    base_height: 20.0,
    base_thickness: 2.0,
    bail_diameter: 5.0,
    bail_thickness: 1.5,
  },
  earring_params: {
    stud_diameter: 6.0,
    stud_thickness: 1.5,
    pin_length: 10.0,
    pin_diameter: 0.8,
  },
};

const DEFAULT_CUSTOM: Customization = {
  metal_type: "18k_gold",
  gemstone_material: "diamond",
  side_stone_material: "diamond",
  target_budget: null,
};

export const useProjectStore = create<ProjectState>()(
  temporal(
  (set) => ({
  projectId: null,
  sourceImage: null,
  parseResult: null,
  currentParams: { ...DEFAULT_PARAMS },
  customization: { ...DEFAULT_CUSTOM },
  buildId: null,
  modelUrl: null,
  budgetResult: null,
  validationResult: null,
  isParsing: false,
  isBuilding: false,
  buildError: null,

  setProject: (id, parse, custom) =>
    set({
      projectId: id,
      parseResult: parse,
      currentParams: { ...parse.params },
      customization: custom,
      buildError: null,
    }),

  setSourceImage: (file) => set({ sourceImage: file }),

  updateParams: (partial) =>
    set((s) => ({
      currentParams: { ...s.currentParams, ...partial },
    })),

  updateStone: (partial) =>
    set((s) => ({
      currentParams: {
        ...s.currentParams,
        center_stone: { ...s.currentParams.center_stone, ...partial },
      },
    })),

  updateCustomization: (partial) =>
    set((s) => ({
      customization: { ...s.customization, ...partial },
    })),

  setBuildResult: (buildId, glbUrl, validation) =>
    set({ buildId, modelUrl: glbUrl, validationResult: validation, isBuilding: false, buildError: null }),

  setBudgetResult: (result) => set({ budgetResult: result }),

  setIsParsing: (v) => set({ isParsing: v }),
  setIsBuilding: (v) => set({ isBuilding: v }),
  setBuildError: (e) => set({ buildError: e, isBuilding: false }),

  replaceParams: (params) => set({ currentParams: params }),

  setParseFailure: () =>
    set({
      parseResult: {
        params: { ...DEFAULT_PARAMS },
        confidence_score: 0,
        band_confidence: 0,
        stone_confidence: 0,
        setting_confidence: 0,
        symmetry_confidence: 0,
        detections: [],
      },
      currentParams: { ...DEFAULT_PARAMS },
      customization: { ...DEFAULT_CUSTOM },
      isParsing: false,
      buildError: null,
    }),

  reset: () =>
    set({
      projectId: null,
      sourceImage: null,
      parseResult: null,
      currentParams: { ...DEFAULT_PARAMS },
      customization: { ...DEFAULT_CUSTOM },
      buildId: null,
      modelUrl: null,
      budgetResult: null,
      validationResult: null,
      isParsing: false,
      isBuilding: false,
      buildError: null,
    }),
}),
  {
    // Only track param + customization changes for undo/redo (not UI state)
    partialize: (state) => ({
      currentParams: state.currentParams,
      customization: state.customization,
    }),
    limit: 50,
  }
));
