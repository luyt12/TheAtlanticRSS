# New Yorker Daily Email

Automated daily email digest of The New Yorker articles, summarized in Chinese via Kimi K2.5 AI.

## How It Works

1. Fetches latest articles from The New Yorker RSS feed
2. Filters for today's articles (US Eastern Time)
3. Generates Chinese summaries using Kimi K2.5 (NVIDIA API)
4. Sends a formatted HTML email daily

## Schedule

Runs automatically every day at 03:00 UTC via GitHub Actions.

## Setup

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `KIMI_API_KEY` | Kimi K2.5 API key (NVIDIA endpoint) |
| `SMTP_PASS` | SMTP password / app password |
| `EMAIL_TO` | Recipient email address |
| `EMAIL_FROM` | Sender email address |
| `SMTP_HOST` | SMTP server hostname |
| `SMTP_PORT` | SMTP server port |
| `SMTP_USER` | SMTP login username |

### Manual Trigger

Go to **Actions** tab → **Daily New Yorker Email** → **Run workflow**.

## Tech Stack

- Python 3.11
- GitHub Actions (scheduled)
- Kimi K2.5 via NVIDIA API
- feedparser for RSS parsing
- SMTP over TLS (port 465)
