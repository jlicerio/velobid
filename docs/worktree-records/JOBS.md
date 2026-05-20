# Job Plan — fix/public-legal-routes-and-auth-prefetch

Branch: `fix/public-legal-routes-and-auth-prefetch`
Worktree: `//192.168.1.237/Ubuntu-Dev/projects/velobid-public-route-qa`
Base: `origin/main`

## Job 1 — Verify source vs deployed bundle

Goal: determine whether `/terms` and `/privacy` are broken in source or only stale in production.

Steps:
1. Inspect `frontend/src/app/router.tsx` for `/terms` and `/privacy` routes.
2. Inspect `frontend/src/pages/TermsPage.tsx` and `frontend/src/pages/PrivacyPage.tsx`.
3. Browser-check live `/terms` and `/privacy`.
4. If source is correct but live is 404, mark as stale deployed bundle.

Done when:
- Root cause is documented as source bug or stale deploy.

## Job 2 — Fix public legal pages

Goal: `/terms` and `/privacy` render legal pages, not app 404.

If source is broken:
- Fix/create `TermsPage.tsx` and `PrivacyPage.tsx`.
- Ensure routes remain public and outside `AppShell`.
- Add links back to `/login` or `/signup`.

If source is correct:
- Do not change source unnecessarily.
- Ensure tests catch stale bundles after deployment.

Done when:
- `/terms` renders Terms content.
- `/privacy` renders Privacy content.

## Job 3 — Stop unauthenticated project prefetch

Goal: public pages must not fetch protected project/dashboard APIs.

Observed issue:
- `/login` emits `401 GET /api/v1/projects/with-pricing` twice.

Inspect:
- `frontend/src/components/shared/AppShell.tsx`
- `frontend/src/pages/ProjectsPage.tsx`
- `frontend/src/lib/dashboard-context.ts`
- `frontend/src/lib/chat-store.tsx`
- `frontend/src/api/services/projects.ts`
- `frontend/src/app/router.tsx`

Steps:
1. Search for `fetchProjectsWithPricing`, `loadDashboardSnapshot`, and `projects/with-pricing`.
2. Find which component runs while unauthenticated.
3. Ensure protected data fetches only run when `localStorage.token` exists.
4. Prefer central auth guard if practical; otherwise use minimal local guard.
5. Do not hide real 401s after a token exists.

Done when:
- Opening `/login` in a clean browser makes no `projects/with-pricing` request.

## Job 4 — Add login autocomplete polish

Goal: remove browser autocomplete diagnostic.

File:
- `frontend/src/pages/LoginPage.tsx`

Changes:
- Add `autoComplete="username"` to User ID input.
- Add `autoComplete="current-password"` to Password input.

Done when:
- Browser no longer suggests missing `current-password` autocomplete.

## Job 5 — Add Playwright coverage

Goal: make browser-session findings repeatable.

Preferred setup:
- Reuse PR #8 Playwright scaffold if merged or rebaseable.

Tests:
- `public-routes.spec.ts`
  - `/login` renders login page.
  - `/signup` renders signup page.
  - `/terms` does not render 404.
  - `/privacy` does not render 404.
  - `/projects` redirects unauthenticated to `/login`.
- `unauthenticated-console.spec.ts`
  - `/login` has no console error containing `projects/with-pricing`.
  - `/signup` has no console error containing `projects/with-pricing`.
- `mobile-auth.spec.ts`
  - viewport `375x812`.
  - login fields and Sign In visible.
  - signup fields and Create Account visible.

Done when:
- Playwright tests fail before fix and pass after fix.

## Job 6 — Validate

Run:
```bash
cd frontend
npm install
npm run build
npm run lint
VELOBID_URL=http://192.168.1.237:8000 npm run test:smoke
```

If backend changed, also run:
```bash
pytest -q tests
```

Record pass/fail in PR body.

## Job 7 — Open PR

PR title:
- `fix: public legal routes and unauthenticated project prefetch`

PR body must include:
- Link to this job plan.
- Browser-session findings.
- Root cause for `/terms` and `/privacy`.
- Validation results.
- Relationship to PR #8 if Playwright scaffold is reused.

## Strict scope

Do not include:
- Billing work.
- Docker multi-stage work.
- Auth persistence work.
- Security hardening beyond this route/prefetch issue.
- PR #7 decomposition.
