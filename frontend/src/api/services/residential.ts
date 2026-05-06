import { apiFetch } from "@/lib/api/client"

export async function createEstimate(data: any): Promise<any> {
  return apiFetch<any>("/residential/estimate", { method: "POST", body: data })
}
