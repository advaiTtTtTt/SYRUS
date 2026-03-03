/**
 * Debounced build trigger hook.
 *
 * Separates material-only changes from geometry changes:
 *   - Geometry changes (currentParams) → full rebuild + budget estimate
 *   - Material changes (metal/gem) → budget estimate only (shader swap is instant)
 *   - Budget target change → budget adjustment (may alter params → full rebuild)
 *
 * Cancels in-flight requests on new changes (AbortController).
 */

import { useCallback, useEffect, useRef } from "react";
import { buildRing } from "../api/buildApi";
import { estimateCost } from "../api/budgetApi";
import { useProjectStore } from "../store/useProjectStore";

const DEBOUNCE_MS = 300;

export function useBuild() {
  const {
    currentParams,
    customization,
    projectId,
    setIsBuilding,
    setBuildResult,
    setBudgetResult,
    setBuildError,
  } = useProjectStore();

  // Track type to detect type changes
  const prevTypeRef = useRef(currentParams.type);

  const timerRef = useRef<ReturnType<typeof setTimeout>>();
  const abortRef = useRef<AbortController>();
  const budgetTimerRef = useRef<ReturnType<typeof setTimeout>>();

  // Full geometry rebuild + budget estimate
  const triggerBuild = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (abortRef.current) abortRef.current.abort();

    timerRef.current = setTimeout(async () => {
      setIsBuilding(true);
      abortRef.current = new AbortController();

      try {
        const [buildRes, budgetRes] = await Promise.all([
          buildRing(currentParams, customization, projectId ?? undefined),
          estimateCost(currentParams, customization),
        ]);

        setBuildResult(
          buildRes.build_id,
          buildRes.model_glb_url,
          buildRes.validation
        );
        setBudgetResult(budgetRes);
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        const msg = err instanceof Error ? err.message : "Build failed";
        setBuildError(msg);
      }
    }, DEBOUNCE_MS);
  }, [currentParams, customization, projectId, setIsBuilding, setBuildResult, setBudgetResult, setBuildError]);

  // Budget-only re-estimate (material swap — no geometry rebuild)
  const triggerBudgetOnly = useCallback(() => {
    if (budgetTimerRef.current) clearTimeout(budgetTimerRef.current);

    budgetTimerRef.current = setTimeout(async () => {
      try {
        const budgetRes = await estimateCost(currentParams, customization);
        setBudgetResult(budgetRes);
      } catch {
        // Budget estimate failure is non-fatal
      }
    }, DEBOUNCE_MS);
  }, [currentParams, customization, setBudgetResult]);

  // Trigger full rebuild when geometry params change
  useEffect(() => {
    // If jewelry type changed, clear stale model so fallback renders immediately
    if (prevTypeRef.current !== currentParams.type) {
      prevTypeRef.current = currentParams.type;
      useProjectStore.setState({ modelUrl: null });
    }
    triggerBuild();
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [currentParams]); // eslint-disable-line react-hooks/exhaustive-deps

  // Material/gem changes → budget only (shaders update reactively in RingModel)
  useEffect(() => {
    triggerBudgetOnly();
    return () => {
      if (budgetTimerRef.current) clearTimeout(budgetTimerRef.current);
    };
  }, [customization.metal_type, customization.gemstone_material, customization.side_stone_material]); // eslint-disable-line react-hooks/exhaustive-deps

  return { triggerBuild };
}
