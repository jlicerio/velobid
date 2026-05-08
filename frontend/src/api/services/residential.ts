import { apiFetch } from "@/lib/api/client"

export interface ResidentialEquipmentItem {
  item: string
  brand?: string
  model?: string
  tons?: number
  btu?: number
  cost: number
  qty?: number
}

export interface ResidentialLaborTask {
  item: string
  hours: number
  qty?: number
}

export interface CreateResidentialEstimateRequest {
  customer_name: string
  customer_address: string
  customer_phone?: string
  customer_email?: string
  property_sqft?: number
  scope_description: string
  equipment?: ResidentialEquipmentItem[]
  labor_tasks?: ResidentialLaborTask[]
  misc_materials?: number
  permit_fee?: number
  equipment_markup_pct?: number
  labor_rate?: number
  generate_pdf?: boolean
}

export interface ResidentialEstimateTotals {
  equipment_total?: number
  labor_total?: number
  labor_hours?: number
  misc_materials?: number
  permit_fee?: number
  subtotal?: number
  tax?: number
  tax_rate?: number
  equipment_markup_pct?: number
  labor_rate?: number
  grand_total?: number
  [key: string]: number | undefined
}

export interface ResidentialEstimateLineItem {
  type: string
  description: string
  detail?: string
  cost?: number
  markup?: number
  total: number
  hours?: number
  rate?: number
}

export interface ResidentialEstimateResponse {
  project_id: string
  customer_name: string
  grand_total: number
  pdf_url?: string | null
  totals: ResidentialEstimateTotals
  line_items: ResidentialEstimateLineItem[]
}

export async function createEstimate(
  data: CreateResidentialEstimateRequest,
): Promise<ResidentialEstimateResponse> {
  return apiFetch<ResidentialEstimateResponse>("/residential/estimate", { method: "POST", body: data })
}
