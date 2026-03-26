# 🐟 TinyFish Financial Agent - Quick Start Guide

## ⚡ One-Command Setup

```cmd
python setup_all.py
```

This will create the entire project structure with all files.

## 📋 Manual Setup (If Needed)

If you prefer to run each step manually:

### Step 1: Create Directories
```cmd
python setup_dirs.py
```

### Step 2: Create All Project Files
```cmd
python create_files_part1.py
python create_files_part2.py
python create_files_part3.py
python create_files_part4.py
```

## 🔧 Installation

### 1. Create Virtual Environment
```cmd
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows (CMD):**
```cmd
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies
```cmd
pip install -r requirements.txt
```

### 4. Configure Environment
```cmd
REM Copy the example environment file
copy .env.example .env

REM Edit .env with your favorite editor
notepad .env
```

**Required API Keys in .env:**
- `OPENAI_API_KEY` - Get from https://platform.openai.com/api-keys
- `TINYFISH_API_KEY` - Get from TinyFish dashboard

**Optional Configuration:**
- Discord webhook URL for alerts
- Slack webhook URL for alerts
- Telegram bot token for alerts
- Redis URL (default: redis://localhost:6379/0)
- Postgres URL for vector storage

## 🚀 Running the Agent

### Option 1: Using Main Entry Point (Recommended)
```cmd
python main.py
```

This will:
- Initialize the agent
- Monitor configured tickers every 5 minutes (configurable)
- Print trading signals to console
- Send alerts if configured

### Option 2: Using Module Directly
```cmd
python -m src.agent.core
```

### Option 3: Docker (Production)
```cmd
REM Start all services
docker-compose up -d

REM View logs
docker-compose logs -f agent

REM Stop services
docker-compose down
```

## 🧪 Running Tests

```cmd
REM All tests
pytest tests/ -v

REM With coverage report
pytest tests/ --cov=src --cov-report=html

REM Specific test file
pytest tests/test_agent.py -v

REM Run in watch mode (with pytest-watch)
pip install pytest-watch
ptw tests/
```

## 📁 Project Structure After Setup

```
TinyFish/
├── main.py                  ⭐ Main entry point - RUN THIS
├── setup_all.py             🔧 Master setup script
├── setup_dirs.py            📁 Directory creation
├── create_files_part*.py    📝 File creation scripts
│
├── README.md                📖 Project documentation
├── INSTALLATION.md          📋 Detailed installation guide
├── QUICKSTART.md            ⚡ This file
├── requirements.txt         📦 Python dependencies
├── .env.example             🔐 Environment template
├── .gitignore              🚫 Git ignore rules
│
├── src/                    🐍 Source code
│   ├── agent/              🤖 Core orchestration
│   ├── sources/            📰 Data scrapers
│   ├── sentiment/          🧠 AI analysis
│   ├── data/               💾 Models & storage
│   ├── trading/            📊 Signals & alerts
│   └── utils/              🛠️ Utilities
│
├── tests/                  ✅ Test suite
├── scripts/                📜 Utility scripts
├── docker-compose.yml      🐳 Docker config
└── Dockerfile              📦 Container definition
```

## 💡 Usage Examples

### Basic Sentiment Monitoring
```python
import asyncio
from src.agent.core import FinancialAgent

async def main():
    agent = FinancialAgent(
        openai_api_key="sk-...",
        tinyfish_key="..."
    )
    
    # Monitor a single ticker
    signal = await agent.monitor_sentiment(["AAPL"])
    
    print(f"Action: {signal.action}")
    print(f"Confidence: {signal.confidence:.1%}")
    
    await agent.cleanup()

asyncio.run(main())
```

### Multiple Tickers
```python
signal = await agent.monitor_sentiment(["AAPL", "TSLA", "NVDA", "BTC"])
```

### Custom Sources Only
```python
signal = await agent.monitor_sentiment(
    tickers=["AAPL"],
    source_types=["news", "social"]  # Only news and social
)
```

### Get Sentiment from Specific Source
```python
score = await agent.analyze_source("cnbc", "AAPL")
print(f"CNBC Sentiment: {score.sentiment}")
print(f"Bull Score: {score.bull_score}")
```

## 🔍 Verifying Setup

Run this quick verification:

```python
# verify_setup.py
import sys

print("Checking installation...")

try:
    from src.agent.core import FinancialAgent
    from src.data.models import TradingSignal, SentimentScore
    from src.sentiment.analyzer import SentimentAnalyzer
    print("✅ All imports successful!")
    
    # Check env file
    import os
    if os.path.exists(".env"):
        print("✅ .env file found")
    else:
        print("❌ .env file missing - copy from .env.example")
    
    # Check virtual environment
    if hasattr(sys, 'prefix'):
        print(f"✅ Virtual environment: {sys.prefix}")
    
    print("\n🎉 Setup verified! Ready to run.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Run: pip install -r requirements.txt")
except Exception as e:
    print(f"❌ Error: {e}")
```

Save the above as `verify_setup.py` and run:
```cmd
python verify_setup.py
```

## 🐛 Troubleshooting

### "No module named 'src'"
```cmd
REM Make sure you're in the project root
cd c:\Users\alson\TinyFish

REM And virtual environment is activated
venv\Scripts\activate
```

### "OPENAI_API_KEY not found"
```cmd
REM Make sure .env file exists and has your key
type .env
```

### "Redis connection failed"
```cmd
REM Start Redis with Docker
docker-compose up -d redis

REM Or set REDIS_URL to a remote Redis instance in .env
```

### Tests failing
```cmd
REM Update pip and install fresh
python -m pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

## 📚 Next Steps

1. **Configure Your Environment**: Edit `.env` with real API keys
2. **Start Simple**: Run `python main.py` to test basic functionality
3. **Add Custom Sources**: Extend scrapers in `src/sources/`
4. **Configure Alerts**: Set up Discord/Slack webhooks
5. **Deploy to Production**: Use Docker Compose for 24/7 monitoring

## 🎯 Quick Commands Cheat Sheet

```cmd
REM Setup
python setup_all.py

REM Install
python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt

REM Configure
copy .env.example .env && notepad .env

REM Test
pytest tests/ -v

REM Run
python main.py

REM Docker
docker-compose up -d

REM View logs
docker-compose logs -f agent
```

## 📞 Need Help?

- Check `INSTALLATION.md` for detailed instructions
- Review `README.md` for architecture and features
- Run `pytest tests/ -v` to verify everything works
- Check logs for error messages

---

**Ready?** Start with: `python setup_all.py` then `python main.py` 🚀
