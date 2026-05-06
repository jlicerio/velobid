export async function sendChatMessage(
  messages: any[],
  projectId?: string,
  bidderId?: string,
  signal?: AbortSignal,
): Promise<Response> {
  return fetch("/api/v1/agent/hermes-chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages,
      project_id: projectId || undefined,
      bidder_id: bidderId || "acme_hvac",
    }),
    signal,
    credentials: "include",
  })
}
