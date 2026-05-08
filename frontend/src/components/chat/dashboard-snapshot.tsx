import { useState, type ReactNode } from "react"
import {
  Archive,
  ChevronDown,
  ChevronUp,
  Clock3,
  DollarSign,
  LayoutDashboard,
  TrendingUp,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import type { DashboardSnapshot as DashboardSnapshotType } from "@/lib/dashboard-context"
import { formatCurrency, formatNumber } from "@/lib/dashboard-context"

interface DashboardSnapshotCardProps {
  snapshot: DashboardSnapshotType
  className?: string
}

function MetricPill({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div className="rounded-full border border-border/70 bg-background/80 px-3 py-1 text-[11px] text-muted-foreground shadow-sm">
      <span className="font-medium text-foreground">{value}</span>{" "}
      <span className="text-muted-foreground">{label}</span>
    </div>
  )
}

function MetricCard({
  icon,
  label,
  value,
  detail,
}: {
  icon: ReactNode
  label: string
  value: string
  detail: string
}) {
  return (
    <div className="rounded-2xl border border-border/70 bg-background/70 p-3 shadow-sm">
      <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
        <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-primary">
          {icon}
        </span>
        {label}
      </div>
      <p className="mt-3 text-2xl font-semibold tracking-tight text-foreground">{value}</p>
      <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{detail}</p>
    </div>
  )
}

export function DashboardSnapshotCard({
  snapshot,
  className,
}: DashboardSnapshotCardProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <Card
      className={cn(
        "mx-4 mt-3 overflow-hidden border-primary/10 bg-gradient-to-br from-primary/8 via-card to-card shadow-sm",
        className,
      )}
    >
      <CardContent className="p-4">
        <button
          type="button"
          onClick={() => setExpanded((value) => !value)}
          className="flex w-full items-start gap-3 text-left"
          aria-expanded={expanded}
        >
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary ring-1 ring-primary/10">
            <LayoutDashboard className="h-5 w-5" />
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-[10px] uppercase tracking-[0.28em] text-muted-foreground">
                Dashboard context
              </p>
              <Badge
                variant="outline"
                className="border-primary/20 bg-background/80 text-[10px] uppercase tracking-[0.18em] text-primary"
              >
                Hidden from chat
              </Badge>
            </div>

            <div className="mt-1 flex flex-wrap items-center gap-2">
              <span className="text-sm font-semibold text-foreground">
                Portfolio snapshot
              </span>
              <span className="text-xs text-muted-foreground">
                {snapshot.totalProjects} projects · {snapshot.activeProjects} active ·{" "}
                {snapshot.archivedProjects} archived
              </span>
            </div>

            <div className="mt-2 flex flex-wrap gap-2">
              <MetricPill label="bid total" value={formatCurrency(snapshot.totalBid)} />
              <MetricPill label="labor hrs" value={formatNumber(snapshot.totalLaborHours)} />
              <MetricPill label="materials" value={formatCurrency(snapshot.totalMaterial)} />
            </div>
          </div>

          <span className="mt-1 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-border bg-background text-muted-foreground">
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </span>
        </button>

        {expanded && (
          <div className="mt-4 grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)]">
            <div className="grid grid-cols-2 gap-2">
              <MetricCard
                icon={<TrendingUp className="h-3.5 w-3.5" />}
                label="Active"
                value={formatNumber(snapshot.activeProjects)}
                detail="Currently live in the pipeline"
              />
              <MetricCard
                icon={<Archive className="h-3.5 w-3.5" />}
                label="Archived"
                value={formatNumber(snapshot.archivedProjects)}
                detail="Still available for reference"
              />
              <MetricCard
                icon={<Clock3 className="h-3.5 w-3.5" />}
                label="Labor hours"
                value={formatNumber(snapshot.totalLaborHours)}
                detail="Across the current portfolio"
              />
              <MetricCard
                icon={<DollarSign className="h-3.5 w-3.5" />}
                label="Materials"
                value={formatCurrency(snapshot.totalMaterial)}
                detail="Material cost across all projects"
              />
            </div>

            <div className="rounded-2xl border border-border/70 bg-background/70 p-3 shadow-sm">
              <div className="flex items-center justify-between gap-2">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                  Top projects
                </p>
                <p className="text-[11px] text-muted-foreground">
                  {snapshot.topProjects.length} shown
                </p>
              </div>

              <div className="mt-3 space-y-2">
                {snapshot.topProjects.length === 0 ? (
                  <p className="rounded-xl border border-dashed border-border/70 bg-muted/20 px-3 py-4 text-sm text-muted-foreground">
                    No projects available yet.
                  </p>
                ) : (
                  snapshot.topProjects.map((project, index) => (
                    <div
                      key={project.id}
                      className="flex items-start gap-3 rounded-xl border border-border/60 bg-muted/30 px-3 py-2"
                    >
                      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[11px] font-semibold text-primary">
                        {index + 1}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-foreground">
                          {project.name}
                        </p>
                        <p className="truncate text-[11px] text-muted-foreground">
                          {project.trade} · {project.location}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-[11px] font-medium text-foreground">
                          {formatCurrency(project.totalBid)}
                        </p>
                        <p className="text-[11px] text-muted-foreground">
                          {formatNumber(project.totalLaborHours)} hrs
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
