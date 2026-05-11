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
  status?: string
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
  try {
    const response = await apiFetch<Response>("/projects/export/csv", { rawResponse: true })
    if (!response.ok) throw new Error(`Export failed: ${response.status}`)
    const blob = await response.blob()
    if (blob.size === 0) throw new Error("Export returned empty data")
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "portfolio-summary.csv"
    a.style.display = "none"
    document.body.appendChild(a)
    a.click()
    setTimeout(() => {
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    }, 1000)
  } catch (err) {
    console.error("CSV export failed:", err)
    alert(err instanceof Error ? err.message : "CSV export failed. Please try again.")
  }
}
