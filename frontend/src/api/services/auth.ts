import { apiFetch } from "@/lib/api/client"

export async function fetchBidders(): Promise<any> {
  return apiFetch<any>("/bidders")
}

export async function login(bidderId: string, userId: string, password: string): Promise<any> {
  return apiFetch<any>("/auth/login", {
    method: "POST",
    body: { bidder_id: bidderId, user_id: userId, password },
  })
}

export function logout() {
  localStorage.removeItem("token")
  localStorage.removeItem("bidder_id")
  localStorage.removeItem("user_id")
  window.location.href = "/login"
}
