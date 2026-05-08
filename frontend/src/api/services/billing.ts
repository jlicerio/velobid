import { apiFetch } from '../../lib/api/client'

export interface BillingStatus {
  configured: boolean
  customer_id?: string | null
  subscription_id?: string | null
  subscription_status?: string | null
  price_id?: string | null
  trial_ends_at?: string | null
  current_period_end?: string | null
  cancel_at_period_end?: boolean | null
  last_event_type?: string | null
  updated_at?: string | null
}

export interface CheckoutSessionPayload {
  plan?: 'starter' | 'pro' | 'enterprise'
  seats?: number
  trial_days?: number
}

export interface CheckoutSessionResponse {
  session_id: string
  url: string
  customer_id: string
}

export interface PortalSessionResponse {
  url: string
}

export function fetchBillingStatus() {
  return apiFetch<BillingStatus>('/billing/status')
}

export function createCheckoutSession(payload: CheckoutSessionPayload = {}) {
  return apiFetch<CheckoutSessionResponse>('/billing/checkout-session', {
    method: 'POST',
    body: payload,
  })
}

export function createPortalSession() {
  return apiFetch<PortalSessionResponse>('/billing/portal-session', {
    method: 'POST',
  })
}
