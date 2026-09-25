import smtplib
from email.message import EmailMessage

from app.core.config import settings

EMAIL_OUTBOX: list[dict[str, str]] = []


def send_email(to_address: str, subject: str, body: str) -> None:
    if not settings.SMTP_HOST:
        EMAIL_OUTBOX.append({"to": to_address, "subject": subject, "body": body})
        return
    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        smtp.starttls()
        if settings.SMTP_USERNAME:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)
