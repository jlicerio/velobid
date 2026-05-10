# AI Chat Debugging Notes

## Silent-Return Bug (Fixed)

**Symptom:** AI Chat send button does nothing — typing a message and clicking send clears the input but no API call is made, no response returns, no error is shown.

**Root Cause:** In `frontend/src/lib/chat-store.tsx`, the `sendMessage` function started with:

```ts
if (!state.currentSessionId) return
```

When `currentSessionId` was `null` (no session created yet), the function silently returned. Meanwhile, `handleSend` in `MessageInput` had already called `setText("")`, so the user's message disappeared with zero feedback.

**Fix:** Instead of silently returning, `sendMessage` now auto-creates a session if none exists:

```ts
let sessionId = state.currentSessionId
if (!sessionId) {
  // Auto-create a session if none exists
  const newId = crypto.randomUUID()
  dispatch({
    type: "CREATE_SESSION",
    session: {
      id: newId,
      projectId: state.projectId || "",
      title: `Chat ${new Date().toLocaleTimeString()}`,
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    },
  })
  sessionId = newId
}
```

Additionally, `message-input.tsx` now wraps `sendMessage` in try/catch and shows a red error banner below the input when sending fails.

---

## Backend Configuration

### `OPENCODE_API_KEY` Required

The FastAPI backend reads `OPENCODE_API_KEY` (not `OPENCODE_GO_API_KEY`) to call the LLM. The docker-compose.yml currently sets `OPENCODE_GO_API_KEY` for Hermes but does **NOT** pass `OPENCODE_API_KEY` to the velobid container.

| Variable | Used By | Purpose |
|---|---|---|
| `OPENCODE_API_KEY` | FastAPI backend (agent.py, ai.py) | Direct LLM calls from the backend agent |
| `OPENCODE_BASE_URL` | FastAPI backend | LLM API base URL (defaults to OpenCode) |
| `OPENCODE_GO_API_KEY` | Hermes container | LLM API key for Hermes proxy |
| `HERMES_API_KEY` | Both | Internal auth between backend and Hermes (default: `velobid-internal`) |

**Fix:** Add to the `velobid` service in `docker-compose.yml`:

```yaml
environment:
  - OPENCODE_API_KEY=${OPENCODE_API_KEY}
  - OPENCODE_BASE_URL=${OPENCODE_BASE_URL:-https://opencode.ai/zen/go/v1}
```

---

## Hermes Dependency

- When **NO project** is selected (dashboard view): frontend routes to `/api/v1/agent/hermes-chat` which proxies to Hermes
- When a project **IS** selected: frontend routes to `/api/v1/agent/chat` which uses the backend agent directly (requires `OPENCODE_API_KEY`)
- Hermes must be running for dashboard chat to work. It is started with `profiles: ["hermes"]` in `docker-compose.dev.yml` — it may not be running by default in dev mode.
- If Hermes is unreachable, the `/api/v1/agent/hermes-chat` route will return an error that is now properly displayed in the chat UI.

---

## Chat Architecture Overview

### Frontend Flow:
1. User types message in `MessageInput`, clicks send
2. `handleSend` calls `sendMessage(trimmed)` from `chat-store.tsx`
3. `sendMessage` adds user + assistant messages to session, then calls `sendChatMessage` from `api/services/chat.ts`
4. `sendChatMessage` decides the endpoint:
   - With `projectId` → POST `/api/v1/agent/chat` (agent with tool loop)
   - Without `projectId` → POST `/api/v1/agent/hermes-chat` (proxied to Hermes)

### Backend Routes:
- `/api/v1/agent/chat` (`agent_chat.py`): Uses OpenAI client directly, runs tool loop with up to 5 iterations, streams SSE. Requires `OPENCODE_API_KEY`.
- `/api/v1/agent/hermes-chat` (`hermes_chat.py`): Proxies to Hermes container at `HERMES_URL` (default `http://hermes:8642`).

### Auth:
- Both routes require Bearer token authentication (`get_auth_context`)
- Both routes enforce agent access (`enforce_agent_access`) — checks trial/subscription and rate limits
