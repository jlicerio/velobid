import { apiFetch } from "@/lib/api/client"

export interface CompanySettings {
  name: string
  address: string
  phone: string
  email: string
  license_number: string
}

export interface PricingSettings {
  default_contingency_pct: number
  default_overhead_profit_pct: number
  default_equipment_markup_pct: number
  default_labor_rate: number
  default_tax_rate: number
  default_permit_fee: number
  default_misc_material_pct: number
}

export interface AgentSettings {
  model: string
  temperature: number
  company_context: string
}

export interface SettingsResponse {
  company: CompanySettings
  pricing: PricingSettings
  agent: AgentSettings
}

export interface PatchSettingsResponse {
  ok: true
  settings: SettingsResponse
}

export async function fetchSettings(): Promise<SettingsResponse> {
  return apiFetch<SettingsResponse>("/settings")
}

export async function patchSettings(
  body: unknown,
): Promise<PatchSettingsResponse> {
  return apiFetch<PatchSettingsResponse>("/settings", {
    method: "PATCH",
    body,
  })
}
