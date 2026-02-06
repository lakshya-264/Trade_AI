"""
Sentiment Analysis Service
Analyzes market sentiment from news, social media, and other sources
"""

import re
from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SentimentAnalysisService:
    """Sentiment analysis for market data and news"""
    
    def __init__(self):
        # Positive and negative keywords for sentiment analysis
        self.positive_keywords = [
            'bullish', 'growth', 'profit', 'gain', 'rise', 'increase', 'positive',
            'strong', 'excellent', 'outperform', 'beat', 'surge', 'rally', 'boom',
            'breakthrough', 'milestone', 'record', 'success', 'expansion', 'upgrade'
        ]
        
        self.negative_keywords = [
            'bearish', 'decline', 'loss', 'fall', 'decrease', 'negative', 'weak',
            'poor', 'underperform', 'miss', 'drop', 'crash', 'recession', 'crisis',
            'concern', 'risk', 'volatility', 'uncertainty', 'downgrade', 'warning'
        ]
        
        # Market-specific terms
        self.market_terms = [
            'earnings', 'revenue', 'profit', 'margin', 'guidance', 'outlook',
            'acquisition', 'merger', 'partnership', 'contract', 'order', 'deal'
        ]
    
    def analyze_text_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text content"""
        try:
            if not text:
                return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
            
            text_lower = text.lower()
            
            # Count positive and negative words
            positive_count = sum(1 for word in self.positive_keywords if word in text_lower)
            negative_count = sum(1 for word in self.negative_keywords if word in text_lower)
            
            # Calculate sentiment score
            total_words = len(text.split())
            if total_words == 0:
                return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
            
            positive_ratio = positive_count / total_words
            negative_ratio = negative_count / total_words
            
            # Calculate overall sentiment
            if positive_ratio > negative_ratio:
                sentiment = "positive"
                score = positive_ratio - negative_ratio
            elif negative_ratio > positive_ratio:
                sentiment = "negative"
                score = negative_ratio - positive_ratio
            else:
                sentiment = "neutral"
                score = 0.0
            
            # Calculate confidence based on word density
            confidence = min(1.0, (positive_count + negative_count) / total_words * 10)
            
            return {
                "sentiment": sentiment,
                "score": round(score, 3),
                "confidence": round(confidence, 3),
                "positive_words": positive_count,
                "negative_words": negative_count,
                "total_words": total_words
            }
            
        except Exception as e:
            logger.error(f"Text sentiment analysis error: {e}")
            return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
    
    def analyze_news_sentiment(self, news_items: List[Dict]) -> Dict[str, Any]:
        """Analyze sentiment from news items"""
        try:
            if not news_items:
                return {"overall_sentiment": "neutral", "confidence": 0.0, "details": []}
            
            sentiments = []
            total_confidence = 0.0
            
            for news in news_items:
                title = news.get('title', '')
                content = news.get('content', '')
                combined_text = f"{title} {content}"
                
                sentiment = self.analyze_text_sentiment(combined_text)
                sentiments.append(sentiment)
                total_confidence += sentiment['confidence']
            
            # Calculate overall sentiment
            positive_count = sum(1 for s in sentiments if s['sentiment'] == 'positive')
            negative_count = sum(1 for s in sentiments if s['sentiment'] == 'negative')
            neutral_count = len(sentiments) - positive_count - negative_count
            
            if positive_count > negative_count and positive_count > neutral_count:
                overall_sentiment = "positive"
            elif negative_count > positive_count and negative_count > neutral_count:
                overall_sentiment = "negative"
            else:
                overall_sentiment = "neutral"
            
            avg_confidence = total_confidence / len(sentiments) if sentiments else 0.0
            
            return {
                "overall_sentiment": overall_sentiment,
                "confidence": round(avg_confidence, 3),
                "positive_count": positive_count,
                "negative_count": negative_count,
                "neutral_count": neutral_count,
                "total_news": len(news_items),
                "details": sentiments
            }
            
        except Exception as e:
            logger.error(f"News sentiment analysis error: {e}")
            return {"overall_sentiment": "neutral", "confidence": 0.0, "details": []}
    
    def analyze_social_sentiment(self, social_posts: List[Dict]) -> Dict[str, Any]:
        """Analyze sentiment from social media posts"""
        try:
            if not social_posts:
                return {"overall_sentiment": "neutral", "confidence": 0.0, "engagement": 0}
            
            sentiments = []
            total_engagement = 0
            
            for post in social_posts:
                text = post.get('text', '')
                engagement = post.get('likes', 0) + post.get('retweets', 0) + post.get('comments', 0)
                
                sentiment = self.analyze_text_sentiment(text)
                # Weight sentiment by engagement
                weighted_sentiment = sentiment['score'] * (1 + engagement / 100)
                sentiment['weighted_score'] = weighted_sentiment
                
                sentiments.append(sentiment)
                total_engagement += engagement
            
            # Calculate weighted overall sentiment
            weighted_positive = sum(s['weighted_score'] for s in sentiments if s['sentiment'] == 'positive')
            weighted_negative = sum(abs(s['weighted_score']) for s in sentiments if s['sentiment'] == 'negative')
            
            if weighted_positive > weighted_negative:
                overall_sentiment = "positive"
                score = weighted_positive - weighted_negative
            elif weighted_negative > weighted_positive:
                overall_sentiment = "negative"
                score = weighted_negative - weighted_positive
            else:
                overall_sentiment = "neutral"
                score = 0.0
            
            avg_confidence = sum(s['confidence'] for s in sentiments) / len(sentiments)
            
            return {
                "overall_sentiment": overall_sentiment,
                "confidence": round(avg_confidence, 3),
                "score": round(score, 3),
                "total_posts": len(social_posts),
                "total_engagement": total_engagement,
                "avg_engagement": round(total_engagement / len(social_posts), 2)
            }
            
        except Exception as e:
            logger.error(f"Social sentiment analysis error: {e}")
            return {"overall_sentiment": "neutral", "confidence": 0.0, "engagement": 0}
    
    def analyze_market_sentiment(self, symbol: str, data_sources: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive market sentiment analysis"""
        try:
            # Analyze different data sources
            news_sentiment = self.analyze_news_sentiment(data_sources.get('news', []))
            social_sentiment = self.analyze_social_sentiment(data_sources.get('social', []))
            
            # Analyze price action sentiment
            price_sentiment = self._analyze_price_sentiment(data_sources.get('price_data', {}))
            
            # Combine all sentiment sources
            sentiment_scores = []
            confidences = []
            
            if news_sentiment['confidence'] > 0:
                sentiment_scores.append(news_sentiment['score'] if news_sentiment['overall_sentiment'] != 'neutral' else 0)
                confidences.append(news_sentiment['confidence'])
            
            if social_sentiment['confidence'] > 0:
                sentiment_scores.append(social_sentiment['score'])
                confidences.append(social_sentiment['confidence'])
            
            if price_sentiment['confidence'] > 0:
                sentiment_scores.append(price_sentiment['score'])
                confidences.append(price_sentiment['confidence'])
            
            # Calculate weighted overall sentiment
            if sentiment_scores and confidences:
                weighted_score = sum(s * c for s, c in zip(sentiment_scores, confidences))
                total_confidence = sum(confidences)
                overall_score = weighted_score / total_confidence if total_confidence > 0 else 0
                
                if overall_score > 0.1:
                    overall_sentiment = "positive"
                elif overall_score < -0.1:
                    overall_sentiment = "negative"
                else:
                    overall_sentiment = "neutral"
            else:
                overall_sentiment = "neutral"
                overall_score = 0.0
                total_confidence = 0.0
            
            return {
                "symbol": symbol,
                "overall_sentiment": overall_sentiment,
                "overall_score": round(overall_score, 3),
                "confidence": round(total_confidence / len(confidences) if confidences else 0, 3),
                "sources": {
                    "news": news_sentiment,
                    "social": social_sentiment,
                    "price_action": price_sentiment
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Market sentiment analysis error for {symbol}: {e}")
            return {
                "symbol": symbol,
                "overall_sentiment": "neutral",
                "overall_score": 0.0,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _analyze_price_sentiment(self, price_data: Dict) -> Dict[str, Any]:
        """Analyze sentiment based on price action"""
        try:
            if not price_data:
                return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
            
            current_price = price_data.get('current', 0)
            open_price = price_data.get('open', current_price)
            high_price = price_data.get('high', current_price)
            low_price = price_data.get('low', current_price)
            
            if current_price == 0 or open_price == 0:
                return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
            
            # Calculate price change percentage
            price_change = ((current_price - open_price) / open_price) * 100
            
            # Analyze price position within daily range
            daily_range = high_price - low_price
            if daily_range > 0:
                position_in_range = (current_price - low_price) / daily_range
            else:
                position_in_range = 0.5
            
            # Determine sentiment based on price action
            if price_change > 2 and position_in_range > 0.7:
                sentiment = "positive"
                score = min(1.0, price_change / 10)
            elif price_change < -2 and position_in_range < 0.3:
                sentiment = "negative"
                score = min(1.0, abs(price_change) / 10)
            else:
                sentiment = "neutral"
                score = 0.0
            
            confidence = min(1.0, abs(price_change) / 5)  # Higher confidence for larger moves
            
            return {
                "sentiment": sentiment,
                "score": round(score, 3),
                "confidence": round(confidence, 3),
                "price_change": round(price_change, 2),
                "position_in_range": round(position_in_range, 3)
            }
            
        except Exception as e:
            logger.error(f"Price sentiment analysis error: {e}")
            return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
    
    def get_sentiment_summary(self, analysis: Dict[str, Any]) -> str:
        """Generate human-readable sentiment summary"""
        try:
            sentiment = analysis.get('overall_sentiment', 'neutral')
            confidence = analysis.get('confidence', 0.0)
            score = analysis.get('overall_score', 0.0)
            
            if sentiment == "positive":
                if confidence > 0.7:
                    return f"Strong positive sentiment (confidence: {confidence:.1%})"
                else:
                    return f"Moderately positive sentiment (confidence: {confidence:.1%})"
            elif sentiment == "negative":
                if confidence > 0.7:
                    return f"Strong negative sentiment (confidence: {confidence:.1%})"
                else:
                    return f"Moderately negative sentiment (confidence: {confidence:.1%})"
            else:
                return f"Neutral sentiment (confidence: {confidence:.1%})"
                
        except Exception as e:
            logger.error(f"Sentiment summary error: {e}")
            return "Unable to determine sentiment"
