"""OpenAI GPT-4 sentiment extraction and analysis."""

from typing import Any
import structlog
from openai import AsyncOpenAI

from src.data.models import SentimentScore

logger = structlog.get_logger(__name__)


class SentimentAnalyzer:
    """
    Uses OpenAI GPT-4 to analyze financial sentiment from text.
    
    Example:
        >>> analyzer = SentimentAnalyzer(openai_api_key="sk-...")
        >>> score = await analyzer.analyze_ticker("AAPL", [{"text": "Apple stock soars!"}])
        >>> print(f"Sentiment: {score.sentiment}, Bull: {score.bull_score}")
    """
    
    def __init__(
        self,
        openai_api_key: str,
        model: str = "gpt-4-turbo-preview",
    ) -> None:
        """
        Initialize the sentiment analyzer.
        
        Args:
            openai_api_key: OpenAI API key
            model: GPT model to use
        """
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.model = model
        self.logger = logger.bind(component="sentiment_analyzer")
    
    async def analyze_ticker(
        self,
        ticker: str,
        data_items: list[dict[str, Any]],
    ) -> SentimentScore:
        """
        Analyze sentiment for a specific ticker across data items.
        
        Args:
            ticker: Stock ticker symbol
            data_items: List of text data items to analyze
        
        Returns:
            Aggregated sentiment score
        """
        self.logger.info("analyzing_ticker", ticker=ticker, item_count=len(data_items))
        
        if not data_items:
            return self._neutral_score(ticker)
        
        # Combine all texts
        combined_text = "\n\n".join(
            item.get("text", "") or item.get("title", "")
            for item in data_items
        )[:8000]  # Limit to avoid token limits
        
        # Build analysis prompt
        prompt = self._build_analysis_prompt(ticker, combined_text)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial sentiment analysis expert. Analyze market sentiment objectively.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            
            analysis = response.choices[0].message.content
            self.logger.debug("llm_analysis", analysis=analysis)
            
            # Parse sentiment from response
            score = self._parse_sentiment(ticker, analysis)
            
            return score
            
        except Exception as e:
            self.logger.error("analysis_failed", ticker=ticker, error=str(e))
            return self._neutral_score(ticker)
    
    def _build_analysis_prompt(self, ticker: str, text: str) -> str:
        """Build the sentiment analysis prompt."""
        return f"""
        Analyze the overall market sentiment for {ticker} based on the following content:
        
        {text}
        
        Provide:
        1. Bull score (0.0 - 1.0): How bullish is the sentiment?
        2. Bear score (0.0 - 1.0): How bearish is the sentiment?
        3. Overall sentiment: BULL, BEAR, or NEUTRAL
        4. Key reasons (2-3 bullet points)
        
        Format your response as:
        Bull Score: X.XX
        Bear Score: X.XX
        Sentiment: [BULL/BEAR/NEUTRAL]
        Reasons:
        - Reason 1
        - Reason 2
        """
    
    def _parse_sentiment(self, ticker: str, analysis: str | None) -> SentimentScore:
        """Parse LLM response into structured sentiment score."""
        if not analysis:
            return self._neutral_score(ticker)
        
        try:
            # Extract scores using simple parsing
            lines = analysis.split("\n")
            
            bull_score = 0.5
            bear_score = 0.5
            sentiment = "NEUTRAL"
            reasons = []
            
            for line in lines:
                line = line.strip()
                
                if line.startswith("Bull Score:"):
                    try:
                        bull_score = float(line.split(":")[1].strip())
                    except:
                        pass
                
                elif line.startswith("Bear Score:"):
                    try:
                        bear_score = float(line.split(":")[1].strip())
                    except:
                        pass
                
                elif line.startswith("Sentiment:"):
                    sentiment_text = line.split(":")[1].strip().upper()
                    if sentiment_text in ["BULL", "BEAR", "NEUTRAL"]:
                        sentiment = sentiment_text
                
                elif line.startswith("-"):
                    reasons.append(line[1:].strip())
            
            return SentimentScore(
                ticker=ticker,
                bull_score=bull_score,
                bear_score=bear_score,
                sentiment=sentiment,
                reasons=reasons,
            )
            
        except Exception as e:
            self.logger.error("sentiment_parsing_failed", error=str(e))
            return self._neutral_score(ticker)
    
    def _neutral_score(self, ticker: str) -> SentimentScore:
        """Return a neutral sentiment score."""
        return SentimentScore(
            ticker=ticker,
            bull_score=0.5,
            bear_score=0.5,
            sentiment="NEUTRAL",
            reasons=["Insufficient data for analysis"],
        )
    
    async def batch_analyze(
        self,
        items: list[tuple[str, list[dict[str, Any]]]],
    ) -> list[SentimentScore]:
        """
        Analyze multiple tickers in batch.
        
        Args:
            items: List of (ticker, data_items) tuples
        
        Returns:
            List of sentiment scores
        """
        import asyncio
        
        tasks = [
            self.analyze_ticker(ticker, data)
            for ticker, data in items
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        scores = []
        for result in results:
            if isinstance(result, SentimentScore):
                scores.append(result)
            else:
                self.logger.warning("batch_item_failed", error=str(result))
        
        return scores
