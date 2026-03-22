"""Email and Telegram notification handlers."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

from config import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    EMAIL_TO,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)
from scraper import ScrapeResult, TrainOption

logger = logging.getLogger(__name__)


def _format_train(t: TrainOption) -> str:
    return f"{t.departure} → {t.arrival} ({t.duration}) | {t.currency}{t.price:.2f} {t.train_class}"


def _build_text_report(result: ScrapeResult) -> str:
    lines = ["=== Eurostar Price Alert ===\n"]

    if result.outbound:
        lines.append("OUTBOUND — Paris → London (Apr 24, afternoon):")
        for t in sorted(result.outbound, key=lambda x: x.price):
            lines.append(f"  {_format_train(t)}")
        if result.cheapest_outbound:
            lines.append(
                f"  >> Cheapest: {result.cheapest_outbound.currency}"
                f"{result.cheapest_outbound.price:.2f} "
                f"at {result.cheapest_outbound.departure}"
            )
    else:
        lines.append("OUTBOUND: No trains found in the afternoon window.")

    lines.append("")

    if result.inbound:
        lines.append("INBOUND — London → Paris (Apr 26, ~5-6 PM):")
        for t in sorted(result.inbound, key=lambda x: x.price):
            lines.append(f"  {_format_train(t)}")
        if result.cheapest_inbound:
            lines.append(
                f"  >> Cheapest: {result.cheapest_inbound.currency}"
                f"{result.cheapest_inbound.price:.2f} "
                f"at {result.cheapest_inbound.departure}"
            )
    else:
        lines.append("INBOUND: No trains found in the 5-6 PM window.")

    if result.total_cheapest is not None:
        lines.append(f"\nBEST ROUND-TRIP TOTAL: £{result.total_cheapest:.2f}")

    lines.append(f"\nBook here: {result.url}")
    return "\n".join(lines)


def _build_html_report(result: ScrapeResult) -> str:
    html = ["<h2>Eurostar Price Alert</h2>"]

    def _table(trains: list[TrainOption]) -> str:
        if not trains:
            return "<p><em>No trains found in time window.</em></p>"
        rows = ""
        for t in sorted(trains, key=lambda x: x.price):
            rows += (
                f"<tr><td>{t.departure}</td><td>{t.arrival}</td>"
                f"<td>{t.duration}</td>"
                f"<td><strong>{t.currency}{t.price:.2f}</strong></td>"
                f"<td>{t.train_class}</td></tr>"
            )
        return (
            "<table border='1' cellpadding='5' cellspacing='0'>"
            "<tr><th>Depart</th><th>Arrive</th><th>Duration</th>"
            "<th>Price</th><th>Class</th></tr>"
            f"{rows}</table>"
        )

    html.append("<h3>Outbound — Paris → London (Apr 24, afternoon)</h3>")
    html.append(_table(result.outbound))

    html.append("<h3>Inbound — London → Paris (Apr 26, ~5-6 PM)</h3>")
    html.append(_table(result.inbound))

    if result.total_cheapest is not None:
        html.append(
            f"<p><strong>Best round-trip total: £{result.total_cheapest:.2f}</strong></p>"
        )

    html.append(f'<p><a href="{result.url}">Book on Eurostar</a></p>')
    return "\n".join(html)


def send_email(result: ScrapeResult) -> bool:
    """Send price alert via email. Returns True on success."""
    if not all([SMTP_USER, SMTP_PASSWORD, EMAIL_TO]):
        logger.warning("Email not configured — skipping email notification.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = (
        f"Eurostar Alert: "
        f"{'£' + f'{result.total_cheapest:.0f}' if result.total_cheapest else 'New prices'}"
        f" — Paris↔London Apr 24-26"
    )
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_TO

    msg.attach(MIMEText(_build_text_report(result), "plain"))
    msg.attach(MIMEText(_build_html_report(result), "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, EMAIL_TO.split(","), msg.as_string())
        logger.info("Email sent to %s", EMAIL_TO)
        return True
    except Exception:
        logger.exception("Failed to send email")
        return False


def send_telegram(result: ScrapeResult) -> bool:
    """Send price alert via Telegram. Returns True on success."""
    if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        logger.warning("Telegram not configured — skipping Telegram notification.")
        return False

    text = _build_text_report(result)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    try:
        resp = requests.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        resp.raise_for_status()
        logger.info("Telegram message sent to chat %s", TELEGRAM_CHAT_ID)
        return True
    except Exception:
        logger.exception("Failed to send Telegram message")
        return False


def notify(result: ScrapeResult) -> None:
    """Send notifications via all configured channels."""
    send_email(result)
    send_telegram(result)
