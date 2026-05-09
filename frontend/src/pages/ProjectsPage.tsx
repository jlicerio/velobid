import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import type { Project } from "@/api/services/projects";
import { fetchProjectsWithPricing, archiveProject, bulkArchiveProjects, exportPortfolioCsv } from "@/api/services/projects";
import { previewBid } from "@/api/services/bids";
import { ProjectStatusBadge } from "@/components/projects/project-status-badge";
import { Search, FolderKanban, BadgeDollarSign, Clock3, Layers3, Download } from "lucide-react";

export function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "active" | "archived">("all");
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<"name" | "bid" | "labor" | "hours" | "area">("name");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const navigate = useNavigate();

  useEffect(() => {
    fetchProjects();
  }, []);

  async function fetchProjects() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProjectsWithPricing();
      setProjects(data);
      void enrichLaborHours(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load projects");
    } finally {
      setLoading(false);
    }
  }

  async function enrichLaborHours(baseProjects: Project[]) {
    const needsHours = baseProjects.filter((project) => project.total_labor_hours == null)
    if (needsHours.length === 0) return

    type ProjectUpdate = {
      id: string
      total_bid?: number
      total_material?: number
      total_labor?: number
      total_labor_hours?: number
    }

    const updates = await Promise.all(
      needsHours.map(async (project) => {
        try {
          const preview = await previewBid(project.id, project.trade || "hvac")
          return {
            id: project.id,
            total_bid: preview.totals.total_bid_amount,
            total_material: preview.totals.total_material,
            total_labor: preview.totals.total_labor,
            total_labor_hours: preview.totals.total_labor_hours,
          }
        } catch {
          return null
        }
      })
    )

    const updateMap = new Map<string, ProjectUpdate>()
    for (const item of updates) {
      if (item) updateMap.set(item.id, item)
    }

    setProjects((current) =>
      current.map((project) => {
        const update = updateMap.get(project.id)
        return update ? { ...project, ...update } : project
      })
    )
  }

  async function handleArchive(projectId: string, archive: boolean) {
    try {
      await archiveProject(projectId, archive);
      await fetchProjects();
    } catch (e: unknown) {
      console.error("Archive failed:", e);
    }
  }

  function toggleSelection(id: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const filtered = projects.filter((p) => {
    if (filter === "active") return !p.archived;
    if (filter === "archived") return p.archived;
    return true;
  }).filter((project) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase().trim();
    return [
      project.name,
      project.city,
      project.state,
      project.trade,
      project.id,
    ].some((value) => (value || "").toLowerCase().includes(q));
  }).sort((a, b) => {
    switch (sortBy) {
      case "bid":
        return (b.total_bid || 0) - (a.total_bid || 0);
      case "labor":
        return (b.total_labor || 0) - (a.total_labor || 0);
      case "hours":
        return (b.total_labor_hours || 0) - (a.total_labor_hours || 0);
      case "area":
        return (b.area_sf || 0) - (a.area_sf || 0);
      case "name":
      default:
        return a.name.localeCompare(b.name);
    }
  });

  const allVisibleSelected = filtered.length > 0 && filtered.every((p) => selectedIds.has(p.id));

  function toggleSelectAll() {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (allVisibleSelected) {
        filtered.forEach((p) => next.delete(p.id));
      } else {
        filtered.forEach((p) => next.add(p.id));
      }
      return next;
    });
  }

  async function handleBulkArchive(archive: boolean) {
    if (selectedIds.size === 0) return;
    try {
      await bulkArchiveProjects(Array.from(selectedIds), archive);
      setSelectedIds(new Set());
      await fetchProjects();
    } catch (e: unknown) {
      console.error("Bulk archive failed:", e);
    }
  }

  const summary = projects.reduce(
    (acc, project) => {
      acc.total += 1;
      if (project.archived) acc.archived += 1;
      else acc.active += 1;
      acc.bid += project.total_bid || 0;
      acc.material += project.total_material || 0;
      acc.labor += project.total_labor || 0;
      acc.hours += project.total_labor_hours || 0;
      acc.area += project.area_sf || 0;
      return acc;
    },
    { total: 0, active: 0, archived: 0, bid: 0, material: 0, labor: 0, hours: 0, area: 0 }
  );

  const money = (v?: number) => v != null ? `$${v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "—";
  const statCards = [
    { label: "Projects", value: summary.total.toLocaleString(), icon: FolderKanban },
    { label: "Active", value: summary.active.toLocaleString(), icon: Layers3 },
    { label: "Total Bid", value: money(summary.bid), icon: BadgeDollarSign },
    { label: "Labor Hours", value: summary.hours.toLocaleString(undefined, { maximumFractionDigits: 1 }), icon: Clock3 },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Hero */}
      <div className="rounded-2xl border bg-gradient-to-br from-card via-card to-muted/20 p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-2xl">
            <p className="text-xs uppercase tracking-[0.35em] text-muted-foreground">Projects Dashboard</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight">Full project overview and management</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Track total bid value, labor hours, material spend, and project status across the whole portfolio.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button disabled title="Coming soon" className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium shadow-sm cursor-not-allowed opacity-60">
              + New Project
            </button>
          </div>
        </div>
      </div>

      {/* Overview cards */}
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        {statCards.map((stat) => {
          const Icon = stat.icon
          return (
            <div key={stat.label} className="rounded-xl border bg-card p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{stat.label}</p>
                <Icon className="h-4 w-4 text-primary/80" />
              </div>
              <div className="mt-3 text-2xl font-semibold tracking-tight">{stat.value}</div>
            </div>
          )
        })}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.5fr_0.85fr]">
        <div className="space-y-6">
          {/* Controls */}
          <div className="rounded-xl border bg-card p-4 shadow-sm space-y-4">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div className="relative flex-1 max-w-xl">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search projects, cities, trades, or IDs..."
                  className="w-full rounded-lg border bg-background py-2 pl-10 pr-3 text-sm outline-none ring-0 focus:border-primary"
                />
              </div>
              <div className="flex flex-wrap gap-2">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                  className="rounded-lg border bg-background px-3 py-2 text-sm"
                >
                  <option value="name">Sort: Name</option>
                  <option value="bid">Sort: Bid value</option>
                  <option value="labor">Sort: Labor cost</option>
                  <option value="hours">Sort: Labor hours</option>
                  <option value="area">Sort: Area</option>
                </select>
              </div>
            </div>

            {/* Filter tabs */}
            <div className="flex flex-wrap gap-1 bg-muted/50 rounded-lg p-1 w-fit border">
              {(["all", "active", "archived"] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
                    filter === f
                      ? "bg-background text-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                  <span className="ml-1.5 text-xs opacity-60">
                    {f === "all"
                      ? projects.length
                      : f === "active"
                      ? projects.filter((p) => !p.archived).length
                      : projects.filter((p) => p.archived).length}
                  </span>
                </button>
              ))}
            </div>

            {/* Selection controls */}
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <label className="flex items-center gap-2 text-sm cursor-pointer select-none">
                <input
                  type="checkbox"
                  className="h-4 w-4 accent-primary cursor-pointer"
                  checked={allVisibleSelected}
                  onChange={toggleSelectAll}
                />
                Select all visible
              </label>
              {selectedIds.size > 0 && (
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm text-muted-foreground">{selectedIds.size} selected</span>
                  <button
                    onClick={() => handleBulkArchive(true)}
                    className="text-xs px-2.5 py-1.5 rounded-md border hover:bg-accent transition-colors"
                  >
                    Archive selected
                  </button>
                  <button
                    onClick={() => handleBulkArchive(false)}
                    className="text-xs px-2.5 py-1.5 rounded-md border hover:bg-accent transition-colors"
                  >
                    Unarchive selected
                  </button>
                  <button
                    onClick={() => setSelectedIds(new Set())}
                    className="text-xs px-2.5 py-1.5 rounded-md border hover:bg-accent transition-colors text-muted-foreground"
                  >
                    Clear
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Loading */}
          {loading && (
            <div className="flex items-center justify-center h-64 rounded-xl border bg-card">
              <div className="animate-spin h-8 w-8 border-[3px] border-primary border-t-transparent rounded-full" />
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="flex flex-col items-center justify-center h-64 gap-4 rounded-xl border bg-card">
              <p className="text-destructive">Error: {error}</p>
              <button onClick={fetchProjects} className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm shadow-sm">
                Retry
              </button>
            </div>
          )}

          {/* Empty */}
          {!loading && !error && filtered.length === 0 && (
            <div className="flex flex-col items-center justify-center h-64 text-muted-foreground rounded-xl border bg-card">
              <p className="text-lg mb-2">
                {filter === "all" ? "No projects yet" : filter === "active" ? "No active projects" : "No archived projects"}
              </p>
              <button className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm shadow-sm">
                Create your first project
              </button>
            </div>
          )}

          {/* Project Grid */}
          {!loading && !error && filtered.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {filtered.map((project) => (
                <div
                  key={project.id}
                  className="group cursor-pointer rounded-xl border bg-card p-5 transition-all duration-200 hover:border-primary/20 hover:shadow-lg"
                  onClick={() => navigate(`/projects/${project.id}`)}
                >
                  <div className="mb-3 flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3 min-w-0">
                      <input
                        type="checkbox"
                        className="mt-1 h-4 w-4 accent-primary cursor-pointer shrink-0"
                        checked={selectedIds.has(project.id)}
                        onClick={(e) => e.stopPropagation()}
                        onChange={() => toggleSelection(project.id)}
                      />
                      <div className="min-w-0">
                        <h3 className="font-semibold text-[15px] leading-tight group-hover:text-primary transition-colors">
                          {project.name}
                        </h3>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {(project.city || project.state) ? `${project.city || ""}, ${project.state || ""}` : project.trade || "—"}
                        </p>
                      </div>
                    </div>
                    <div className="flex flex-wrap items-center justify-end gap-2 shrink-0 ml-2">
                      <ProjectStatusBadge status={project.status} archived={project.archived} />
                    </div>
                  </div>

                  <div className="mb-4 grid grid-cols-2 gap-2.5 sm:gap-3">
                    <div className="rounded-lg border bg-muted/25 p-3">
                      <div className="text-[10px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
                        Total Bid
                      </div>
                      <div className="mt-1 text-lg font-semibold tracking-tight">{money(project.total_bid)}</div>
                    </div>
                    <div className="rounded-lg border bg-muted/25 p-3">
                      <div className="text-[10px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
                        {project.total_labor_hours != null ? "Labor Hours" : "Labor Cost"}
                      </div>
                      <div className="mt-1 text-lg font-semibold tracking-tight">
                        {project.total_labor_hours != null
                          ? `${project.total_labor_hours.toLocaleString()} hrs`
                          : money(project.total_labor)}
                      </div>
                    </div>
                    <div className="rounded-lg border bg-muted/25 p-3">
                      <div className="text-[10px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
                        Materials
                      </div>
                      <div className="mt-1 text-lg font-semibold tracking-tight">{money(project.total_material)}</div>
                    </div>
                    <div className="rounded-lg border bg-muted/25 p-3">
                      <div className="text-[10px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
                        Area
                      </div>
                      <div className="mt-1 text-lg font-semibold tracking-tight">
                        {project.area_sf ? `${project.area_sf.toLocaleString()} SF` : "—"}
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      {project.trade ? <span className="rounded-full border bg-muted/30 px-2 py-1 capitalize">{project.trade}</span> : null}
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={(e) => { e.stopPropagation(); navigate(`/projects/${project.id}`); }}
                        className="text-xs px-2.5 py-1 rounded-md border hover:bg-accent transition-colors"
                      >
                        Open
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleArchive(project.id, !project.archived); }}
                        className="text-xs px-2.5 py-1 rounded-md border hover:bg-accent transition-colors"
                      >
                        {project.archived ? "Unarchive" : "Archive"}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Management tools */}
        <aside className="space-y-4">
          <div className="rounded-xl border bg-card p-4 shadow-sm">
            <h2 className="text-sm font-semibold">Export</h2>
            <p className="mt-1 text-xs text-muted-foreground">
              Download the current portfolio data.
            </p>
            <div className="mt-4">
              <button
                onClick={exportPortfolioCsv}
                className="w-full flex items-center justify-between rounded-lg border px-3 py-2 text-sm hover:bg-accent"
              >
                <span className="flex items-center gap-2"><Download className="h-4 w-4" /> Export CSV</span>
                <span className="text-xs text-muted-foreground">Summary</span>
              </button>
            </div>
          </div>


        </aside>
      </div>
    </div>
  );
}
