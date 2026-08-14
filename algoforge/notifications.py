"""Gmail SMTP notification hook."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from algoforge.config import Settings
from algoforge.models import ForgeResult

log = logging.getLogger(__name__)


def send_daily_reminder(result: ForgeResult, settings: Settings) -> None:
    """Send an email reminder that the daily DSA problem is ready."""
    if not settings.gmail_address or not settings.gmail_app_password:
        log.warning("Skipping email reminder: GMAIL_ADDRESS or GMAIL_APP_PASSWORD not set.")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = settings.gmail_address
        msg["To"] = settings.gmail_address
        msg["Subject"] = f"AlgoForge Daily: {result.problem.title} [{result.problem.difficulty}]"

        body = (
            f"Your daily DSA problem is ready!\n\n"
            f"Title: {result.problem.title}\n"
            f"Difficulty: {result.problem.difficulty}\n"
            f"Topics: {', '.join(result.problem.topics) if result.problem.topics else 'N/A'}\n\n"
            f"The Master Agent has written optimal solutions in both Java and Python, "
            f"and explained the real-world company patterns.\n\n"
            f"Open your Study Deck to review it and maintain your streak:\n"
            f"http://localhost:5173/study/{result.problem.slug_folder}\n\n"
            f"Happy forging!"
        )
        msg.attach(MIMEText(body, "plain"))

        # Connect to Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(settings.gmail_address, settings.gmail_app_password)
            server.send_message(msg)

        log.info("Successfully sent daily reminder email to %s", settings.gmail_address)
    except Exception as e:
        log.error("Failed to send email reminder: %s", e)
