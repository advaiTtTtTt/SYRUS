import client from "./client";
import type {
  BudgetAdjustment,
  BudgetEstimate,
  Customization,
  ParametricRing,
} from "../types/jewelry";

export async function estimateCost(
  params: ParametricRing,
  customization: Customization
): Promise<BudgetEstimate> {
  const { data } = await client.post<BudgetEstimate>("/budget/estimate", {
    params,
    customization,
  });
  return data;
}

export async function adjustBudget(
  params: ParametricRing,
  customization: Customization,
  targetBudget: number
): Promise<BudgetAdjustment> {
  const { data } = await client.post<BudgetAdjustment>("/budget/adjust", {
    params,
    customization,
    target_budget: targetBudget,
  });
  return data;
}
