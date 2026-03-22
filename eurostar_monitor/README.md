# Eurostar Price Monitor

Monitors Eurostar train ticket prices for a Paris Gare du Nord → London St Pancras round trip and sends alerts via **email** and **Telegram** when prices change.

## Trip Details (configured in `config.py`)

| Leg      | Route                | Date       | Time Window   |
|----------|----------------------|------------|---------------|
| Outbound | Paris → London       | Apr 24, 2026 | Afternoon (12-20h) |
| Inbound  | London → Paris       | Apr 26, 2026 | ~5-6 PM (16-19h)   |

## Setup

### 1. Install dependencies

```bash
cd eurostar_monitor
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

#### Email (Gmail example)
1. Enable 2FA on your Google account
2. Create an App Password at https://myaccount.google.com/apppasswords
3. Set `SMTP_USER`, `SMTP_PASSWORD`, and `EMAIL_TO` in `.env`

#### Telegram
1. Message [@BotFather](https://t.me/BotFather) on Telegram → `/newbot` → copy the token
2. Start a chat with your bot and send any message
3. Get your chat ID: `curl https://api.telegram.org/bot<TOKEN>/getUpdates`
4. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`

### 3. Run

```bash
# Continuous monitoring (default: every 30 min)
python monitor.py

# One-time scrape (no notifications)
python scraper.py
```

## Configuration

| Env Variable             | Default          | Description                        |
|--------------------------|------------------|------------------------------------|
| `CHECK_INTERVAL_MINUTES` | `30`             | Minutes between checks             |
| `PRICE_THRESHOLD`        | `0` (disabled)   | Only notify if total below this £  |
| `SMTP_HOST`              | `smtp.gmail.com` | SMTP server                        |
| `SMTP_PORT`              | `587`            | SMTP port                          |
| `SMTP_USER`              |                  | Email sender address               |
| `SMTP_PASSWORD`          |                  | Email password / app password      |
| `EMAIL_TO`               |                  | Recipient(s), comma-separated      |
| `TELEGRAM_BOT_TOKEN`     |                  | Telegram bot token from BotFather  |
| `TELEGRAM_CHAT_ID`       |                  | Your Telegram chat ID              |

## Notification Logic

- **First run**: Always sends a notification with current prices
- **Price drop**: Notifies immediately
- **Price increase > 10%**: Notifies as a warning
- **Threshold**: If `PRICE_THRESHOLD` is set, suppresses notifications when price is above it

## Debugging

If no trains are found, check:
- `eurostar_debug.png` — screenshot of the page state
- `eurostar_debug.html` — raw HTML of the page
- `eurostar_monitor.log` — application logs
