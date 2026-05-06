import { apiFetch } from "@/lib/api/client"

export interface Project {
  id: string
  name: string
  total_bid?: number
  total_material?: number
  total_labor?: number
  area_sf?: number
  trade?: string
  archived?: boolean
  city?: string
  state?: string
}

export async function fetchProjectsWithPricing(): Promise<Project[]> {
  return apiFetch<Project[]>("/projects/with-pricing")
}

export async function archiveProject(id: string, archive: boolean): Promise<void> {
  const action = archive ? "archive" : "unarchive"
  return apiFetch<void>(`/projects/${id}/${action}`, { method: "PATCH" })
}
