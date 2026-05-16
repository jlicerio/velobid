"""Email delivery module.

Sends transactional emails (verification, password reset) via SMTP.
Falls back to console logging when SMTP credentials are not configured.

SMTP configuration via environment variables:
  SMTP_HOST            — SMTP server hostname (default: "")
  SMTP_PORT            — SMTP server port (default: 587)
  SMTP_USERNAME        — SMTP username (default: "")
  SMTP_PASSWORD        — SMTP password (default: "")
  SMTP_USE_TLS         — enable STARTTLS (default: "true")
  EMAIL_FROM           — sender address (default: "noreply@nexgenexpert.com")
  EMAIL_FROM_NAME      — sender display name (default: "VeloBid")
  VERIFICATION_BASE_URL  — base URL for verification links (default: from settings or fallback)
  PASSWORD_RESET_BASE_URL — base URL for password reset links
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── helpers ─────────────────────────────────────────────────────────────────


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _bool_env(key: str, default: bool = True) -> bool:
    val = os.environ.get(key, "").strip().lower()
    if val in ("1", "true", "yes", "on"):
        return True
    if val in ("0", "false", "no", "off"):
        return False
    return default


def _build_html(subject: str, body: str, link: str, link_label: str = "") -> str:
    """Build a minimal styled HTML email."""
    label = link_label or link
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f5f5">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:40px 0">
<table role="presentation" width="480" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.12)">
<tr><td style="padding:32px 32px 16px">
<h1 style="font-size:20px;margin:0 0 8px;color:#1a1a2e">{subject}</h1>
<p style="font-size:15px;line-height:1.5;color:#555;margin:0 0 20px">{body}</p>
<table role="presentation" cellpadding="0" cellspacing="0">
<tr><td style="border-radius:6px;background:#2563eb;padding:12px 24px">
<a href="{link}" target="_blank" style="color:#fff;text-decoration:none;font-size:15px;font-weight:600">{label}</a>
</td></tr>
</table>
</td></tr>
<tr><td style="padding:16px 32px 24px;border-top:1px solid #eee;font-size:12px;color:#999">
<p style="margin:0">VeloBid — Construction Estimating Platform</p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


# ── SMTP sender ─────────────────────────────────────────────────────────────


def _smtp_configured() -> bool:
    """Return True if SMTP env vars are set enough to attempt sending."""
    return bool(_env("SMTP_HOST") and _env("SMTP_USERNAME"))


async def _send_via_smtp(
    to_email: str,
    subject: str,
    html_body: str,
) -> None:
    """Send an HTML email via SMTP using aiosmtplib."""
    import aiosmtplib

    host = _env("SMTP_HOST", "smtp.gmail.com")
    port = int(_env("SMTP_PORT", "587"))
    username = _env("SMTP_USERNAME", "")
    password = _env("SMTP_PASSWORD", "")
    use_tls = _bool_env("SMTP_USE_TLS", True)
    from_name = _env("EMAIL_FROM_NAME", "VeloBid")
    from_addr = _env("EMAIL_FROM", "noreply@nexgenexpert.com")

    # Build MIME message
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{from_name} <{from_addr}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["X-Mailer"] = "VeloBid"
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=host,
            port=port,
            username=username,
            password=password,
            use_tls=use_tls,
            timeout=15,
        )
        logger.info("Email sent to %s — subject=%s", to_email, subject)
    except Exception:
        logger.exception("SMTP send to %s failed", to_email)
        raise


# ── public API (same signatures as original MVP module) ─────────────────────


def send_verification_email(to_email: str, token: str) -> None:
    """Send an email verification link.

    Uses SMTP when configured; falls back to console logging.
    """
    base_url = _env(
        "VERIFICATION_BASE_URL",
        "https://velobid.tailfceaca.ts.net/api/v1/auth/email/verify",
    )
    link = f"{base_url}?token={token}"

    if not _smtp_configured():
        logger.info(
            "Sending verification email to %s\n"
            "  Subject: Please verify your email address\n"
            "  Body:\n"
            "    Thank you for signing up!\n"
            "    Please verify your email address by clicking the link below:\n"
            "    %s\n"
            "    This link will expire shortly.",
            to_email,
            link,
        )
        return

    import asyncio

    subject = "Verify your email — VeloBid"
    body = (
        "Thank you for signing up! Please verify your email address "
        "by clicking the button below."
    )
    html = _build_html(subject, body, link, "Verify Email Address")

    try:
        asyncio.create_task(_send_via_smtp(to_email, subject, html))
        logger.info("Queued verification email for %s via SMTP", to_email)
    except Exception:
        logger.exception(
            "Failed to queue verification email to %s — fallback to console",
            to_email,
        )
        logger.info(
            "VERIFICATION LINK (console fallback): %s\n  Token: %s",
            link,
            token,
        )


def send_password_reset_email(to_email: str, token: str) -> None:
    """Send a password reset link.

    Uses SMTP when configured; falls back to console logging.
    """
    base_url = _env(
        "PASSWORD_RESET_BASE_URL",
        "https://velobid.tailfceaca.ts.net/api/v1/auth/password/reset",
    )
    link = f"{base_url}?token={token}"

    if not _smtp_configured():
        logger.info(
            "Sending password reset email to %s\n"
            "  Subject: Password reset requested\n"
            "  Body:\n"
            "    You have requested to reset your password.\n"
            "    Click the link below to set a new password:\n"
            "    %s\n"
            "    If you did not request this, you can safely ignore this email.",
            to_email,
            link,
        )
        return

    import asyncio

    subject = "Reset your password — VeloBid"
    body = (
        "You have requested to reset your password. "
        "Click the button below to set a new password. "
        "If you did not request this, you can safely ignore this email."
    )
    html = _build_html(subject, body, link, "Reset Password")

    try:
        asyncio.create_task(_send_via_smtp(to_email, subject, html))
        logger.info("Queued password reset email for %s via SMTP", to_email)
    except Exception:
        logger.exception(
            "Failed to queue password reset email to %s — fallback to console",
            to_email,
        )
        logger.info(
            "PASSWORD RESET LINK (console fallback): %s\n  Token: %s",
            link,
            token,
        )
