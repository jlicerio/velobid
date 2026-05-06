import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import type { Project } from "@/api/services/projects";
import { fetchProjectsWithPricing, archiveProject } from "@/api/services/projects";

export function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "active" | "archived">("all");
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
    } catch (e: any) {
      setError(e.message || "Failed to load projects");
    } finally {
      setLoading(false);
    }
  }

  async function handleArchive(projectId: string, archive: boolean) {
    try {
      await archiveProject(projectId, archive);
      await fetchProjects();
    } catch (e: any) {
      console.error("Archive failed:", e);
    }
  }

  const filtered = projects.filter((p) => {
    if (filter === "active") return !p.archived;
    if (filter === "archived") return p.archived;
    return true;
  });

  const money = (v?: number) => v != null ? `$${v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "—";

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Projects</h1>
          <p className="text-sm text-muted-foreground mt-0.5">{filtered.length} {filter === "all" ? "total" : filter} projects</p>
        </div>
        <button className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 shadow-sm">
          + New Project
        </button>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 mb-6 bg-muted/50 rounded-lg p-1 w-fit border">
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
              {f === "all" ? projects.length : projects.filter(p => f === "active" ? !p.archived : p.archived).length}
            </span>
          </button>
        ))}
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin h-8 w-8 border-[3px] border-primary border-t-transparent rounded-full" />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex flex-col items-center justify-center h-64 gap-4">
          <p className="text-destructive">Error: {error}</p>
          <button onClick={fetchProjects} className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm shadow-sm">
            Retry
          </button>
        </div>
      )}

      {/* Empty */}
      {!loading && !error && filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
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
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-2 gap-4">
          {filtered.map((project) => (
            <div
              key={project.id}
              className="border rounded-xl p-5 hover:shadow-lg hover:border-primary/20 transition-all duration-200 cursor-pointer bg-card group"
              onClick={() => navigate(`/projects/${project.id}`)}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="min-w-0">
                  <h3 className="font-semibold text-[15px] leading-tight group-hover:text-primary transition-colors">
                    {project.name}
                  </h3>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {(project.city || project.state) ? `${project.city || ""}, ${project.state || ""}` : project.trade || "—"}
                  </p>
                </div>
                {project.archived && (
                  <span className="text-[11px] bg-muted text-muted-foreground px-2 py-0.5 rounded-full shrink-0 ml-2">
                    Archived
                  </span>
                )}
              </div>

              {/* Pricing stats */}
              <div className="grid grid-cols-3 gap-3 mb-3">
                <div className="bg-muted/30 rounded-lg p-2.5">
                  <div className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider">Total Bid</div>
                  <div className="text-base font-bold mt-0.5">{money(project.total_bid)}</div>
                </div>
                <div className="bg-muted/30 rounded-lg p-2.5">
                  <div className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider">Labor</div>
                  <div className="text-base font-bold mt-0.5">{project.total_labor ? `${project.total_labor.toLocaleString()} hrs` : "—"}</div>
                </div>
                <div className="bg-muted/30 rounded-lg p-2.5">
                  <div className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider">Materials</div>
                  <div className="text-base font-bold mt-0.5">{money(project.total_material)}</div>
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between">
                <div className="flex gap-3 text-xs text-muted-foreground">
                  {project.area_sf ? <span>{project.area_sf.toLocaleString()} SF</span> : null}
                  {project.trade ? <span className="capitalize">{project.trade}</span> : null}
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); handleArchive(project.id, !project.archived); }}
                  className="text-xs px-2.5 py-1 rounded-md border hover:bg-accent transition-colors opacity-0 group-hover:opacity-100"
                >
                  {project.archived ? "Unarchive" : "Archive"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
