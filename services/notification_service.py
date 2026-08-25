import logging
from email.message import EmailMessage
from typing import Optional

import aiosmtplib

from config import settings
from models import Appointment, Barber, Service

logger = logging.getLogger(__name__)


def _is_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_FROM)


async def send_email(to: str, subject: str, body: str) -> None:
    if not _is_configured():
        logger.info("SMTP not configured, would send email to %s: %s\n%s", to, subject, body)
        return

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=settings.SMTP_USE_TLS,
        )
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc)


async def send_appointment_confirmation(appointment: Appointment, service: Service, barber: Barber) -> None:
    body = (
        f"Hello, {appointment.client_name}!\n\n"
        f"You're booked with {barber.display_name} for \"{service.name}\".\n"
        f"Date and time: {appointment.start_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"If your plans have changed, please contact the barbershop."
    )
    await send_email(appointment.client_email, "Booking confirmation", body)


async def send_appointment_cancellation(
    appointment: Appointment, service: Service, barber: Barber, reason: Optional[str] = None
) -> None:
    body = (
        f"Hello, {appointment.client_name}!\n\n"
        f"Unfortunately, your booking with {barber.display_name} for \"{service.name}\" "
        f"({appointment.start_at.strftime('%d.%m.%Y %H:%M')}) has been cancelled.\n"
    )
    if reason:
        body += f"Reason: {reason}\n"
    body += "\nWe apologize for the inconvenience."
    await send_email(appointment.client_email, "Booking cancelled", body)
