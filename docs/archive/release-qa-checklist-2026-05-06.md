> **ARCHIVED** — Historical release QA checklist from 2026-05-06. Superseded by the automated Playwright smoke tests and the production next-phase plan.
> This document has been archived because its purpose has been fulfilled or superseded by newer documentation.
> See  for the current development plan.
> Original location: 
# Release QA Checklist - Pre-Prod Signoff

Use this checklist before promoting a build from pre-prod to production.

## Release candidate setup
- [ ] Deploy the exact release commit SHA to pre-prod.
- [ ] Confirm service health checks are green after deploy.
- [ ] Confirm required environment variables and secrets are loaded.
- [ ] Confirm database migrations completed successfully (if any).

## Core user flows
- [ ] Login succeeds and session persists after refresh.
- [ ] Logout routes to a valid sign-in page (`/login`).
- [ ] Residential estimate can be submitted with required fields.
- [ ] Residential success state is rendered as structured UI, not raw JSON (Issue #3).
- [ ] Newly created project appears in the project list without manual workaround.

## UI and responsiveness
- [ ] Desktop pass (>=1280px): no overlap, clipped content, or broken nav states.
- [ ] Mobile pass (375x812): main content visible, chat toggle works, form actions reachable.
- [ ] `+ New Project` disabled state is visually clear and not fake-active.

## Project detail validation
- [ ] Overview tab loads expected content with no UI errors.
- [ ] Bids tab shows clear "coming soon" messaging.
- [ ] Documents tab shows clear "coming soon" messaging.

## Regression and stability
- [ ] No uncaught console errors across primary flows.
- [ ] Key API calls return expected status codes in UI flows.
- [ ] No broken routes or dead-end screens (`/login`, project detail, estimate flow).

## Final signoff gates
- [ ] Main UI issue acceptance criteria are complete (Issue #2).
- [ ] Residential success UI follow-up is complete and verified (Issue #3).
- [ ] QA notes are updated with date, devices, browsers, and tester.
- [ ] Release is explicitly approved for production promotion.

## Issue links
- Issue #2: https://github.com/jlicerio/velobid/issues/2
- Issue #3: https://github.com/jlicerio/velobid/issues/3
