# TinyFish Financial Agent 🐟📈

An AI-powered financial sentiment analysis agent that combines TinyFish browser automation with OpenAI's GPT-4 to monitor real-time market sentiment across news, social media, and crypto platforms.

## Features

- 🤖 **Autonomous Web Scraping**: TinyFish-powered browser automation for dynamic content
- 🧠 **AI Sentiment Analysis**: OpenAI GPT-4 sentiment extraction and scoring
- 📊 **Multi-Source Monitoring**: CNBC, Bloomberg, Reddit, Twitter, CoinMarketCap, and more
- 📡 **Trading Signals**: Actionable BUY/SELL/HOLD signals with confidence scores
- ⚡ **Real-time Alerts**: Discord, Slack, and Telegram notifications
- 🗄️ **Vector Storage**: Redis + Postgres for historical sentiment tracking

## Architecture

```
┌─────────────────┐
│  TinyFish Agent │
│   Orchestrator  │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    │         │          │          │
┌───▼───┐ ┌──▼──┐ ┌─────▼────┐ ┌───▼───┐
│ News  │ │Forum│ │  Social  │ │Crypto │
│Sources│ │ API │ │ Scraping │ │ APIs  │
└───┬───┘ └──┬──┘ └─────┬────┘ └───┬───┘
    │        │          │          │
    └────────┴──────────┴──────────┘
                  │
           ┌──────▼──────┐
           │   OpenAI    │
           │  Sentiment  │
           │   Analysis  │
           └──────┬──────┘
                  │
           ┌──────▼──────┐
           │   Trading   │
           │   Signals   │
           └─────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)
- OpenAI API Key
- TinyFish API Key

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/tinyfish-financial-agent.git
cd tinyfish-financial-agent

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Edit `.env` with your credentials:

```env
OPENAI_API_KEY=sk-...
TINYFISH_API_KEY=...
REDIS_URL=redis://localhost:6379
DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
```

### Running the Agent

#### Development Mode

```bash
# Start development environment
./scripts/dev.sh

# Or manually
python -m pytest tests/
python -m src.agent.core
```

#### Production (Docker)

```bash
docker-compose up -d
```

## Usage

### Basic Sentiment Analysis

```python
from src.agent.core import FinancialAgent
from src.data.models import TradingSignal

# Initialize agent
agent = FinancialAgent(
    openai_api_key="sk-...",
    tinyfish_key="..."
)

# Monitor sentiment for specific tickers
signal = await agent.monitor_sentiment(["AAPL", "TSLA", "BTC"])

print(f"Signal: {signal.action}")
print(f"Confidence: {signal.confidence}")
print(f"Reasons: {signal.reasons}")
```

### Custom Source Configuration

```python
from src.sources.news import CNBCSource, BloombergSource
from src.sentiment.analyzer import SentimentAnalyzer

# Configure sources
sources = [
    CNBCSource(),
    BloombergSource(),
    RedditSource(subreddits=["wallstreetbets", "stocks"])
]

# Analyze
analyzer = SentimentAnalyzer(openai_api_key="sk-...")
sentiment = await analyzer.analyze_ticker("AAPL", sources)
```

## Project Structure

```
tinyfish-financial-agent/
├── src/
│   ├── agent/          # Core agent orchestration
│   ├── sources/        # Data source scrapers
│   ├── sentiment/      # Sentiment analysis & signals
│   ├── data/           # Models, storage, caching
│   ├── trading/        # Signal generation & alerts
│   └── utils/          # Configuration, logging, types
├── tests/              # Unit & integration tests
├── scripts/            # Development & deployment scripts
└── docker-compose.yml  # Production infrastructure
```

## Development

### Running Tests

```bash
pytest tests/ -v --cov=src
```

### Code Quality

```bash
# Format code
black src/ tests/

# Type checking
mypy src/

# Linting
ruff src/ tests/
```

## API Reference

### FinancialAgent

Main orchestrator class for sentiment monitoring.

**Methods:**
- `monitor_sentiment(tickers: list[str]) -> TradingSignal`
- `analyze_source(source: str, ticker: str) -> SentimentScore`
- `generate_alert(signal: TradingSignal) -> None`

### SentimentAnalyzer

OpenAI-powered sentiment extraction.

**Methods:**
- `analyze_text(text: str, ticker: str) -> SentimentScore`
- `batch_analyze(texts: list[str]) -> list[SentimentScore]`

## Roadmap

- [ ] WebSocket streaming for real-time alerts
- [ ] Multi-model ensemble (GPT-4 + Claude + Llama)
- [ ] Backtesting framework
- [ ] Portfolio optimization
- [ ] Technical indicator integration

## Contributing

Contributions welcome! Please read our [Contributing Guide](CONTRIBUTING.md).

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Disclaimer

⚠️ **This tool is for educational purposes only. Not financial advice. Always do your own research before making investment decisions.**

## Support

- 📧 Email: support@tinyfish-agent.com
- 💬 Discord: [Join our community](https://discord.gg/...)
- 📝 Issues: [GitHub Issues](https://github.com/yourusername/tinyfish-financial-agent/issues)

---

Built with ❤️ using [TinyFish](https://tinyfish.ai) & [OpenAI](https://openai.com)
