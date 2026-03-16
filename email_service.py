from __future__ import annotations
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.shared.config.settings import settings

log = logging.getLogger("email")


class EmailService:
    def _send(self, to: str, subject: str, html: str):
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
            msg["To"] = to
            msg.attach(MIMEText(html, "html"))
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
                if settings.SMTP_USE_TLS:
                    s.starttls()
                s.login(settings.SMTP_USER, settings.SMTP_PASS)
                s.sendmail(settings.EMAIL_FROM, to, msg.as_string())
            log.info("Email sent to %s", to)
        except Exception as e:
            log.error("Email failed: %s", e)

    def send_verification_email(self, to: str, token: str):
        url = f"{settings.APP_BASE_URL}/verify-email?token={token}"
        self._send(to, "Verify your Dacexy account", f"""
        <h2>Welcome to Dacexy!</h2>
        <p>Click below to verify your email address:</p>
        <a href="{url}" style="background:#6366f1;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;">Verify Email</a>
        <p>Or copy this link: {url}</p>
        """)

    def send_password_reset(self, to: str, token: str):
        url = f"{settings.APP_BASE_URL}/reset-password?token={token}"
        self._send(to, "Reset your Dacexy password", f"""
        <h2>Password Reset</h2>
        <p>Click below to reset your password:</p>
        <a href="{url}" style="background:#6366f1;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;">Reset Password</a>
        <p>This link expires in 1 hour.</p>
        """)
