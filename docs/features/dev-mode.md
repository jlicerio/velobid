# Dev Mode

**Purpose:** Bypass email verification and TOTP setup during development,
allowing instant account creation and login via the signup endpoint.

**Flag:** `DEV_MODE=true` in `.env`

---

## How It Works

When `DEV_MODE=true`, the `POST /auth/signup/start` endpoint performs the
full signup flow synchronously and returns auth tokens immediately:

| Step | Normal flow | Dev mode |
|------|-------------|----------|
| 1. Create pending signup | Done | Done |
| 2. Send verification email | Sent (or logged) | Skipped |
| 3. Email verification user clicks link | Must | Auto-verified |
| 4. TOTP 2FA setup user scans QR | Must | Auto-generated + confirmed |
| 5. Account activated | Manual steps 3+4 | Inline, immediately |

**Response:** The API returns the normal `SignupStartResponse` plus a
`dev_access_token` field when dev mode is active.

---

## `.env` Configuration

```ini
# Enable dev mode (bypass email verification + 2FA)
DEV_MODE=true
```

---

## Usage

### Signup (returns token immediately)

```bash
curl -X POST https://velobid.tailfceaca.ts.net/api/v1/auth/signup/start \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Co",
    "primary_contact": "Test User",
    "admin_email": "test@example.com",
    "password": "testpass123",
    "accept_terms": true
  }'
```

Response (dev mode):

```json
{
  "signup_id": "...",
  "email": "te***@example.com",
  "message": "Verification email sent. Please check your inbox.",
  "expires_in_minutes": 30,
  "dev_access_token": "eyJ...",
  "dev_refresh_token": "eyJ..."
}
```

Use `dev_access_token` for all authenticated API calls.

### Login (works normally, no 2FA challenge)

```bash
curl -X POST https://velobid.tailfceaca.ts.net/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'
```

Because the status is already `active`, login returns tokens directly
without a 2FA challenge (no TOTP was enabled).

---

## Implementation

### `api/services/auth.py` — `start_signup()`

After creating the `PendingSignup`, if `DEV_MODE=true`:

1. Verify the email token (bypass actual verification)
2. Generate a TOTP secret
3. Generate a valid TOTP code and confirm it
4. Set status to `active`, org_status to `active`
5. Issue access + refresh tokens
6. Return tokens in the response

### Turnstile

Turnstile verification is already auto-passed when `TURNSTILE_SECRET_KEY`
is not set (returns `True`). No additional change needed.

---

## Security Notes

- **Never** enable `DEV_MODE=true` in production
- Dev mode creates accounts with `two_factor_enabled=False`
- The `dev_access_token` is a standard JWT — same expiry as normal tokens
- Recovery codes are still generated and returned (save them for testing)
