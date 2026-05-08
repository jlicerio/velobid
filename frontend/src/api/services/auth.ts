import { apiFetch } from "@/lib/api/client"
import { ApiError } from "@/lib/api/errors"

export async function login(userId: string, password: string): Promise<any> {
  const payload = { user_id: userId, password }

  try {
    return await apiFetch<any>("/auth/login", {
      method: "POST",
      body: payload,
    })
  } catch (error) {
    // Compatibility fallback: older API builds may still require bidder_id.
    if (error instanceof ApiError && error.status === 422) {
      const fromEnv = (import.meta as any)?.env?.VITE_DEFAULT_BIDDER_ID as string | undefined
      const fromStorage = typeof window !== "undefined" ? localStorage.getItem("bidder_id") : null
      const fallbackBidderId = (fromEnv || fromStorage || "air_hero").trim()

      return apiFetch<any>("/auth/login", {
        method: "POST",
        body: { ...payload, bidder_id: fallbackBidderId },
      })
    }
    throw error
  }
}

export function logout() {
  localStorage.removeItem("token")
  localStorage.removeItem("bidder_id")
  localStorage.removeItem("user_id")
  window.location.href = "/login"
}
