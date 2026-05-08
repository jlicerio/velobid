import { apiFetch } from "@/lib/api/client"

export interface Project {
  id: string
  name: string
  total_bid?: number
  total_material?: number
  total_labor?: number
  total_labor_hours?: number
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

export async function bulkArchiveProjects(ids: string[], archive: boolean): Promise<void> {
  return apiFetch<void>("/projects/bulk-archive", {
    method: "POST",
    body: { ids, archived: archive },
  })
}

export async function exportPortfolioCsv(): Promise<void> {
  const response = await apiFetch<Response>("/projects/export/csv")
  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = "portfolio-summary.csv"
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}
