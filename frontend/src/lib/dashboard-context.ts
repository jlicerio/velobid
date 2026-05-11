import { fetchProjectsWithPricing, type Project } from "@/api/services/projects"

export interface DashboardTopProject {
  id: string
  name: string
  trade: string
  location: string
  totalBid: number
  totalLaborHours: number
}

export interface DashboardSnapshot {
  totalProjects: number
  activeProjects: number
  archivedProjects: number
  totalBid: number
  totalLaborHours: number
  totalMaterial: number
  topProjects: DashboardTopProject[]
}

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
})

const numberFormatter = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 1,
})

export function formatCurrency(value: number) {
  return currencyFormatter.format(value)
}

export function formatNumber(value: number) {
  return numberFormatter.format(value)
}

function formatLocation(project: Project) {
  const parts = [project.city, project.state].filter(Boolean)
  return parts.length > 0 ? parts.join(", ") : "Location unavailable"
}

function summarizeProjects(projects: Project[]): DashboardSnapshot {
  const activeProjects = projects.filter((project) => !project.archived)
  const archivedProjects = projects.filter((project) => project.archived)
  const totalBid = projects.reduce((sum, project) => sum + (project.total_bid || 0), 0)
  const totalLaborHours = projects.reduce(
    (sum, project) => sum + (project.total_labor_hours || 0),
    0,
  )
  const totalMaterial = projects.reduce(
    (sum, project) => sum + (project.total_material || 0),
    0,
  )

  const topProjects = [...projects]
    .sort((a, b) => (b.total_bid || 0) - (a.total_bid || 0))
    .slice(0, 4)
    .map((project) => ({
      id: project.id,
      name: project.name,
      trade: project.trade || "unknown",
      location: formatLocation(project),
      totalBid: project.total_bid || 0,
      totalLaborHours: project.total_labor_hours || 0,
    }))

  return {
    totalProjects: projects.length,
    activeProjects: activeProjects.length,
    archivedProjects: archivedProjects.length,
    totalBid,
    totalLaborHours,
    totalMaterial,
    topProjects,
  }
}

export async function loadDashboardSnapshot(): Promise<DashboardSnapshot | null> {
  try {
    const projects = await fetchProjectsWithPricing()
    return summarizeProjects(projects)
  } catch {
    return null
  }
}

export function buildDashboardContext(snapshot: DashboardSnapshot) {
  const topProjects = snapshot.topProjects
    .map(
      (project) =>
        `- ${project.name} | ${project.trade} | ${project.location} | bid ${formatCurrency(project.totalBid)} | labor ${formatNumber(project.totalLaborHours)} hrs`,
    )
    .join("\n")

  return [
    "# VeloBid Portfolio Context",
    "",
    "You are helping the user manage the full VeloBid projects dashboard.",
    "Answer using the portfolio context below when the user asks about projects, totals, status, labor hours, or management actions.",
    "",
    "## Summary",
    `- Projects total: ${snapshot.totalProjects}`,
    `- Active projects: ${snapshot.activeProjects}`,
    `- Archived projects: ${snapshot.archivedProjects}`,
    "",
    "## Totals",
    `- Bid total: ${formatCurrency(snapshot.totalBid)}`,
    `- Labor hours: ${formatNumber(snapshot.totalLaborHours)}`,
    `- Materials: ${formatCurrency(snapshot.totalMaterial)}`,
    "",
    "## Top Projects",
    topProjects,
    "",
    "## Response Rules",
    "- If the user asks for an overview, summarize the portfolio.",
    "- If they ask for a project-specific detail, ask which project they mean or use the best matching project from the current view.",
    "- Prefer short sections, bullets, and tables where they make the answer easier to scan.",
  ].join("\n")
}
