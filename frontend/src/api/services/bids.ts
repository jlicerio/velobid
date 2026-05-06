import { apiFetch } from "@/lib/api/client"
import type { BidPreviewResponse, GenerateBidResponse } from "@/types"

export async function previewBid(
  projectId: string,
  trade: string,
): Promise<BidPreviewResponse> {
  return apiFetch<BidPreviewResponse>("/bids/preview", {
    method: "POST",
    body: { project_id: projectId, trade },
  })
}

export async function generateBid(
  projectId: string,
  trade: string,
  pkg: string,
): Promise<GenerateBidResponse> {
  return apiFetch<GenerateBidResponse>("/bids/generate", {
    method: "POST",
    body: { project_id: projectId, trade, package_name: pkg },
  })
}
