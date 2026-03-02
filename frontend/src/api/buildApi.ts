import client from "./client";
import type {
  BuildResponse,
  Customization,
  ParametricRing,
} from "../types/jewelry";

export async function buildRing(
  params: ParametricRing,
  customization: Customization,
  projectId?: string
): Promise<BuildResponse> {
  const { data } = await client.post<BuildResponse>("/build", {
    project_id: projectId ?? null,
    params,
    customization,
  });
  return data;
}
