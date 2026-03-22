#!/usr/bin/env python3
"""Eurostar price monitor — main entry point.

Periodically scrapes Eurostar for Paris→London round-trip prices
and sends alerts via email and Telegram.
"""

import logging
import sys
import time
from datetime import datetime

from config import CHECK_INTERVAL_MINUTES, PRICE_THRESHOLD
from scraper import scrape_prices
from notifier import notify

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("eurostar_monitor.log"),
    ],
)
logger = logging.getLogger(__name__)

last_cheapest: float | None = None


def check_once() -> None:
    """Run a single price check and notify if appropriate."""
    global last_cheapest

    logger.info("--- Price check at %s ---", datetime.now().strftime("%Y-%m-%d %H:%M"))

    try:
        result = scrape_prices()
    except Exception:
        logger.exception("Scrape failed")
        return

    if not result.outbound and not result.inbound:
        logger.warning("No trains found. Will retry next cycle.")
        return

    current = result.total_cheapest
    logger.info("Cheapest round-trip: %s", f"£{current:.2f}" if current else "N/A")

    should_notify = False

    # Always notify on first successful scrape
    if last_cheapest is None:
        should_notify = True
    # Notify if price dropped
    elif current is not None and current < last_cheapest:
        logger.info("Price DROP: £%.2f → £%.2f", last_cheapest, current)
        should_notify = True
    # Notify if price went up significantly (>10%)
    elif current is not None and current > last_cheapest * 1.1:
        logger.info("Price INCREASE: £%.2f → £%.2f", last_cheapest, current)
        should_notify = True

    # Threshold filter
    if PRICE_THRESHOLD > 0 and current is not None and current > PRICE_THRESHOLD:
        logger.info("Price £%.2f above threshold £%.2f — suppressing notification.", current, PRICE_THRESHOLD)
        should_notify = False

    if should_notify:
        notify(result)
    else:
        logger.info("No significant change — skipping notification.")

    if current is not None:
        last_cheapest = current


def main() -> None:
    logger.info("Eurostar Price Monitor started")
    logger.info("Checking every %d minutes", CHECK_INTERVAL_MINUTES)
    logger.info("Price threshold: %s", f"£{PRICE_THRESHOLD:.0f}" if PRICE_THRESHOLD else "disabled")

    while True:
        check_once()
        logger.info("Next check in %d minutes...", CHECK_INTERVAL_MINUTES)
        time.sleep(CHECK_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    main()
