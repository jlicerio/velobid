# VeloBid Phase 1 -> Phase 2 User Data Cutover Checklist

This checklist is for transitioning from a single-node Docker Compose beta setup (Phase 1) to a more scalable beta-ready architecture (Phase 2) without breaking user identity, sessions, or profile data.

## Scope
- User identity and auth continuity
- User profile data integrity
- Session/token continuity during deploys
- Safe migration and rollback

## Definitions
- Phase 1: single VM + Docker Compose, limited users, simple ops
- Phase 2: reverse proxy, managed/shared data services, stronger observability, safer deploy/rollback
- Canonical user id: immutable `user_id` UUID used everywhere internally

## A. Pre-Cutover Readiness

### A1) Identity model locked
- [ ] `user_id` UUID exists for every user.
- [ ] App logic does not key users by email/username.
- [ ] External auth mapping (if used) is stored as `external_auth_id`.
- [ ] Unique constraints are defined on required identity fields.

### A2) Schema and compatibility
- [ ] All new columns/tables are added as backward-compatible migrations.
- [ ] Legacy read path still works after migrations.
- [ ] `created_at`, `updated_at`, `version` fields exist on user records.
- [ ] Migration scripts are idempotent.

### A3) Access layer
- [ ] All user data reads/writes go through a single service/repository layer.
- [ ] No direct ad-hoc DB/file access from feature handlers.
- [ ] Logging includes operation + `user_id` + request id (without secrets).

### A4) Safety
- [ ] Backup is automated and tested for user data.
- [ ] Restore drill completed in non-prod within last 7 days.
- [ ] Rollback owner assigned and documented.

## B. Data Migration Plan

### B1) Backfill
- [ ] Export current user data from Phase 1 source.
- [ ] Normalize and map all users to canonical `user_id`.
- [ ] Import into Phase 2 store.
- [ ] Verify row counts and key integrity.

Command placeholders:
```bash
# export
<export_users_command>

# transform/normalize
<normalize_users_command>

# import
<import_users_command>
```

### B2) Validation before live traffic
- [ ] Count parity validated (`old_count == new_count` for active users).
- [ ] Spot-check at least 25 users across roles/tenants.
- [ ] Null/blank critical fields report reviewed.
- [ ] Duplicate identity report reviewed.

Query placeholders:
```sql
-- active user count
<active_user_count_query>

-- duplicate emails or external IDs
<duplicate_identity_query>

-- missing required user fields
<missing_required_fields_query>
```

## C. Dual-Read / Dual-Write Cutover

### C1) Dual-read enablement
- [ ] Read path checks new store first.
- [ ] Fallback to old store is enabled on miss.
- [ ] Read source is tagged in logs/metrics (`new` vs `fallback_old`).

### C2) Dual-write enablement
- [ ] Writes go to both old and new stores.
- [ ] Write failures to new store are surfaced in alerting.
- [ ] Write latency impact is monitored.
- [ ] Conflict resolution rule documented (new wins / old wins / timestamp wins).

### C3) Consistency checks during dual mode
- [ ] Hourly diff job compares old vs new user records.
- [ ] Mismatch threshold defined (example: <0.1%).
- [ ] Any mismatch triggers investigation ticket.

## D. Session and Auth Continuity

- [ ] Auth signing secrets shared and stable across deploys.
- [ ] Session backend is shared (not container-local filesystem).
- [ ] Token TTL and refresh policy documented.
- [ ] Forced logout plan defined only for emergency.
- [ ] Login success rate dashboard exists.

## E. Rollout Plan (Traffic Ramp)

- [ ] Internal users only (0% public beta)
- [ ] 5% beta cohort
- [ ] 25% beta cohort
- [ ] 50% beta cohort
- [ ] 100% beta users

At each stage:
- [ ] Login success >= target
- [ ] Profile read/write error rate <= target
- [ ] P95 latency within target
- [ ] No unresolved P1/P2 incidents

## F. Monitoring and Alerting Gates

Track these metrics per rollout stage:
- [ ] `auth_login_success_rate`
- [ ] `user_read_error_rate`
- [ ] `user_write_error_rate`
- [ ] `dual_read_fallback_rate`
- [ ] `dual_write_mismatch_rate`
- [ ] `user_profile_p95_latency_ms`

Alert examples:
- [ ] Login success drops below threshold for 5 min
- [ ] Fallback read rate spikes above threshold
- [ ] Write mismatch rate exceeds threshold

## G. Cutover Completion Criteria

Promote to Phase 2 source of truth only when all are true:
- [ ] Dual-write mismatches remain below threshold for 24h.
- [ ] Fallback reads are near zero for 24h.
- [ ] No critical auth/session incidents for 24h.
- [ ] Data parity checks pass on scheduled jobs.

Then:
- [ ] Disable old-store read fallback.
- [ ] Disable old-store writes.
- [ ] Keep rollback path for one release window.

## H. Rollback Plan (One-Command Mindset)

Rollback triggers:
- [ ] P1 auth outage
- [ ] sustained write failures
- [ ] unacceptable mismatch rate

Rollback actions:
- [ ] Flip feature flag: reads -> old store.
- [ ] Flip feature flag: writes -> old store only.
- [ ] Pause rollout at current cohort.
- [ ] Announce incident status and ETA.

Rollback command placeholders:
```bash
<set_feature_flag_reads_old_command>
<set_feature_flag_writes_old_command>
<pause_rollout_command>
```

## I. Post-Cutover Cleanup

- [ ] Remove dual-write logic after stability window.
- [ ] Remove old fallback read path.
- [ ] Archive migration scripts and reports.
- [ ] Update runbooks and onboarding docs.
- [ ] Create retrospective with lessons learned.

## J. Ownership

- Cutover lead: `<name>`
- DB/data lead: `<name>`
- App/auth lead: `<name>`
- SRE/ops lead: `<name>`
- Incident commander backup: `<name>`

## K. Signoff

- Engineering lead: `[ ]`
- Product owner: `[ ]`
- QA lead: `[ ]`
- Ops/SRE: `[ ]`

Date approved: `<YYYY-MM-DD>`
