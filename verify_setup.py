"""
Setup verification script for TinyFish Financial Agent.
Run this to verify your installation is complete and correct.
"""

import os
import sys
from pathlib import Path


def check_files():
    """Check if all required files exist."""
    print("\n📄 Checking Project Files...")
    print("="*60)
    
    required_files = {
        "Core Files": [
            "README.md",
            "INSTALLATION.md",
            "QUICKSTART.md",
            "requirements.txt",
            ".env.example",
            ".gitignore",
            "main.py",
        ],
        "Docker Files": [
            "docker-compose.yml",
            "Dockerfile",
        ],
        "Scripts": [
            "scripts/dev.sh",
            "scripts/deploy.sh",
        ],
        "Source - Agent": [
            "src/__init__.py",
            "src/agent/__init__.py",
            "src/agent/core.py",
            "src/agent/planner.py",
            "src/agent/executor.py",
        ],
        "Source - Data Sources": [
            "src/sources/__init__.py",
            "src/sources/news.py",
            "src/sources/forums.py",
            "src/sources/social.py",
            "src/sources/crypto.py",
        ],
        "Source - Sentiment": [
            "src/sentiment/__init__.py",
            "src/sentiment/analyzer.py",
            "src/sentiment/signals.py",
            "src/sentiment/scorer.py",
        ],
        "Source - Data": [
            "src/data/__init__.py",
            "src/data/models.py",
            "src/data/storage.py",
            "src/data/cache.py",
        ],
        "Source - Trading": [
            "src/trading/__init__.py",
            "src/trading/signals.py",
            "src/trading/alerts.py",
        ],
        "Source - Utils": [
            "src/utils/__init__.py",
            "src/utils/config.py",
            "src/utils/logger.py",
            "src/utils/types.py",
        ],
        "Tests": [
            "tests/__init__.py",
            "tests/test_agent.py",
            "tests/test_sentiment.py",
            "tests/test_sources.py",
        ],
    }
    
    all_good = True
    
    for category, files in required_files.items():
        print(f"\n{category}:")
        for file in files:
            exists = os.path.exists(file)
            status = "✅" if exists else "❌"
            print(f"  {status} {file}")
            if not exists:
                all_good = False
    
    return all_good


def check_imports():
    """Check if all imports work."""
    print("\n\n🐍 Checking Python Imports...")
    print("="*60)
    
    imports = [
        ("src.agent.core", "FinancialAgent"),
        ("src.agent.planner", "AgentPlanner"),
        ("src.agent.executor", "TinyFishExecutor"),
        ("src.data.models", "SentimentScore"),
        ("src.data.models", "TradingSignal"),
        ("src.sentiment.analyzer", "SentimentAnalyzer"),
        ("src.sentiment.signals", "SignalGenerator"),
        ("src.sources.news", "CNBCSource"),
        ("src.sources.forums", "RedditSource"),
        ("src.trading.alerts", "AlertManager"),
        ("src.utils.config", "Settings"),
    ]
    
    all_good = True
    
    for module, cls in imports:
        try:
            mod = __import__(module, fromlist=[cls])
            getattr(mod, cls)
            print(f"  ✅ {module}.{cls}")
        except ImportError as e:
            print(f"  ❌ {module}.{cls} - Import Error: {e}")
            all_good = False
        except AttributeError as e:
            print(f"  ❌ {module}.{cls} - Attribute Error: {e}")
            all_good = False
        except Exception as e:
            print(f"  ❌ {module}.{cls} - Error: {e}")
            all_good = False
    
    return all_good


def check_environment():
    """Check environment setup."""
    print("\n\n🔧 Checking Environment...")
    print("="*60)
    
    # Check Python version
    py_version = sys.version_info
    print(f"  Python Version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    
    if py_version.major == 3 and py_version.minor >= 11:
        print(f"    ✅ Python 3.11+ (Required)")
    else:
        print(f"    ❌ Python 3.11+ required, found {py_version.major}.{py_version.minor}")
    
    # Check virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    if in_venv:
        print(f"  ✅ Virtual Environment Active")
        print(f"    Location: {sys.prefix}")
    else:
        print(f"  ⚠️  No Virtual Environment Detected")
        print(f"    Recommendation: Create one with 'python -m venv venv'")
    
    # Check .env file
    if os.path.exists(".env"):
        print(f"  ✅ .env file exists")
        
        # Check if it has required keys
        with open(".env", "r") as f:
            content = f.read()
            required_keys = ["OPENAI_API_KEY", "TINYFISH_API_KEY"]
            
            for key in required_keys:
                if key in content:
                    # Check if it's not just the example placeholder
                    if "your-" in content or "sk-..." in content:
                        print(f"    ⚠️  {key} found but appears to be placeholder")
                    else:
                        print(f"    ✅ {key} configured")
                else:
                    print(f"    ❌ {key} missing")
    else:
        print(f"  ❌ .env file missing")
        print(f"    Run: copy .env.example .env")
    
    # Check dependencies
    print(f"\n  Checking Key Dependencies:")
    
    deps = [
        "openai",
        "pydantic",
        "structlog",
        "httpx",
        "beautifulsoup4",
        "pytest",
    ]
    
    for dep in deps:
        try:
            __import__(dep)
            print(f"    ✅ {dep}")
        except ImportError:
            print(f"    ❌ {dep} not installed")


def check_structure():
    """Check directory structure."""
    print("\n\n📁 Checking Directory Structure...")
    print("="*60)
    
    required_dirs = [
        "src",
        "src/agent",
        "src/sources",
        "src/sentiment",
        "src/data",
        "src/trading",
        "src/utils",
        "tests",
        "scripts",
    ]
    
    all_good = True
    
    for dir_path in required_dirs:
        exists = os.path.isdir(dir_path)
        status = "✅" if exists else "❌"
        print(f"  {status} {dir_path}/")
        if not exists:
            all_good = False
    
    return all_good


def main():
    """Run all verification checks."""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║    🐟 TinyFish Financial Agent - Setup Verification     🐟║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Run all checks
    files_ok = check_files()
    structure_ok = check_structure()
    check_environment()
    
    # Only check imports if files exist
    if files_ok and structure_ok:
        imports_ok = check_imports()
    else:
        imports_ok = False
        print("\n⚠️  Skipping import checks due to missing files/directories")
    
    # Summary
    print("\n\n" + "="*60)
    print("📊 VERIFICATION SUMMARY")
    print("="*60)
    
    if files_ok and structure_ok and imports_ok:
        print("""
✅ ALL CHECKS PASSED!

Your TinyFish Financial Agent is ready to run.

Next steps:
1. Configure .env with your API keys
2. Install dependencies: pip install -r requirements.txt  
3. Run tests: pytest tests/ -v
4. Start agent: python main.py

Happy trading! 🚀
        """)
    else:
        print("""
❌ SOME CHECKS FAILED

Please fix the issues above before running the agent.

Common fixes:
1. Run setup: python setup_all.py
2. Install deps: pip install -r requirements.txt
3. Create .env: copy .env.example .env

Need help? Check INSTALLATION.md or QUICKSTART.md
        """)


if __name__ == "__main__":
    main()
