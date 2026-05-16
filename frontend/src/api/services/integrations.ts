import { apiFetch } from "@/lib/api/client"

export interface IntegrationStatus {
  toolkit: string
  status: "connected" | "not_connected" | "not_configured" | "not_available"
  connect_url: string | null
}

export interface ConnectionListResponse {
  bidder_id: string
  integrations: IntegrationStatus[]
}

export interface OAuthInitiateRequest {
  toolkit: string
  bidder_id: string
}

export interface OAuthInitiateResponse {
  toolkit: string
  redirect_url: string | null
}

export interface DisconnectResponse {
  bidder_id: string
  toolkit: string
  status: string
}

const TOOLKIT_LABELS: Record<string, string> = {
  GMAIL: "Gmail",
  GOOGLE_DRIVE: "Google Drive",
}

const TOOLKIT_ICONS: Record<string, string> = {
  GMAIL: "✉️",
  GOOGLE_DRIVE: "📁",
}

export function getToolkitLabel(toolkit: string): string {
  return TOOLKIT_LABELS[toolkit] || toolkit
}

export function getToolkitIcon(toolkit: string): string {
  return TOOLKIT_ICONS[toolkit] || "🔌"
}

export async function fetchIntegrationStatus(
  bidderId: string,
): Promise<ConnectionListResponse> {
  return apiFetch<ConnectionListResponse>(
    `/integrations/status?bidder_id=${encodeURIComponent(bidderId)}`,
  )
}

export async function initiateOAuth(
  body: OAuthInitiateRequest,
): Promise<OAuthInitiateResponse> {
  return apiFetch<OAuthInitiateResponse>("/integrations/connect", {
    method: "POST",
    body,
  })
}

export async function disconnectIntegration(
  body: OAuthInitiateRequest,
): Promise<DisconnectResponse> {
  return apiFetch<DisconnectResponse>("/integrations/disconnect", {
    method: "POST",
    body,
  })
}
