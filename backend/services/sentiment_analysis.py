"""
Sentiment analysis service
"""
from typing import Dict, Any, List
import re

class SentimentAnalyzer:
    def __init__(self):
        self.positive_words = [
            "bullish", "buy", "strong", "growth", "profit", "gain", "up", "rise",
            "positive", "good", "excellent", "outperform", "beat", "surge"
        ]
        self.negative_words = [
            "bearish", "sell", "weak", "decline", "loss", "down", "fall", "drop",
            "negative", "bad", "poor", "underperform", "miss", "crash"
        ]
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        if not text:
            return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
        
        text_lower = text.lower()
        positive_count = sum(1 for word in self.positive_words if word in text_lower)
        negative_count = sum(1 for word in self.negative_words if word in text_lower)
        
        total_words = len(text.split())
        if total_words == 0:
            return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
        
        positive_score = positive_count / total_words
        negative_score = negative_count / total_words
        
        if positive_score > negative_score:
            sentiment = "positive"
            score = positive_score
        elif negative_score > positive_score:
            sentiment = "negative"
            score = negative_score
        else:
            sentiment = "neutral"
            score = 0.0
        
        confidence = abs(positive_score - negative_score)
        
        return {
            "sentiment": sentiment,
            "score": score,
            "confidence": confidence,
            "positive_words": positive_count,
            "negative_words": negative_count
        }
    
    def analyze_news_sentiment(self, news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment of news items"""
        if not news_items:
            return {"overall_sentiment": "neutral", "average_score": 0.0}
        
        sentiments = []
        for item in news_items:
            text = item.get("title", "") + " " + item.get("content", "")
            sentiment = self.analyze_sentiment(text)
            sentiments.append(sentiment)
        
        positive_count = sum(1 for s in sentiments if s["sentiment"] == "positive")
        negative_count = sum(1 for s in sentiments if s["sentiment"] == "negative")
        total_count = len(sentiments)
        
        if positive_count > negative_count:
            overall_sentiment = "positive"
        elif negative_count > positive_count:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"
        
        average_score = sum(s["score"] for s in sentiments) / total_count
        
        return {
            "overall_sentiment": overall_sentiment,
            "average_score": average_score,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": total_count - positive_count - negative_count
        }


class SentimentAnalysisService:
    """
    Backwards-compatible service wrapper expected by other modules.
    Provides high-level methods using SentimentAnalyzer under the hood.
    """

    def __init__(self):
        self.analyzer = SentimentAnalyzer()

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze free-form text sentiment."""
        return self.analyzer.analyze_sentiment(text)

    def analyze_news_sentiment(self, news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment across multiple news articles."""
        return self.analyzer.analyze_news_sentiment(news_items)

