# Changelog

## 2026-05-12 — AI Chat Error Handling & Empty Response Detection

Full session to harden AI chat error handling across the stack. Three fixes completed in commit `3bd75e4`.

### 🟡 Medium — Fixed

- **AI chat empty stream returns blank assistant message** (hermes-chat)
  - `api/services/hermes_proxy.py` — added `had_meaningful_event` tracking; emits explicit SSE `error` event with `code: "empty_response"` when upstream returns `[DONE]` with zero content/thought/tool events.
  - `frontend/src/components/chat/message-list.tsx`[sic] — `chat-store.tsx` now tracks `receivedMeaningfulEvent` per-stream; blank responses replaced with diagnostic text + retry hint.
  - Commit: `3bd75e4`

- **AI chat auth/config failures silently swallow errors** (agent-chat)
  - `api/routers/agent_chat.py` — 6 specific OpenAI exception handlers (`AuthenticationError`, `RateLimitError`, `NotFoundError`, `BadRequestError`, `APIConnectionError`, `InternalServerError`) replace a single catch-all. Each returns an actionable SSE error event.
  - Sensitive data (API keys, filesystem paths) redacted from error payloads via `_mask_api_key()`.
  - Commit: `3bd75e4`

## 2026-05-10 — QA Audit Fixes

Full UI/UX QA audit performed against `https://velobid.tailfceaca.ts.net/projects`.
22 features passed, 6 issues found, all fixed below.

### 🔴 High — Fixed

- **Generate Client Bid fails with path resolution error** (#1)
  - `api/services/bids.py:128` — `request_output_dir.relative_to(PROJECT_ROOT)` raised `ValueError` because `/data/velobid` (Docker shared volume) is not a subpath of `/app` (container WORKDIR).
  - Fix: pass absolute `output_dir` directly — `generate_pdfs.py` accepts absolute paths.
  - Commit: `d83a3f5`

### 🟡 Medium — Fixed

- **AI Chat send button unresponsive** (#2)
  - `frontend/src/lib/chat-store.tsx` — `sendMessage` silently returned when `currentSessionId` was null, dropping the user's message with no feedback.
  - Fix: auto-create a session when none exists; added error banner in `message-input.tsx`.
  - Also documented backend `OPENCODE_API_KEY` config requirement in `docs/ai-chat-debugging-notes.md`.
  - Commit: `79b4ef2`

- **Export CSV navigates to about:blank** (#3)
  - `frontend/src/api/services/projects.ts` — blob URL was revoked before browser started the download.
  - `frontend/src/lib/api/client.ts` — added `rawResponse` option to bypass JSON parsing for blob downloads.
  - Fix: `setTimeout` delay before `revokeObjectURL`, error handling, empty blob check.
  - Commit: `bfbb045`

### 🟡 Low — Fixed

- **AI context sidebar shows stale active/archived counts** (#4)
  - `frontend/src/components/shared/AppShell.tsx` — deduplication guard prevented dashboard context from refreshing after archive/unarchive.
  - `frontend/src/lib/chat-store.tsx` — added `dashboardVersion` counter + `REFRESH_DASHBOARD` action.
  - `frontend/src/pages/ProjectsPage.tsx` — archive/unarchive now triggers `refreshDashboard()`.
  - Commit: `5340b36`

- **Clearing search field doesn't reset filter** (#5)
  - `frontend/src/pages/ProjectsPage.tsx` — search normalization called `.trim()` twice independently.
  - Fix: compute `const q = search.trim().toLowerCase()` once and reuse.
  - Commit: `edde7ca`

### Notes

- Issue #6 (`+ New Project` disabled) is by design — commercial project creation is on the roadmap.
- Deploying these fixes requires `OPENCODE_API_KEY` in the velobid container environment for AI chat to function.
