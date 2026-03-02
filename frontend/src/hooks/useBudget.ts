/**
 * Budget hook — handles budget adjustment flow.
 */

import { useCallback } from "react";
import { adjustBudget } from "../api/budgetApi";
import { useProjectStore } from "../store/useProjectStore";

export function useBudget() {
  const { currentParams, customization, replaceParams, updateCustomization } =
    useProjectStore();

  const applyBudgetAdjustment = useCallback(
    async (targetBudget: number) => {
      const result = await adjustBudget(currentParams, customization, targetBudget);

      if (result.budget_fit) {
        // Replace params with adjusted version — triggers rebuild via useBuild
        replaceParams(result.adjusted_params);
      }

      return result;
    },
    [currentParams, customization, replaceParams, updateCustomization]
  );

  return { applyBudgetAdjustment };
}
