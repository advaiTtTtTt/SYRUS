import client from "./client";
import type { ParseResult, Customization } from "../types/jewelry";

export interface ParseResponse {
  project_id: string;
  parse_result: ParseResult;
  customization: Customization;
}

export async function parseImage(file: File): Promise<ParseResponse> {
  const form = new FormData();
  form.append("file", file);

  const { data } = await client.post<ParseResponse>("/parse", form, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 60_000, // parsing can be slow
  });

  return data;
}
