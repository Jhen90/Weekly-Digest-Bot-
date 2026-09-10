import smtplib
from email.message import EmailMessage
import logging

log = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587  # STARTTLS

def send_email(
    html: str,
    text: str,
    subject: str,
    sender: str,
    recipient: str,
    app_password: str,
) -> bool:
    """
    Send email via Gmail SMTP.
    Returns True on success, False on recoverable errors, raises on fatal errors.
    """
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient

        msg.set_content(text)
        msg.add_alternative(html, subtype="html")

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=60) as smtp:
            smtp.starttls()
            smtp.login(sender, app_password)
            smtp.send_message(msg)

        log.info(f"✓ Email sent to {recipient}")
        return True

    except smtplib.SMTPAuthenticationError:
        log.error("Gmail authentication failed. Check GMAIL_APP_PASSWORD.")
        raise
    except Exception as e:
        log.error(f"Failed to send email: {e}")
        raise
