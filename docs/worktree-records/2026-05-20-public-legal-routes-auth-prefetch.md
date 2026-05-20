# Worktree Record — Public Legal Routes + Auth Prefetch QA

Date: 2026-05-20
Branch: `fix/public-legal-routes-and-auth-prefetch`
Worktree: `//192.168.1.237/Ubuntu-Dev/projects/velobid-public-route-qa`
Base: `origin/main`

## Trigger

A Playwright MCP browser-session UI pass against the live VeloBid deployment found production-readiness gaps relevant to the next production beta hardening phase.

Target tested:

```text
http://192.168.1.237:8000
Desktop viewport: 1365x900
Mobile viewport: 375x812
```

## Browser Session Results

### Passing checks

- `/` redirects to `/login` when unauthenticated.
- `/login` renders correctly on desktop.
- Login submit is disabled when fields are empty.
- Login submit enables when User ID and Password are filled.
- Invalid credentials remain on `/login` and show `Invalid credentials`.
- `/projects` redirects unauthenticated users back to `/login`.
- `/signup` renders correctly on desktop.
- `/signup` fits on mobile `375x812` with all fields and CTA reachable.
- `/login` fits on mobile `375x812`.
- API health endpoints are up:
  - `GET /api/v1/health -> 200`
  - `GET /api/v1/meta -> 200`

### Issues found

#### 1. `/terms` renders app 404

```text
GET /terms -> HTTP 200
Rendered UI -> 404 Page not found
```

Source router contains a `/terms` route, so the deployed bundle may be stale or the route/page implementation differs from source.

#### 2. `/privacy` renders app 404

```text
GET /privacy -> HTTP 200
Rendered UI -> 404 Page not found
```

Same likely root as `/terms`.

#### 3. Login route performs unauthenticated project API fetch

Console on `/login` shows:

```text
401 GET /api/v1/projects/with-pricing
401 GET /api/v1/projects/with-pricing
```

This is non-blocking but should be removed for production observability. Public unauthenticated pages should not fetch protected project data before auth state is confirmed.

#### 4. Password autocomplete diagnostic

Browser diagnostic:

```text
Input elements should have autocomplete attributes
suggested: current-password
```

The login password field should include:

```tsx
autoComplete="current-password"
```

## Intended Scope

This worktree should stay focused on:

1. Fix deployed/public legal route behavior for `/terms` and `/privacy`.
2. Prevent protected project/dashboard data fetches while unauthenticated.
3. Add login password autocomplete.
4. Add Playwright smoke coverage for public routes and unauthenticated console cleanliness.
5. Update documentation/test notes only as needed.

## Out of Scope

- Full auth model consolidation.
- Billing/Stripe UI.
- Docker multi-stage build.
- PR #7 decomposition.
- Hermes deployment changes.

## Suggested Test Additions

Add to the Playwright smoke suite introduced in PR #8:

```text
frontend/tests/smoke/public-routes.spec.ts
frontend/tests/smoke/unauthenticated-console.spec.ts
frontend/tests/smoke/mobile-auth.spec.ts
```

Required assertions:

- `/terms` renders legal content and not the 404 page.
- `/privacy` renders legal content and not the 404 page.
- `/login` does not emit `401 /api/v1/projects/with-pricing`.
- `/signup` mobile layout remains reachable at `375x812`.
- `/login` mobile layout remains reachable at `375x812`.

## Acceptance Criteria

- Browser session against deployed app passes public-route checks.
- No protected project fetch occurs on `/login` before auth.
- Login password field has correct autocomplete.
- Playwright smoke tests cover the regressions.
- Branch has a focused PR linked to this worktree record.

## Implementation Record — 2026-05-20

Latest pushed implementation commit before this documentation update:

```text
7a54c05 fix: public legal routes, unauthenticated prefetch, autocomplete, and Playwright coverage
```

### Source root cause

The QA worktree was missing the legal route/page implementation:

- `frontend/src/app/router.tsx` did not include public `/terms` or `/privacy` routes.
- `frontend/src/pages/TermsPage.tsx` did not exist.
- `frontend/src/pages/PrivacyPage.tsx` did not exist.

The live app returned HTTP 200 but rendered the React app-level `NotFoundPage`, confirming the observed legal-page issue was a client routing/page gap for this branch. If `/terms` or `/privacy` still render 404 after these changes are deployed, the active Docker/frontend bundle is stale.

### Auth prefetch root cause

Unauthenticated users could enter the protected app route tree before redirect completed. During that window:

- `AppShell` could call `loadDashboardSnapshot()`.
- `ProjectsPage` could call `fetchProjectsWithPricing()`.

Both paths could cause `401 GET /api/v1/projects/with-pricing` before the user reached `/login`.

### Fix summary

Public legal routes:

- Added `frontend/src/pages/TermsPage.tsx`.
- Added `frontend/src/pages/PrivacyPage.tsx`.
- Added public `/terms` and `/privacy` routes in `frontend/src/app/router.tsx`.
- Kept both routes outside `AppShell` and outside auth protection.

Protected route boundary:

- Added `frontend/src/components/shared/ProtectedRoute.tsx`.
- Wrapped authenticated app routes under `ProtectedRoute`.
- Removed `AppShell`'s redundant auth-redirect effect because `AppShell` no longer mounts while unauthenticated.

Login autocomplete:

- Added `autoComplete="username"` to the User ID field.
- Added `autoComplete="current-password"` to the Password field.

Playwright coverage:

- Added `frontend/playwright.config.ts`.
- Added `frontend/tests/smoke/public-routes.spec.ts`.
- Added `frontend/tests/smoke/unauthenticated-console.spec.ts`.
- Added `frontend/tests/smoke/mobile-auth.spec.ts`.
- Updated `frontend/package.json` and `frontend/package-lock.json`.

### Validation results

Linux build on `selfsim-system`:

```bash
cd /home/selfsim/projects/velobid-public-route-qa/frontend
npm install
npm run build
```

Result: passed.

```text
vite v8.0.10 building client environment for production...
✓ built in 900ms
```

Lint:

```bash
npm run lint
```

Result: failed on pre-existing repo-wide lint debt unrelated to this branch. Do not broaden this branch to fix unrelated lint.

Playwright smoke against live deployment before redeploying this branch:

```text
Target: http://192.168.1.237:8000
Result: 7 passed, 2 failed
```

Passed tests confirmed:

- `/login` renders.
- `/signup` renders.
- `/projects` redirects unauthenticated users to `/login`.
- `/login` emits no `projects/with-pricing` console error.
- `/signup` emits no `projects/with-pricing` console error.
- mobile login/signup views are usable at `375x812`.

Failed tests before redeploy:

- `/terms` does not render 404.
- `/privacy` does not render 404.

Interpretation: live Docker is still running the old frontend bundle. These two failures should resolve after Docker is rebuilt/redeployed from `fix/public-legal-routes-and-auth-prefetch`.

### Deployment retest command

After Docker rebuild/redeploy:

```bash
cd /home/selfsim/projects/velobid-public-route-qa/frontend
VELOBID_URL=http://192.168.1.237:8000 npm run test:smoke
```

Expected result:

```text
9 passed
```

### Future-agent notes

- `frontend/test-results/` is a local Playwright artifact and should not be committed.
- The Linux worktree may need a temporary Linux-local `.git` pointer for git commands; restore the UNC pointer afterward for Windows/Zed tooling.
- Keep scope focused: no billing work, Docker multi-stage work, auth persistence redesign, unrelated lint cleanup, or PR #7 decomposition.
