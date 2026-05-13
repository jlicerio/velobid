import { apiFetch } from "@/lib/api/client"

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

export function logout() {
  localStorage.removeItem("token")
  localStorage.removeItem("bidder_id")
  localStorage.removeItem("user_id")
  window.location.href = "/login"
}
