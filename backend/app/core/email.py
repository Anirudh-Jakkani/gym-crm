"""Outgoing email. The provider is chosen by settings.email_provider."""

import asyncio
import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage as MimeMessage
from email.utils import formataddr
from typing import Protocol

import httpx

from app.core.config import settings

log = logging.getLogger("gym_crm.email")


@dataclass
class Email:
    to: str
    subject: str
    text: str
    from_name: str
    reply_to: str | None = None


class EmailError(Exception):
    pass


class EmailSender(Protocol):
    async def send(self, email: Email) -> None: ...


class ConsoleSender:
    """Development: logs the message instead of sending it."""

    async def send(self, email: Email) -> None:
        log.warning(
            "EMAIL (console, not sent) to=%s subject=%r\n%s", email.to, email.subject, email.text
        )


class SmtpSender:
    async def send(self, email: Email) -> None:
        msg = MimeMessage()
        msg["From"] = formataddr((email.from_name, settings.email_from_address))
        msg["To"] = email.to
        msg["Subject"] = email.subject
        if email.reply_to:
            msg["Reply-To"] = email.reply_to
        msg.set_content(email.text)

        def _send() -> None:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
                if settings.smtp_starttls:
                    smtp.starttls()
                if settings.smtp_username:
                    smtp.login(settings.smtp_username, settings.smtp_password or "")
                smtp.send_message(msg)

        try:
            await asyncio.to_thread(_send)
        except (smtplib.SMTPException, OSError) as exc:
            raise EmailError(str(exc)) from exc


class ResendSender:
    async def send(self, email: Email) -> None:
        payload = {
            "from": formataddr((email.from_name, settings.email_from_address)),
            "to": [email.to],
            "subject": email.subject,
            "text": email.text,
        }
        if email.reply_to:
            payload["reply_to"] = email.reply_to
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                res = await client.post(
                    "https://api.resend.com/emails",
                    json=payload,
                    headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                )
        except httpx.HTTPError as exc:
            raise EmailError(str(exc)) from exc
        if res.status_code >= 300:
            raise EmailError(f"Resend {res.status_code}: {res.text[:300]}")


def get_sender() -> EmailSender:
    match settings.email_provider:
        case "smtp":
            return SmtpSender()
        case "resend":
            return ResendSender()
        case _:
            return ConsoleSender()
