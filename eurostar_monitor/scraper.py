"""Eurostar price scraper using Playwright."""

import json
import logging
import os
import re
from dataclasses import dataclass
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from config import (
    SEARCH_URL,
    OUTBOUND_TIME_MIN,
    OUTBOUND_TIME_MAX,
    INBOUND_TIME_MIN,
    INBOUND_TIME_MAX,
)

logger = logging.getLogger(__name__)


@dataclass
class TrainOption:
    departure: str  # e.g. "14:30"
    arrival: str
    duration: str
    price: float
    currency: str
    train_class: str  # Standard / Standard Premier / Business Premier


@dataclass
class ScrapeResult:
    outbound: list[TrainOption]
    inbound: list[TrainOption]
    cheapest_outbound: TrainOption | None
    cheapest_inbound: TrainOption | None
    total_cheapest: float | None
    url: str


def _parse_time_hour(time_str: str) -> int:
    """Extract hour from time string like '14:30'."""
    match = re.match(r"(\d{1,2})", time_str)
    return int(match.group(1)) if match else 0


def _in_time_window(time_str: str, t_min: int, t_max: int) -> bool:
    hour = _parse_time_hour(time_str)
    return t_min <= hour <= t_max


def _extract_trains_from_page(page) -> list[TrainOption]:
    """Extract train options from the currently visible results on the page."""
    trains = []

    # Try to intercept API responses for structured data
    # Eurostar loads results dynamically — we parse the rendered DOM
    cards = page.query_selector_all(
        "[class*='journey-list'] [class*='journey-card'], "
        "[class*='JourneyList'] [class*='JourneyCard'], "
        "[data-testid*='journey'], "
        "[class*='train-card'], "
        "[class*='outbound-journey'] li, "
        "[class*='result']"
    )

    if not cards:
        # Broader fallback: look for any element with price-like content
        cards = page.query_selector_all("[class*='journey'], [class*='Journey']")

    for card in cards:
        try:
            text = card.inner_text()
            # Extract times — look for HH:MM patterns
            times = re.findall(r"\b(\d{1,2}:\d{2})\b", text)
            # Extract price — look for currency patterns
            price_match = re.search(
                r"[£€$]\s*(\d+(?:[.,]\d{2})?)|(\d+(?:[.,]\d{2})?)\s*[£€$]", text
            )
            if not price_match or len(times) < 2:
                continue

            price_str = price_match.group(1) or price_match.group(2)
            price = float(price_str.replace(",", "."))
            currency = "£" if "£" in text else ("€" if "€" in text else "$")

            # Duration
            dur_match = re.search(r"(\d+h\s*\d+m?|\d+:\d+)", text)
            duration = dur_match.group(0) if dur_match else ""

            # Class
            train_class = "Standard"
            if "Premier" in text and "Business" in text:
                train_class = "Business Premier"
            elif "Premier" in text:
                train_class = "Standard Premier"

            trains.append(
                TrainOption(
                    departure=times[0],
                    arrival=times[1],
                    duration=duration,
                    price=price,
                    currency=currency,
                    train_class=train_class,
                )
            )
        except (ValueError, IndexError):
            continue

    return trains


def _try_extract_from_network(responses: list) -> list[dict]:
    """Try to extract journey data from intercepted network responses."""
    journeys = []
    for resp in responses:
        try:
            if resp.status != 200:
                continue
            url = resp.url
            if "search" not in url.lower() and "journey" not in url.lower():
                continue
            body = resp.json()
            # Common Eurostar API response patterns
            for key in ("outbound", "inbound", "journeys", "results", "data"):
                if key in body and isinstance(body[key], list):
                    journeys.extend(body[key])
        except Exception:
            continue
    return journeys


def _parse_api_journeys(raw_journeys: list) -> list[TrainOption]:
    """Parse train options from intercepted API JSON."""
    trains = []
    for j in raw_journeys:
        try:
            dep = j.get("departureTime", j.get("departure", {}).get("time", ""))
            arr = j.get("arrivalTime", j.get("arrival", {}).get("time", ""))
            dur = j.get("duration", "")

            # Price can be nested in various ways
            price = None
            currency = "£"
            if "price" in j:
                p = j["price"]
                if isinstance(p, (int, float)):
                    price = float(p)
                elif isinstance(p, dict):
                    price = float(p.get("amount", p.get("value", 0)))
                    currency = p.get("currency", "£")
            elif "fares" in j and j["fares"]:
                fare = j["fares"][0]
                price = float(fare.get("price", fare.get("amount", 0)))
                currency = fare.get("currency", "£")

            if price and dep:
                trains.append(
                    TrainOption(
                        departure=dep[:5] if len(dep) >= 5 else dep,
                        arrival=arr[:5] if len(arr) >= 5 else arr,
                        duration=dur,
                        price=price,
                        currency=currency,
                        train_class="Standard",
                    )
                )
        except (ValueError, TypeError, KeyError):
            continue
    return trains


def scrape_prices() -> ScrapeResult:
    """Scrape Eurostar prices for the configured trip."""
    logger.info("Starting Eurostar price scrape...")
    logger.info("URL: %s", SEARCH_URL)

    captured_responses = []

    with sync_playwright() as p:
        # Use PLAYWRIGHT_CHROMIUM_PATH env var or auto-detect installed browser
        chromium_path = os.getenv("PLAYWRIGHT_CHROMIUM_PATH", "")
        if not chromium_path:
            # Auto-detect from Playwright cache
            cache_dir = os.path.expanduser("~/.cache/ms-playwright")
            if os.path.isdir(cache_dir):
                for entry in sorted(os.listdir(cache_dir), reverse=True):
                    if entry.startswith("chromium-"):
                        candidate = os.path.join(cache_dir, entry, "chrome-linux", "chrome")
                        if os.path.isfile(candidate):
                            chromium_path = candidate
                            break

        launch_kwargs = {"headless": True}
        if chromium_path:
            launch_kwargs["executable_path"] = chromium_path
            logger.info("Using Chromium at: %s", chromium_path)

        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="en-GB",
        )
        page = context.new_page()

        # Intercept API responses
        page.on(
            "response",
            lambda resp: captured_responses.append(resp)
            if any(
                kw in resp.url.lower()
                for kw in ("search", "journey", "availability", "train", "fare")
            )
            else None,
        )

        try:
            page.goto(SEARCH_URL, wait_until="networkidle", timeout=60000)

            # Accept cookies if dialog appears
            for selector in [
                "button[id*='accept']",
                "button[class*='accept']",
                "[data-testid*='accept']",
                "button:has-text('Accept')",
                "button:has-text('Got it')",
                "#onetrust-accept-btn-handler",
            ]:
                try:
                    btn = page.query_selector(selector)
                    if btn and btn.is_visible():
                        btn.click()
                        page.wait_for_timeout(1000)
                        break
                except Exception:
                    continue

            # Wait for results to load
            page.wait_for_timeout(5000)

            # Try waiting for journey results
            for selector in [
                "[class*='journey']",
                "[class*='Journey']",
                "[class*='result']",
                "[class*='train']",
            ]:
                try:
                    page.wait_for_selector(selector, timeout=10000)
                    break
                except PlaywrightTimeout:
                    continue

            page.wait_for_timeout(2000)

            # Strategy 1: Try to parse intercepted API responses
            raw_journeys = _try_extract_from_network(captured_responses)
            api_trains = _parse_api_journeys(raw_journeys) if raw_journeys else []

            # Strategy 2: Parse the rendered DOM
            dom_trains = _extract_trains_from_page(page)

            # Take a screenshot for debugging
            page.screenshot(path="eurostar_debug.png", full_page=True)

            # Use whichever strategy yielded more results
            all_trains = api_trains if len(api_trains) >= len(dom_trains) else dom_trains

            if not all_trains:
                logger.warning(
                    "No train data extracted. Check eurostar_debug.png for page state."
                )
                # Dump page content for debugging
                with open("eurostar_debug.html", "w", encoding="utf-8") as f:
                    f.write(page.content())

        except PlaywrightTimeout:
            logger.error("Timeout loading Eurostar search page")
            all_trains = []
        except Exception as exc:
            logger.error("Failed to load page: %s", exc)
            all_trains = []
        finally:
            browser.close()

    # Split into outbound / inbound based on time windows
    # If we can't distinguish, treat first half as outbound
    outbound = [
        t
        for t in all_trains
        if _in_time_window(t.departure, OUTBOUND_TIME_MIN, OUTBOUND_TIME_MAX)
    ]
    inbound = [
        t
        for t in all_trains
        if _in_time_window(t.departure, INBOUND_TIME_MIN, INBOUND_TIME_MAX)
    ]

    # If splitting didn't work, show all
    if not outbound and not inbound and all_trains:
        outbound = all_trains
        inbound = []

    cheapest_out = min(outbound, key=lambda t: t.price) if outbound else None
    cheapest_in = min(inbound, key=lambda t: t.price) if inbound else None

    total = None
    if cheapest_out and cheapest_in:
        total = cheapest_out.price + cheapest_in.price
    elif cheapest_out:
        total = cheapest_out.price

    return ScrapeResult(
        outbound=outbound,
        inbound=inbound,
        cheapest_outbound=cheapest_out,
        cheapest_inbound=cheapest_in,
        total_cheapest=total,
        url=SEARCH_URL,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = scrape_prices()
    print(f"\nOutbound trains ({len(result.outbound)}):")
    for t in result.outbound:
        print(f"  {t.departure} → {t.arrival} | {t.currency}{t.price} | {t.train_class}")
    print(f"\nInbound trains ({len(result.inbound)}):")
    for t in result.inbound:
        print(f"  {t.departure} → {t.arrival} | {t.currency}{t.price} | {t.train_class}")
    if result.total_cheapest:
        print(f"\nCheapest total: {result.total_cheapest}")
