import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

type ProjectStatusBadgeProps = {
  status?: string | null
  archived?: boolean
  className?: string
}

const STATUS_META: Record<string, { label: string; className: string }> = {
  draft: {
    label: "Draft",
    className: "border-slate-500/30 bg-slate-500/10 text-slate-200 dark:text-slate-300",
  },
  estimating: {
    label: "Estimating",
    className: "border-amber-500/30 bg-amber-500/10 text-amber-200 dark:text-amber-300",
  },
  pending_clarification: {
    label: "Pending Clarification",
    className: "border-sky-500/30 bg-sky-500/10 text-sky-200 dark:text-sky-300",
  },
  ready_to_submit: {
    label: "Ready to Submit",
    className: "border-indigo-500/30 bg-indigo-500/10 text-indigo-200 dark:text-indigo-300",
  },
  submitted: {
    label: "Submitted",
    className: "border-cyan-500/30 bg-cyan-500/10 text-cyan-200 dark:text-cyan-300",
  },
  won: {
    label: "Won",
    className: "border-emerald-500/30 bg-emerald-500/10 text-emerald-200 dark:text-emerald-300",
  },
  lost: {
    label: "Lost",
    className: "border-rose-500/30 bg-rose-500/10 text-rose-200 dark:text-rose-300",
  },
  on_hold: {
    label: "On Hold",
    className: "border-zinc-500/30 bg-zinc-500/10 text-zinc-200 dark:text-zinc-300",
  },
  archived: {
    label: "Archived",
    className: "border-muted-foreground/30 bg-muted/70 text-muted-foreground",
  },
}

function normalizeStatus(status?: string | null) {
  if (!status) return "estimating"
  const clean = status.trim().toLowerCase().replace(/\s+/g, "_")
  if (clean === "estimate") return "estimating"
  return clean
}

export function formatProjectStatus(status?: string | null, archived?: boolean) {
  if (archived) return STATUS_META.archived.label
  const normalized = normalizeStatus(status)
  return STATUS_META[normalized]?.label || normalized.replace(/_/g, " ")
}

export function ProjectStatusBadge({ status, archived = false, className }: ProjectStatusBadgeProps) {
  const normalized = normalizeStatus(status)
  const meta = STATUS_META[normalized] || STATUS_META.estimating

  return (
    <Badge
      variant="outline"
      className={cn("rounded-full border px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-[0.18em]", meta.className, archived && "opacity-90", className)}
    >
      {meta.label}
    </Badge>
  )
}
