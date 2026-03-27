"""Trading signal formatting and output."""

import structlog
from datetime import datetime

from src.data.models import TradingSignal

logger = structlog.get_logger(__name__)


class SignalFormatter:
    """
    Formats trading signals for various outputs.
    
    Example:
        >>> formatter = SignalFormatter()
        >>> text = formatter.to_text(signal)
        >>> json_str = formatter.to_json(signal)
    """
    
    def __init__(self) -> None:
        self.logger = logger.bind(component="signal_formatter")
    
    def to_text(self, signal: TradingSignal) -> str:
        """
        Format signal as plain text.
        
        Args:
            signal: Trading signal to format
        
        Returns:
            Formatted text string
        """
        emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}[signal.action]
        
        text = f"""
{emoji} TRADING SIGNAL {emoji}

Ticker: {signal.ticker}
Action: {signal.action}
Confidence: {signal.confidence:.1%}
Time: {signal.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}

Reasons:
"""
        for i, reason in enumerate(signal.reasons, 1):
            text += f"{i}. {reason}
"
        
        return text.strip()
    
    def to_json(self, signal: TradingSignal) -> str:
        """
        Format signal as JSON.
        
        Args:
            signal: Trading signal to format
        
        Returns:
            JSON string
        """
        return signal.model_dump_json(indent=2)
    
    def to_markdown(self, signal: TradingSignal) -> str:
        """
        Format signal as Markdown.
        
        Args:
            signal: Trading signal to format
        
        Returns:
            Markdown formatted string
        """
        emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}[signal.action]
        
        md = f"""# {emoji} Trading Signal: {signal.action}

**Ticker:** `{signal.ticker}`  
**Confidence:** {signal.confidence:.1%}  
**Time:** {signal.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}

## Reasons

"""
        for reason in signal.reasons:
            md += f"- {reason}
"
        
        return md.strip()
