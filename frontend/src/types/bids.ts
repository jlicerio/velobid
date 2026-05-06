/* ------------------------------------------------------------------ */
/*  Bid-related TypeScript types matching backend Pydantic schemas    */
/* ------------------------------------------------------------------ */

export interface GenerateBidRequest {
  project_id: string
  trade: string
  template_name?: string | null
  package_name?: 'all' | 'client' | 'internal'
  region?: string | null
  validate?: boolean
}

export interface LineItemResponse {
  cost_code: string
  description: string
  quantity: number
  unit: string
  unit_cost_material: number
  unit_cost_labor: number
  total_material: number
  total_labor: number
  total_phase: number
  labor_hours: number
  labor_factor: string
  sort_order: number
}

export interface BidTotalsResponse {
  total_material: number
  total_labor: number
  total_direct_cost: number
  contingency: number
  overhead_profit: number
  total_bid_amount: number
  total_labor_hours: number
  contingency_pct: number
  overhead_profit_pct: number
}

export interface ValidationIssueResponse {
  field: string
  message: string
}

export interface BidPreviewResponse {
  project_name: string
  bidder_name: string
  trade_name: string
  region: string
  status: string
  totals: BidTotalsResponse
  line_items: LineItemResponse[]
  exclusions: string[]
  validation: ValidationIssueResponse[]
}

export interface GeneratedFileResponse {
  filename: string
  path: string
  url: string
}

export interface GenerateBidResponse {
  preview: BidPreviewResponse
  generated_files: GeneratedFileResponse[]
}

/* ------------------------------------------------------------------ */
/*  Version snapshot types                                             */
/* ------------------------------------------------------------------ */

export interface CreateVersionRequest {
  trigger_source: 'user_edit' | 'ai_refine' | 'vision_import' | 'bulk_update'
  commit_message?: string | null
}

export interface TotalsDiff {
  from: number
  to: number
  delta: number
  delta_pct: number
}

export interface LineItemChange {
  cost_code: string
  description: string
  field: string
  from: unknown
  to: unknown
}

export interface VersionDiff {
  diff_type: string
  from_version: string | null
  to_version: string
  totals_changed: Record<string, TotalsDiff>
  line_items_changed: LineItemChange[]
  line_items_added: Record<string, unknown>[]
  line_items_removed: Record<string, unknown>[]
  summary: string
}

export interface SnapshotData {
  project_name: string
  trade_name: string
  totals: Record<string, unknown>
  line_items: Record<string, unknown>[]
  exclusions: string[]
}

export interface VersionMetadata {
  version_id: string
  timestamp: string
  commit_message: string
  trigger_source: string
  snapshot_summary?: string | null
}

export interface VersionListResponse {
  project_id: string
  trade: string
  versions: VersionMetadata[]
}

export interface VersionDetailResponse {
  version_id: string
  timestamp: string
  commit_message: string
  trigger_source: string
  snapshot_data: SnapshotData
  diff_from_previous: VersionDiff | null
}

export interface VersionDiffResponse {
  diff: VersionDiff | null
}

export interface CreateVersionResponse {
  version_id: string
  commit_message: string
  timestamp: string
  diff: VersionDiff | null
}

export interface RestoreVersionResponse {
  version_id: string
  project_name: string
  trade_name: string
  totals: Record<string, unknown>
  line_items: Record<string, unknown>[]
  exclusions: string[]
}

/* ------------------------------------------------------------------ */
/*  Trade / config summaries                                           */
/* ------------------------------------------------------------------ */

export interface ConfigSummary {
  id: string
  name: string
  path: string
}
