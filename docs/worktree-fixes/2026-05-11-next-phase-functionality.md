# Fix Record: Next Phase Functionality Kickoff

- Status: `in_progress`
- Date: `2026-05-11`
- Owner: `codex`
- Worktree: `C:\temp\velobid-phase-next-functionality`
- Branch: `phase/next-functionality`
- Base branch: `codex/container-sync-repo`

## Tracking Links

- Issue: `https://github.com/jlicerio/velobid/issues/1`
- PR: `tbd`
- Related docs: `docs/ai-chat-debugging-notes.md`

## Problem Summary

The live app UI is usable in `Projects`, `Residential`, and `Settings`, but chat reliability and error feedback are inconsistent across routes and deployment states.

## Root Cause

Current evidence suggests mixed backend failure modes:

- `/api/v1/agent/hermes-chat` can return an empty stream (`[DONE]` with no content) in some deployments.
- `/api/v1/agent/chat` can fail when upstream API credentials/config are invalid.
- Frontend currently has limited distinction between empty successful stream and actionable backend failure.

## Fix Plan

1. Add robust empty-stream detection and user-visible error messaging in chat state management.
2. Harden backend proxy/agent routes to emit explicit error events on blank/invalid upstream responses.
3. Add verification coverage for dashboard chat and project chat with clear pass/fail criteria.

## Changes Implemented

- `none yet`: kickoff record created for phase planning and execution tracking.

## Deployment Impact

- Env vars touched: `tbd`
- Migration required: `no`
- Backward compatible: `yes`
- Rollback approach: revert branch commit(s) and redeploy previous image tag

## Verification

- Commands run:
  - `Invoke-WebRequest https://velobid.tailfceaca.ts.net/`
  - `POST /api/v1/auth/login`
  - `POST /api/v1/agent/hermes-chat`
  - `POST /api/v1/agent/chat`
- Results:
  - Live UI routes render in authenticated session for primary pages.
  - Chat route behavior varies by backend path and deployment config, confirming the next-phase target.

## Suggested Next Fixes

1. Frontend: detect `DONE` without any content/thought/tool events and surface a clear retry + diagnostic hint.
2. Backend: in `api/services/hermes_proxy.py`, emit explicit SSE `error` event when upstream returns empty completion.
3. Backend: in `api/routers/agent_chat.py`, keep upstream auth/config failures user-actionable while masking secret details.

## Handoff Notes

Use this file as the phase control log. Append every implementation/test result here before merge.
