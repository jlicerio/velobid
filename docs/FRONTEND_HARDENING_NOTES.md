# Frontend Hardening Notes

## Scope

This worktree contains the checked-in static frontend bundle referenced by `api/static/index.html`.

The 2026-05-13 authenticated QA findings were against the live app at `https://velobid.tailfceaca.ts.net/`. The live app includes routes and UI that are not present in this checked-in static bundle, including `/residential` and the `/projects/:id` `Overview / Bids / Documents` project-detail flow.

## Completed In This Worktree

- Added `api/static/hardening.css`.
- Linked the hardening stylesheet from `api/static/index.html`.
- Added a mobile header rule for the checked-in authenticated header so account actions wrap instead of clipping on narrow screens.

## Not Completed Here

The residential required-field placeholder issue cannot be patched safely in this worktree because the active checked-in bundle does not contain the live `Residential Estimate` route or strings such as `Customer Name`, `Generate Estimate`, or `John Smith`.

## Required Follow-Up

Restore or locate the frontend source/bundle that produced the live `/projects`, `/projects/:id`, `/residential`, and `/settings` routes before implementing the residential form fix. Once source is restored, fix the residential form by keeping required values empty until the user enters data and using placeholders only as examples.
