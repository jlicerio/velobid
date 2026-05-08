# Stripe Billing Runbook

This runbook configures Stripe for VeloBid subscription billing using Checkout, Customer Portal, and a signed webhook endpoint.

## Scope

- Checkout: start a paid subscription.
- Customer Portal: self-service billing updates and cancellations.
- Webhook: sync subscription and invoice state into VeloBid.

## Prerequisites

- Production URL is live (example: `https://velobid.example.com`).
- VeloBid deployment uses `env.production.example` values via `/srv/velobid/secrets/velobid.env`.
- Access to Stripe Dashboard in both test mode and live mode.

## 1) Configure VeloBid Environment

Update `/srv/velobid/secrets/velobid.env` with Stripe values:

- `STRIPE_ENABLED=true`
- `STRIPE_SECRET_KEY=sk_live_...`
- `STRIPE_WEBHOOK_SECRET=whsec_...`
- `STRIPE_CHECKOUT_SUCCESS_URL=https://<your-domain>/settings/billing?checkout=success`
- `STRIPE_CHECKOUT_CANCEL_URL=https://<your-domain>/settings/billing?checkout=canceled`
- `STRIPE_PORTAL_RETURN_URL=https://<your-domain>/settings/billing`
- `STRIPE_PRICE_ID=price_...` (optional default across plans)
- `STRIPE_PRICE_ID_STARTER=price_...`
- `STRIPE_PRICE_ID_PRO=price_...`
- `STRIPE_PRICE_ID_ENTERPRISE=price_...`
- `STRIPE_WEBHOOK_PATH=/api/v1/billing/stripe/webhook`
- `AGENT_TRIAL_DAYS=14`
- `AGENT_RATE_LIMIT_COMPANY_PER_MINUTE=30`
- `AGENT_RATE_LIMIT_COMPANY_PER_HOUR=600`
- `AGENT_RATE_LIMIT_COMPANY_PER_DAY=5000`
- `AGENT_RATE_LIMIT_USER_PER_MINUTE=12`
- `AGENT_RATE_LIMIT_USER_PER_HOUR=240`

Restart the API service after changes.

## 2) Create Products and Prices in Stripe

In Stripe Dashboard:

1. Go to `Product catalog`.
2. Create one product per app plan (Starter, Pro, Enterprise).
3. Add a recurring price for each plan (monthly or annual).
4. Copy each `price_...` ID into the matching env var above.

Use test prices in test mode first, then repeat in live mode with live prices.

## 3) Configure Customer Portal

In Stripe Dashboard:

1. Go to `Settings` -> `Billing` -> `Customer portal`.
2. Enable customer updates needed by your policy:
   - payment method updates
   - invoice history access
   - subscription cancellation/reactivation
3. Save configuration.

VeloBid will use `STRIPE_PORTAL_RETURN_URL` as the return location.

## 4) Configure Webhook Endpoint

In Stripe Dashboard:

1. Go to `Developers` -> `Webhooks`.
2. Add endpoint:
   - URL: `https://<your-domain><STRIPE_WEBHOOK_PATH>`
   - Example: `https://velobid.example.com/api/v1/billing/stripe/webhook`
3. Subscribe to events:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.paid`
   - `invoice.payment_failed`
4. Save endpoint and copy the signing secret (`whsec_...`) into `STRIPE_WEBHOOK_SECRET`.

Only accept signed webhook payloads. Do not process unsigned events.

## 5) Validate End-to-End

In Stripe test mode:

1. Start a Checkout session from VeloBid billing UI.
2. Complete payment with a Stripe test card.
3. Confirm VeloBid marks account as active on `checkout.session.completed`.
4. Open Customer Portal and test update/cancel flows.
5. Verify webhook deliveries are `2xx` in Stripe Dashboard.

Before production launch:

- Confirm all keys are live-mode keys.
- Confirm live-mode webhook endpoint and secret are set.
- Confirm plan-to-price mapping is correct for all plans.

## 6) Operations and Security

- Rotate `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` during planned maintenance windows.
- Keep secrets only in `/srv/velobid/secrets/velobid.env` with restricted file permissions.
- Monitor webhook failures and alert if retries exceed normal levels.

## 7) Agent Trial and Rate Limits

- VeloBid enforces agent access by subscription/trial status on authenticated requests.
- If a bidder has no Stripe status yet, a local trial starts automatically on first agent request and expires after `AGENT_TRIAL_DAYS`.
- When trial expires and there is no active Stripe subscription state, agent requests return `402`.
- Rate-limited requests return `429` with a `Retry-After` header.
