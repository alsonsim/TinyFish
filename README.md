# TinyFish Financial Agent

TinyFish Financial Agent is a local market-sentiment dashboard that combines TinyFish browser automation, OpenAI-backed analysis, and a lightweight web UI to turn news coverage into trading signals, watchlist updates, portfolio views, alerts, and conversational summaries.

## What It Does

- Runs one-shot sentiment scans for comma-separated ticker symbols.
- Collects and normalizes market news, with the current agent prioritizing Yahoo Finance Singapore and Bloomberg Asia.
- Uses OpenAI when available for planning, sentiment extraction, and chat responses.
- Converts bullish and bearish evidence into BUY, SELL, or HOLD signals with confidence and reasons.
- Stores historical analysis in a local SQLite database for charts and later review.
- Tracks watchlists, portfolio holdings, alert rules, and chat history in the dashboard.
- Refreshes watchlists in the background and checks alerts automatically.

## How It Flows

```text
Tickers -> Planner -> TinyFishExecutor -> News sources -> SentimentAnalyzer -> SignalGenerator -> Dashboard/API
                                                    \-> SQLite history, watchlist, portfolio, alerts, chat
```

## Requirements

- Python 3.10 or newer.
- `pip` for installing dependencies.
- `OPENAI_API_KEY` for model-backed planning, analysis, and chat.
- `TINYFISH_API_KEY` for full TinyFish automation coverage.

Optional integrations:

- `DISCORD_WEBHOOK`, `SLACK_WEBHOOK`, `TELEGRAM_BOT_TOKEN`, and `TELEGRAM_CHAT_ID` for alert delivery.
- `REDIS_URL` and `POSTGRES_URL` if you want to wire up the optional storage settings used by the codebase.

## Setup

From the project root:

```powershell
python -m pip install -r requirements.txt
```

Create or update your `.env` file with the settings you want to use. The app reads environment variables case-insensitively.

### Key Environment Variables

- `OPENAI_API_KEY`: Enables OpenAI planning, sentiment analysis, and chat.
- `OPENAI_MODEL`: Model name used by the planner, analyzer, and chatbot.
- `TINYFISH_API_KEY`: Enables TinyFish browser automation.
- `TINYFISH_HEADLESS`: Uses headless browser mode when `true`.
- `DEFAULT_TICKERS`: Comma-separated tickers shown on dashboard load.
- `SENTIMENT_THRESHOLD`: Threshold used when turning scores into BUY or SELL signals.
- `SCAN_INTERVAL`: Background scan interval in seconds.
- `LOG_LEVEL`: Logging level.
- `LOG_FORMAT`: Logging format.
- `ENABLE_CACHING`: Enables cache-related code paths.
- `ENABLE_VECTOR_STORAGE`: Enables vector-storage-related code paths.
- `ENABLE_ALERTS`: Enables alert-related code paths.
- `OFFLINE_MODE`: Enables reduced-connectivity behavior where supported.

## Run The App

Start the local dashboard server:

```powershell
python webapp.py
```

The server starts on `http://127.0.0.1:8080` by default, and you can override the bind address if needed:

```powershell
python webapp.py --host 127.0.0.1 --port 8080
```

On startup, the app also launches the background worker that refreshes the watchlist every 15 minutes and checks alerts every 5 minutes.

## Dashboard Features

- Watchlist: add and remove tickers, then let the background worker refresh them automatically.
- Run Analysis: scan one or more tickers and view the resulting action, confidence, and rationale.
- Historical Trends: inspect sentiment history over time in the built-in chart.
- Developer Output: expand the raw JSON payload for debugging or integration work.
- Chat: ask natural-language questions about tickers, watchlists, or recent sentiment.
- Portfolio: add holdings with quantities and view aggregated sentiment plus a risk indicator.
- Alerts: create sentiment-based alerts using bull score, bear score, or confidence thresholds.
- Dark Mode: toggle the UI theme from the floating control in the lower-right corner.

## API Endpoints

- `POST /api/analyze` - Run a sentiment analysis request.
- `GET /api/history/<TICKER>?days=N` - Load historical sentiment data.
- `POST /api/watchlist` - Fetch the current watchlist.
- `POST /api/watchlist/add` - Add a ticker to the watchlist.
- `POST /api/watchlist/remove` - Remove a ticker from the watchlist.
- `GET /api/portfolio` - Fetch portfolio holdings and aggregated sentiment.
- `POST /api/portfolio/add` - Add a portfolio holding.
- `POST /api/portfolio/remove` - Remove a portfolio holding.
- `GET /api/alerts` - List alert rules and alert state.
- `POST /api/alerts/add` - Create an alert rule.
- `POST /api/alerts/remove` - Delete an alert rule.
- `POST /api/chat` - Send a chat message and get an AI response.
- `GET /api/health` - Check system status and enabled integrations.

## Data And Storage

- The app uses a local SQLite database named `tinyfish.db`.
- The schema is created automatically on first run.
- Stored records include sentiment history, watchlist items, portfolios, holdings, alert rules, alert history, saved searches, search history, preferences, chat history, and source reliability data.

## Project Structure

```text
TinyFish/
├── webapp.py
├── web/
│   ├── index.html
│   ├── app.js
│   └── styles.css
└── src/
    ├── agent/
    ├── chat/
    ├── data/
    ├── scheduler.py
    ├── sentiment/
    ├── sources/
    ├── trading/
    ├── utils/
    └── worker.py
```

## Notes

- If `OPENAI_API_KEY` is missing, the planner, sentiment analyzer, and chatbot fall back to heuristic or simplified behavior where possible.
- If `TINYFISH_API_KEY` is missing, browser automation is disabled, but some source modules can still attempt direct HTTP fetching.
- The main agent currently prioritizes Yahoo Finance Singapore and Bloomberg Asia as its news inputs.
- The dashboard is intentionally local-first and does not require an external database server to start.

## Disclaimer

This project is for informational and educational use only. It is not financial advice. Always verify outputs independently before making investment decisions.
