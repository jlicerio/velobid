# Model Cost and Delegation Playbook

This playbook defines a production baseline for keeping agent quality high while keeping model spend predictable.

## Scope

- Hermes/Codex agent requests initiated from VeloBid UI or operator workflows.
- Trial and paid tenants.

## 1) Model Tier Policy

Use a two-tier model policy:

| Tier | Model | Primary use |
|------|-------|-------------|
| Default (cheap) | `deepseek-v4-flash` (`HERMES_MODEL`) | Day-to-day chat, summarization, simple code/file tasks, first-pass drafting. |
| Escalation (quality) | `deepseek-v4` (or equivalent higher-reasoning model in your provider) | Complex reasoning, high-risk changes, repeated failure recovery. |

Escalate from cheap tier only when at least one condition is true:

1. Request is high risk (auth, payments, data migration, security controls).
2. Cheap tier failed twice (incorrect output, incomplete output, or tool errors not caused by infra).
3. Context remains ambiguous after trim and needs deeper reasoning.
4. User explicitly asks for highest-quality reasoning over speed/cost.

## 2) Token Budget and History Trimming

Use explicit per-request budgets:

- Cheap tier target: `<= 6,000` total tokens (input + output).
- Escalation tier target: `<= 12,000` total tokens.
- Hard stop: do not exceed `16,000` total tokens for a single turn.

History trimming policy before each model call:

1. Keep pinned context: system instructions, tenant/auth scope, current task.
2. Keep only the most recent 4 turns in full text.
3. Replace older turns with a rolling summary (`<= 300` tokens).
4. Replace repeated code/log blocks with file paths and line references.
5. Trim raw logs to tail segments only (last 80-120 lines).

## 3) Delegation Policy (Local vs Hermes)

Keep locally in Codex:

- Planning, requirement clarification, and final patch review.
- Small/medium edits with fast validation.
- Security-sensitive decisions and release signoff messaging.

Delegate to Hermes:

- Long-running Linux tasks (builds, integration tests, data jobs, backups).
- Parallelizable repo scans and environment checks.
- Server-side diagnostics where local environment does not match production.

Delegation handoff contract:

1. Send objective, constraints, expected output format, and timeout.
2. Require return artifacts: commands run, exit codes, key logs/paths.
3. Keep final merge/review decisions local.

## 4) Monitoring and Cost Controls

Track at minimum:

- `agent_requests_total` by tenant, model, endpoint.
- `agent_tokens_input_total` and `agent_tokens_output_total` by model.
- `agent_estimated_cost_usd_total` by tenant/day/month.
- `agent_escalation_rate` (escalated calls / total calls).
- `agent_latency_ms_p50` and `agent_latency_ms_p95`.
- `agent_http_429_total` and `agent_http_402_total` (rate-limit and trial gating).
- `agent_errors_total` by status class and provider error type.

Recommended alerts:

1. Spend warning at 70% of monthly budget.
2. Spend critical at 90% (auto-escalation disabled except high-risk routes).
3. Sudden 429 spike (possible abuse or limit misconfiguration).
4. Webhook/subscription drift causing unexpected 402 increases.

## 5) Operating Cadence

- Daily: review top tenants by spend, escalation rate, and 429 volume.
- Weekly: tune model routing and token caps from real usage.
- Monthly: reconcile estimated model spend vs invoice and update thresholds.
