"""Email service for sending notifications."""

import smtplib
from email.message import EmailMessage
import logging

from ...settings.base import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


async def send_email(to_email: str, subject: str, body: str):
    """
    Sends an email using SMTP settings from the environment.

    Args:
        to_email: The recipient's email address.
        subject: The email subject.
        body: The email body content.
    """
    if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD]):
        logger.error("SMTP settings are not configured. Cannot send email.")
        # In a real scenario, you might raise an exception or just log and return
        return

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_SENDER_EMAIL
    msg["To"] = to_email

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            logger.info(f"Email sent successfully to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")


async def send_welcome_email(
    to_email: str,
    first_name: str,
    username: str,
    default_password: str,
    reset_token: str,
):
    """Sends a welcome email with credentials and a reset link."""
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    subject = "Welcome to HotelAgent"
    body = f"""
Hi {first_name},

Your account has been created successfully.

Username: {username}
One-Time Password: {default_password}

Please reset your password using the link below. This link is valid for 24 hours.
{reset_url}

Thank you,
The HotelAgent Team
"""
    await send_email(to_email, subject, body)


async def send_forgot_password_email(to_email: str, first_name: str, reset_token: str):
    """Sends a password reset link for the forgot password flow."""
    reset_url = f"{settings.FRONTEND_URL}/reset-password-forgot?token={reset_token}"
    subject = "Reset Your HotelAgent Password"
    body = f"""
Hi {first_name},

We received a request to reset your password. Please use the link below to set a new password. This link is valid for 24 hours.
{reset_url}

If you did not request a password reset, please ignore this email.

Thank you,
The HotelAgent Team
"""
    await send_email(to_email, subject, body)