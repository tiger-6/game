import os
from dotenv import load_dotenv

load_dotenv()

# Eurostar station codes (UIC)
STATIONS = {
    "Paris Gare du Nord": "8727100",
    "London St Pancras": "7015400",
}

# Trip details
ORIGIN = STATIONS["Paris Gare du Nord"]
DESTINATION = STATIONS["London St Pancras"]
OUTBOUND_DATE = "2026-04-24"  # Apr 24, 2026
INBOUND_DATE = "2026-04-26"   # Apr 26, 2026

# Preferred time windows (24h format)
OUTBOUND_TIME_MIN = 12  # afternoon
OUTBOUND_TIME_MAX = 20
INBOUND_TIME_MIN = 16   # around 5-6 PM
INBOUND_TIME_MAX = 19

# Eurostar search URL
SEARCH_URL = (
    "https://www.eurostar.com/search/uk-en"
    f"?origin={ORIGIN}&destination={DESTINATION}"
    f"&adult=1&youth=&child=&senior=&infant="
    f"&outbound={OUTBOUND_DATE}&inbound={INBOUND_DATE}"
)

# SMTP email settings
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")

# Telegram settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Monitor settings
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "30"))
PRICE_THRESHOLD = float(os.getenv("PRICE_THRESHOLD", "0"))
