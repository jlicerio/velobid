> **ARCHIVED** — Historical QA UI audit notes from 2026-05-06. The issues identified in this pass were addressed and fixed (issues #2, #3, #5). Superseded by the production next-phase plan.
> This document has been archived because its purpose has been fulfilled or superseded by newer documentation.
> See  for the current development plan.
> Original location: 
# UI/UX QA Notes - 2026-05-06

## Scope covered
- Live UI/UX regression pass on `https://velobid.tailfceaca.ts.net`
- Auth/logout flow
- Residential estimate flow
- Desktop and mobile responsiveness
- Project detail tabs (Overview/Bids/Documents)

## What was fixed since initial audit
- Logout now routes to a valid sign-in screen.
- `/login` route now renders auth UI.
- Residential form now includes required fields (`customer_name`, `customer_address`, `scope_description`).
- Mobile layout now exposes main content and includes chat sidebar toggle.
- `+ New Project` no longer appears as fake-active (currently disabled).
- `Bids`/`Documents` now show clear "coming soon" messaging.

## Remaining item logged
- Issue #3: residential success response is shown as raw JSON block and should be rendered as a structured success UI.
  - https://github.com/jlicerio/velobid/issues/3

## Related issue
- Issue #2 (main UI/UX fixes):
  - https://github.com/jlicerio/velobid/issues/2

## Notes for next pass
- After Issue #3 lands, run one more mobile + desktop validation and close Issue #2 if all acceptance criteria are satisfied.
