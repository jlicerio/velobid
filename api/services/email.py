"""Lightweight email provider abstraction.

For MVP, emails are only logged to the console/logger.
Designed to be swapped with SendGrid/Postmark or similar later.
"""

import logging

logger = logging.getLogger(__name__)

VERIFICATION_BASE_URL = "http://localhost:8000/api/v1/auth/email/verify"
PASSWORD_RESET_BASE_URL = "http://localhost:8000/api/v1/auth/password/reset"


def send_verification_email(to_email: str, token: str) -> None:
    """Send an email verification message.

    For MVP this simply logs the email to the console.
    """
    link = f"{VERIFICATION_BASE_URL}?token={token}"
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


def send_password_reset_email(to_email: str, token: str) -> None:
    """Send a password reset email.

    For MVP this simply logs the email to the console.
    """
    link = f"{PASSWORD_RESET_BASE_URL}?token={token}"
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
