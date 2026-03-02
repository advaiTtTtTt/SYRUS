/**
 * Debounced build trigger hook.
 *
 * After any param change, waits 300ms then fires:
 *   - POST /api/build (geometry + validation)
 *   - POST /api/budget/estimate (cost) — in parallel
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

  const timerRef = useRef<ReturnType<typeof setTimeout>>();
  const abortRef = useRef<AbortController>();

  const triggerBuild = useCallback(() => {
    // Cancel previous
    if (timerRef.current) clearTimeout(timerRef.current);
    if (abortRef.current) abortRef.current.abort();

    timerRef.current = setTimeout(async () => {
      setIsBuilding(true);
      abortRef.current = new AbortController();

      try {
        // Fire build + budget estimate in parallel
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

  // Auto-trigger on param/customization changes (including initial mount)
  useEffect(() => {
    triggerBuild();
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [currentParams, customization]); // eslint-disable-line react-hooks/exhaustive-deps

  return { triggerBuild };
}
