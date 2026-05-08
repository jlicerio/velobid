export async function sendChatMessage(
  messages: any[],
  projectId?: string,
  bidderId?: string,
  signal?: AbortSignal,
): Promise<Response> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const endpoint = projectId ? "/api/v1/agent/chat" : "/api/v1/agent/hermes-chat"

  return fetch(endpoint, {
    method: "POST",
    headers,
    body: JSON.stringify({
      messages,
      project_id: projectId || undefined,
      trade: "hvac",
      bidder_id: bidderId || undefined,
    }),
    signal,
    credentials: "include",
  })
}
