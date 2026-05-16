# Social Login (OAuth) Implementation Plan

**Status:** Work tree / future option (Option C)
**Priority:** Post-MVP
**Depends on:** Google/Microsoft OAuth app registration, domain verification

---

## Overview

Add OAuth-based social login via Google and Microsoft to the current `POST /auth/signup/start` + 2FA flow.
The backend already has placeholder social routes at `api/routers/auth.py` — the social router was removed but the signup page references Google/Microsoft buttons.

**Auth flow (proposed):**

```
[User clicks "Sign in with Google"]
  -> GET /auth/oauth/google/login
  -> Redirect to Google OAuth consent screen
  -> User approves -> callback to GET /auth/oauth/google/callback
  -> Backend exchanges auth code for tokens
  -> Create/find user by email
  -> Issue VeloBid JWT
  -> Redirect to frontend with token
```

---

## File Changes

### 1. New router: `api/routers/oauth.py`

```
api/routers/oauth.py          # NEW — all OAuth endpoints
```

Endpoints:

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/auth/oauth/google/login` | Redirect to Google consent |
| GET | `/auth/oauth/google/callback` | Handle Google callback |
| GET | `/auth/oauth/microsoft/login` | Redirect to Microsoft consent |
| GET | `/auth/oauth/microsoft/callback` | Handle Microsoft callback |
| POST | `/auth/oauth/link` | Link OAuth to existing account |
| DELETE | `/auth/oauth/unlink/{provider}` | Unlink OAuth from account |

### 2. New service: `api/services/oauth.py`

```python
# OAuth client management
# Token exchange
# User creation/lookup by email
# Account linking
```

Functions:

- `get_google_oauth_url(state: str) -> str` — build Google consent URL
- `get_microsoft_oauth_url(state: str) -> str` — build Microsoft consent URL
- `exchange_google_code(code: str) -> dict` — exchange code for tokens
- `exchange_microsoft_code(code: str) -> dict` — exchange code for tokens
- `get_user_info_from_google(tokens: dict) -> dict` — get email/name from Google
- `get_user_info_from_microsoft(tokens: dict) -> dict` — get email/name from Microsoft
- `find_or_create_oauth_user(email: str, name: str, provider: str, provider_id: str) -> dict`
- `link_oauth_to_user(user_id: str, provider: str, provider_id: str) -> None`

### 3. Config additions: `.env`

```
# ── OAuth (Google) ──
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=https://velobid.tailfceaca.ts.net/api/v1/auth/oauth/google/callback

# ── OAuth (Microsoft) ──
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
MICROSOFT_REDIRECT_URI=https://velobid.tailfceaca.ts.net/api/v1/auth/oauth/microsoft/callback
MICROSOFT_TENANT=common          # or a specific tenant ID
```

### 4. Schema additions: `api/schemas/auth.py`

```python
class OAuthLoginUrlResponse(BaseModel):
    url: str
    state: str

class OAuthCallbackResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str
    email: str
    is_new_user: bool
```

### 5. Frontend: `frontend/src/` (login page, callback handler)

- Login buttons call `GET /auth/oauth/google/login` and redirect
- Callback page extracts token from URL query param
- Links to existing account flow (merge)

### 6. Requirements: `requirements.txt`

Add:

```
authlib>=1.3,<2.0       # OAuth client (handles state, PKCE, token exchange)
# OR httpx + manual OAuth flow (no extra dep but more code)
```

---

## Provider Setup Checklist

### Google

1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID (Web application)
3. Authorized redirect URI: `https://velobid.tailfceaca.ts.net/api/v1/auth/oauth/google/callback`
4. Copy Client ID + Client Secret to `.env`
5. Enable Google+ API / People API

### Microsoft

1. Go to https://portal.azure.com -> App registrations
2. Register a new app
3. Set redirect URI: `https://velobid.tailfceaca.ts.net/api/v1/auth/oauth/microsoft/callback`
4. Copy Application (client) ID + client secret to `.env`
5. Set supported account type (single/multi-tenant)

---

## Implementation Order

| Step | What | Who |
|------|------|-----|
| 1 | Register OAuth apps (Google + Microsoft) | Human |
| 2 | Add config vars + update `.env` | Dev |
| 3 | Write `oauth.py` service (token exchange, user lookup) | Dev |
| 4 | Write `oauth.py` router (login redirect, callback, link) | Dev |
| 5 | Wire router into `api/main.py` | Dev |
| 6 | Add callback page to frontend | Dev |
| 7 | Test Google login end-to-end | Both |
| 8 | Test Microsoft login end-to-end | Both |
| 9 | Test account linking | Both |

---

## Notes

- **State parameter:** OAuth login uses a random state parameter stored server-side (in-memory or session) to prevent CSRF. Clean up expired states periodically.
- **Account linking:** A user who signs up via email can later link a Google/Microsoft account using `POST /auth/oauth/link` (requires auth).
- **Email match:** If the OAuth email matches an existing VeloBid account, prompt to link or ask for password confirmation.
- **Token expiry:** Access tokens expire after 1 hour (Google) or variable (Microsoft). Use refresh tokens where available.
- **No 2FA on OAuth login:** Users authenticated via OAuth skip VeloBid's TOTP challenge — the provider handles MFA.
- **Dev testing:** For local dev, use `localhost` redirect URIs in the OAuth app settings.
