import { apiFetch } from "@/lib/api/client"

export interface SignupStartRequest {
  company_name: string
  bidder_display_name?: string | null
  primary_contact: string
  admin_email: string
  password: string
  phone?: string | null
  location?: string | null
  accept_terms: boolean
}

export interface SignupStartResponse {
  signup_id: string
  email: string
  message: string
  expires_in_minutes: number
}

export async function login(userId: string, password: string): Promise<any> {
  const fromStorage = typeof window !== "undefined" ? localStorage.getItem("bidder_id") : null
  const fromEnv = (import.meta as any)?.env?.VITE_DEFAULT_BIDDER_ID as string | undefined
  const bidderId = (fromEnv || fromStorage || "air_hero").trim()

  const payload = {
    bidder_id: bidderId,
    user_id: userId,
    password,
  }

  return apiFetch<any>("/auth/bidders/login", {
    method: "POST",
    body: payload,
  })
}

export async function signupStart(data: SignupStartRequest): Promise<SignupStartResponse> {
  return apiFetch<SignupStartResponse>("/auth/signup/start", {
    method: "POST",
    body: data,
  })
}

export function logout() {
  localStorage.removeItem("token")
  localStorage.removeItem("bidder_id")
  localStorage.removeItem("user_id")
  window.location.href = "/login"
}
