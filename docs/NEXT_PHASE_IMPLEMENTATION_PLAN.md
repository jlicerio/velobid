# VeloBid Next Phase Implementation Plan

## Executive Summary

Authenticated QA on 2026-05-13 showed that the live product is stable enough to build on, but the next phase needs one important alignment decision before feature work starts:

**Use the project-detail information architecture as the canonical estimator workflow.**

The live app uses `/projects`, `/projects/:id`, `/residential`, and `/settings`. The project detail route exposes `Overview`, `Bids`, and `Documents` tabs, and the tested project route `/projects/integration_test` supported bid actions and project chat without console warnings or errors.

The checked-in static bundle in this repo still includes older `/workspace/:projectId/:trade?` behavior with `Live Preview`, `SOV`, `History`, and `Blueprints`. That source/route mismatch is the highest planning risk. Before major frontend work, restore or identify the current live frontend source that generated the deployed bundle.

## QA Baseline

Test target:
`https://velobid.tailfceaca.ts.net/`

Validated authenticated routes:

- `/projects`
- `/projects/integration_test`
- `/residential`
- `/settings`

Validated working interactions:

- Login with the test account provided during QA.
- Project dashboard load and search.
- Project detail tabs: `Overview`, `Bids`, `Documents`.
- Project actions: `Preview Bid`, `Generate Client Bid`, `Generate Internal Bid`.
- Project chat send from `Ask about the project...`.
- Settings page load and `Save Settings` click.
- Residential page load and `Generate Estimate` browser validation.

Known UX defects:

- Mobile authenticated header clips account/navigation actions at `390px` width.
- Residential required fields show example text that looks like prefilled data, but browser validation still treats the fields as empty.
- Login page title and form label associations should be cleaned up.

## Current Architecture Notes

Backend entrypoint:

- `api/main.py`
- Static UI served from `api/static/index.html`.
- Static assets mounted at `/static`.
- Bid/project files mounted at `/files`.

Core API areas:

- `api/routers/bids.py`: bid preview/generation and project-related endpoints.
- `api/routers/agent_chat.py`: portfolio/project chat surface.
- `api/routers/blueprints.py`: blueprint upload and retrieval.
- `api/routers/versions.py`: version history.
- `api/services/bids.py`: project config loading and bid generation service layer.
- `api/services/state.py`: current bid state behavior.
- `bid_engine/pricing_engine.py`: trade pricing.
- `bid_engine/pdf_generator.py` and `bid_engine/templates/*`: PDF output.

Frontend state in this repo:

- `api/static/index.html` references a built bundle.
- Original React/TypeScript source is not present in this checkout.
- Multiple historical built bundles exist in `api/static/assets`.
- The active checked-in bundle does not appear to match the latest live route behavior.

## Source/Route Mismatch Resolution

Before adding new UI features, complete this resolution task:

1. Identify the source repo, branch, or build artifact that produced the live `/projects/:id` project-detail UI.
2. Confirm whether `/workspace/:projectId/:trade?` is deprecated, hidden behind role flags, or from an older bundle.
3. Replace checked-in stale static assets with a reproducible frontend build process.
4. Add a short architecture note documenting canonical routes.

Acceptance criteria:

- A developer can run one documented command to rebuild the frontend asset referenced by `api/static/index.html`.
- The checked-in source contains the project-detail UI that matches live QA.
- Legacy `/workspace` routing is either removed, redirected, or explicitly documented as deprecated.

## Hardening Backlog

1. Fix residential form semantics.

Acceptance criteria:

- Required fields render empty values until the user enters data.
- Placeholder text is clearly an example, not a default.
- Submit validation points to the first missing required field.
- A successful estimate can be generated with valid entered data.

2. Fix mobile authenticated header.

Acceptance criteria:

- At `390x844`, primary nav and account actions remain reachable.
- Header text does not clip or overlap.
- The current page is still visibly indicated.

3. Clean login accessibility and title.

Acceptance criteria:

- Inputs have programmatic labels.
- Password managers and screen readers identify fields correctly.
- Login route title reflects authentication, not only AI chat.

4. Lock project-detail route as canonical.

Acceptance criteria:

- `/projects/:id` owns estimator workflow tabs.
- `Overview`, `Bids`, and `Documents` have clear empty/loading/error states.
- Bid actions surface success/failure feedback.

5. Add smoke QA for authenticated flows.

Acceptance criteria:

- Automated smoke covers login, `/projects`, project detail, `/residential`, and `/settings`.
- Mobile viewport check is included.
- Console warnings/errors fail the smoke run.

## Feature Milestones

### Milestone 1: Route And Source Alignment

- Restore current frontend source.
- Document route ownership.
- Remove or redirect stale workspace paths.
- Add build instructions.

### Milestone 2: Project Detail Completion

- Expand `Overview` into project health, trade summary, latest bid status, and recent activity.
- Make `Bids` the home for bid packages, generated PDFs, versions, and comparison.
- Make `Documents` the home for uploads, blueprint previews, OCR/vision status, and extracted takeoff data.

### Milestone 3: Residential Estimate Flow

- Fix required field semantics.
- Add clear estimate preview before generation.
- Add generated estimate output and download flow.
- Persist residential estimate history per customer/project.

### Milestone 4: AI-Assisted Estimating

- Keep project chat scoped to the current project.
- Add visible tool/status messages for bid changes.
- Require confirmation before mutating bid data.
- Persist chat-derived changes into version history.

### Milestone 5: Production Hardening

- Replace permissive CORS with configured origins.
- Add auth middleware and role-based access if not already in the live branch.
- Add rate limits for AI and generation endpoints.
- Add audit logging for bid generation, settings saves, and document uploads.

## Worktree Strategy

Use one worktree per bounded unit:

- `phase/source-alignment`: restore frontend source and canonical route docs.
- `phase/ui-hardening`: residential form, login accessibility, mobile header.
- `phase/project-detail-bids`: bids tab and bid package feedback.
- `phase/project-detail-documents`: documents tab, upload states, blueprint viewer.
- `phase/qa-smoke`: authenticated Playwright/browser smoke tests.

Rules:

- Do not let two workers edit the same built bundle in parallel.
- Prefer source edits over minified static edits.
- If source is missing, document the limitation and keep static edits small.
- Merge source alignment before broad frontend feature work.

## QA Checklist

Desktop:

- Login redirects to `/projects`.
- Dashboard totals, filters, and search render.
- Project detail route opens from a project card.
- `Overview`, `Bids`, and `Documents` tabs render.
- `Preview Bid`, `Generate Client Bid`, and `Generate Internal Bid` show visible result states.
- Project chat sends and receives without duplicate user messages.
- Settings save gives success or failure feedback.
- Residential estimate submits with valid data.

Mobile:

- Header actions remain reachable at `390x844`.
- Dashboard cards stack without clipped text.
- Project detail tabs remain usable.
- Residential form labels, inputs, and validation messages fit.

Diagnostics:

- Console `error` and `warn` logs are reviewed.
- Network failures show user-facing errors.
- Generated files are reachable from expected links.

## Risks And Blockers

- The live frontend source is missing from this checkout.
- Static bundle edits are fragile and should not become the long-term workflow.
- OpenCode drifted into unrelated trade work during delegation; future prompts need explicit write scope and acceptance criteria.
- Existing repo contains incomplete Git metadata in `C:\Users\xlice\OneDrive\Desktop\velobid`; use `velobid-clone` or a healthy worktree for Git-backed work.
- Auth credentials used in QA must not be committed.

## Handoff Prompts

### Source Alignment Worker

```text
Work only on source/build alignment. Identify the frontend source that produces the live /projects/:id Overview/Bids/Documents UI. Document the build command and update api/static/index.html/assets only from a reproducible build. Do not add product features.
```

### UI Hardening Worker

```text
Work only on residential form semantics, mobile authenticated header behavior, and login accessibility/title. Keep visual language intact. Verify at desktop and 390x844 mobile. Do not touch backend bid logic.
```

### Project Detail Worker

```text
Work only on /projects/:id. Improve Overview/Bids/Documents empty, loading, success, and error states. Preserve existing project actions and chat. Add visible feedback for bid generation.
```

### QA Worker

```text
Create an authenticated smoke suite for login, /projects, /projects/:id, /residential, /settings, and mobile 390x844. Fail on console errors or warnings. Do not mutate production data unless using a dedicated test project.
```

