"""
Main entry point for TinyFish Financial Agent.
Run with: python main.py
"""

import asyncio
import signal
import sys
from typing import Any

import structlog

from src.agent.core import FinancialAgent
from src.utils.config import get_settings
from src.utils.logger import setup_logging


logger = structlog.get_logger(__name__)


class AgentRunner:
    """Main runner for the financial agent."""
    
    def __init__(self) -> None:
        self.settings = get_settings()
        setup_logging(
            level=self.settings.log_level,
            format=self.settings.log_format,
        )
        self.logger = logger.bind(component="agent_runner")
        self.agent: FinancialAgent | None = None
        self.running = False
    
    async def start(self) -> None:
        """Start the agent and monitoring loop."""
        self.logger.info(
            "agent_starting",
            tickers=self.settings.tickers_list,
            interval=self.settings.scan_interval,
        )
        
        try:
            # Initialize agent
            self.agent = FinancialAgent(
                openai_api_key=self.settings.openai_api_key,
                tinyfish_key=self.settings.tinyfish_api_key,
                settings=self.settings,
            )
            
            self.running = True
            
            # Main monitoring loop
            while self.running:
                try:
                    self.logger.info("scan_started")
                    
                    # Monitor sentiment for all default tickers
                    signal = await self.agent.monitor_sentiment(
                        tickers=self.settings.tickers_list,
                    )
                    
                    # Log the signal
                    self.logger.info(
                        "signal_generated",
                        ticker=signal.ticker,
                        action=signal.action,
                        confidence=signal.confidence,
                    )
                    
                    # Print to console for visibility
                    print("\n" + "="*60)
                    print(f"🐟 TRADING SIGNAL: {signal.action}")
                    print("="*60)
                    print(f"Ticker: {signal.ticker}")
                    print(f"Confidence: {signal.confidence:.1%}")
                    print("\nReasons:")
                    for i, reason in enumerate(signal.reasons, 1):
                        print(f"  {i}. {reason}")
                    print("="*60 + "\n")
                    
                    # Wait for next scan
                    self.logger.info(
                        "scan_complete",
                        next_scan_in=self.settings.scan_interval,
                    )
                    await asyncio.sleep(self.settings.scan_interval)
                    
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    self.logger.error("scan_error", error=str(e), exc_info=True)
                    # Wait a bit before retrying on error
                    await asyncio.sleep(60)
        
        except KeyboardInterrupt:
            self.logger.info("shutdown_requested")
        except Exception as e:
            self.logger.error("agent_error", error=str(e), exc_info=True)
        finally:
            await self.cleanup()
    
    async def cleanup(self) -> None:
        """Cleanup resources on shutdown."""
        self.logger.info("cleanup_started")
        self.running = False
        
        if self.agent:
            await self.agent.cleanup()
        
        self.logger.info("cleanup_complete")
    
    def handle_signal(self, sig: Any, frame: Any) -> None:
        """Handle shutdown signals."""
        self.logger.info("signal_received", signal=sig)
        self.running = False


async def main() -> None:
    """Main entry point."""
    runner = AgentRunner()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, runner.handle_signal)
    signal.signal(signal.SIGTERM, runner.handle_signal)
    
    # Start the agent
    await runner.start()


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║         🐟 TinyFish Financial Sentiment Agent 🐟         ║
    ║                                                           ║
    ║    AI-Powered Real-Time Market Sentiment Analysis        ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Agent stopped by user. Goodbye!\n")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}\n", file=sys.stderr)
        sys.exit(1)
