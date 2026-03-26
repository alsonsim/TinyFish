# 🐟 TinyFish Financial Agent - Installation Guide

## Quick Setup (Windows)

### Step 1: Create Project Structure

Run these commands in Command Prompt or PowerShell:

```cmd
cd c:\Users\alson\TinyFish

REM Run the setup batch file to create directories
setup.bat

REM Run all Python file creation scripts
python create_files_part1.py
python create_files_part2.py
python create_files_part3.py
python create_files_part4.py
```

### Step 2: Install Dependencies

```cmd
REM Create virtual environment
python -m venv venv

REM Activate virtual environment
venv\Scripts\activate

REM Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment

```cmd
REM Copy example env file
copy .env.example .env

REM Edit .env with your text editor and add:
REM - OPENAI_API_KEY=sk-your-key-here
REM - TINYFISH_API_KEY=your-key-here
REM - Other configuration values
notepad .env
```

### Step 4: Start Development Environment

```cmd
REM Option A: Using Docker (recommended for production)
docker-compose up -d

REM Option B: Local development (requires Redis installed)
REM Start Redis separately, then:
python -m pytest tests/
python -m src.agent.core
```

## Project Structure

After running the setup scripts, you'll have:

```
TinyFish/
├── README.md                    # Project documentation
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── .env                         # Your config (create this)
├── .gitignore                   # Git ignore rules
├── setup.bat                    # Windows setup script
├── docker-compose.yml           # Docker orchestration
├── Dockerfile                   # Container definition
│
├── src/
│   ├── __init__.py
│   │
│   ├── agent/                   # Core orchestration
│   │   ├── __init__.py
│   │   ├── core.py              # Main FinancialAgent class
│   │   ├── planner.py           # LLM-based planning
│   │   └── executor.py          # TinyFish browser control
│   │
│   ├── sources/                 # Data source scrapers
│   │   ├── __init__.py
│   │   ├── news.py              # CNBC, Bloomberg
│   │   ├── forums.py            # Reddit, StockTwits
│   │   ├── social.py            # Twitter/X
│   │   └── crypto.py            # CoinMarketCap, DefiLlama
│   │
│   ├── sentiment/               # AI sentiment analysis
│   │   ├── __init__.py
│   │   ├── analyzer.py          # OpenAI GPT-4 analysis
│   │   ├── signals.py           # Signal generation
│   │   └── scorer.py            # Score calculations
│   │
│   ├── data/                    # Data models & storage
│   │   ├── __init__.py
│   │   ├── models.py            # Pydantic schemas
│   │   ├── storage.py           # Vector database
│   │   └── cache.py             # Redis caching
│   │
│   ├── trading/                 # Trading signals & alerts
│   │   ├── __init__.py
│   │   ├── signals.py           # Signal formatting
│   │   └── alerts.py            # Discord/Slack/Telegram
│   │
│   └── utils/                   # Shared utilities
│       ├── __init__.py
│       ├── config.py            # Settings management
│       ├── logger.py            # Structured logging
│       └── types.py             # Type definitions
│
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── test_agent.py            # Agent tests
│   ├── test_sentiment.py        # Sentiment tests
│   └── test_sources.py          # Source tests
│
└── scripts/                     # Utility scripts
    ├── dev.sh                   # Development launcher
    └── deploy.sh                # Production deployment
```

## Usage Examples

### Basic Usage

```python
from src.agent.core import FinancialAgent

# Initialize
agent = FinancialAgent(
    openai_api_key="sk-...",
    tinyfish_key="..."
)

# Monitor sentiment
signal = await agent.monitor_sentiment(["AAPL", "TSLA"])

print(f"Action: {signal.action}")
print(f"Confidence: {signal.confidence:.1%}")
for reason in signal.reasons:
    print(f"  - {reason}")
```

### Custom Source Configuration

```python
from src.sources.news import CNBCSource
from src.agent.executor import TinyFishExecutor

executor = TinyFishExecutor(api_key="...")
source = CNBCSource(executor)

data = await source.fetch_data("BTC")
```

### Running Tests

```cmd
REM All tests
pytest tests/ -v

REM With coverage
pytest tests/ --cov=src --cov-report=html

REM Specific test file
pytest tests/test_agent.py -v
```

## Next Steps

1. **Implement TinyFish Integration**: Replace placeholder code in `executor.py` with actual TinyFish API calls
2. **Add More Sources**: Extend scrapers in `src/sources/` for additional data sources
3. **Enhance Sentiment Analysis**: Refine prompts in `analyzer.py` for better accuracy
4. **Configure Alerts**: Set up Discord/Slack/Telegram webhooks in `.env`
5. **Deploy to Production**: Use `docker-compose.yml` for containerized deployment

## Troubleshooting

### Import Errors
```cmd
REM Make sure you're in the virtual environment
venv\Scripts\activate

REM Install dependencies again
pip install -r requirements.txt
```

### Redis Connection Issues
```cmd
REM Check if Redis is running
docker ps

REM Start Redis
docker-compose up -d redis
```

### Test Failures
```cmd
REM Tests use mocks, so they should pass
REM If failing, check Python version (needs 3.11+)
python --version

REM Update dependencies
pip install --upgrade -r requirements.txt
```

## Development Workflow

1. **Start Services**: `docker-compose up -d redis postgres`
2. **Activate Venv**: `venv\Scripts\activate`
3. **Run Tests**: `pytest tests/ -v`
4. **Make Changes**: Edit files in `src/`
5. **Test Changes**: Run specific tests
6. **Commit**: Git commit your changes

## Production Deployment

```bash
# Build and test
docker-compose build
docker-compose run --rm agent pytest tests/

# Deploy
docker-compose up -d

# Monitor
docker-compose logs -f agent
```

## Resources

- **TinyFish Docs**: https://tinyfish.ai/docs
- **OpenAI API**: https://platform.openai.com/docs
- **Pydantic**: https://docs.pydantic.dev
- **Structlog**: https://www.structlog.org

## Support

If you encounter issues:

1. Check the logs: `docker-compose logs agent`
2. Verify `.env` configuration
3. Ensure all API keys are valid
4. Run tests to identify specific issues

---

**Ready to start?** Run the setup commands above and you'll have a complete financial sentiment analysis agent!
