"""
Advanced NLP-based Feature Engineering Service
Enhanced sentiment analysis and text feature extraction for trading models
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import re
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from textblob import TextBlob
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.cluster import KMeans
import asyncio

logger = logging.getLogger(__name__)

class AdvancedNLPFeatures:
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        self.lemmatizer = WordNetLemmatizer()
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.count_vectorizer = CountVectorizer(max_features=500, stop_words='english')
        
        # Financial sentiment lexicons
        self.bullish_words = [
            'bull', 'bullish', 'rally', 'surge', 'gain', 'profit', 'growth', 'up', 'rise',
            'breakout', 'momentum', 'strong', 'positive', 'optimistic', 'buy', 'purchase',
            'investment', 'opportunity', 'potential', 'outperform', 'upgrade', 'beat'
        ]
        
        self.bearish_words = [
            'bear', 'bearish', 'crash', 'fall', 'drop', 'decline', 'loss', 'down', 'plunge',
            'breakdown', 'weak', 'negative', 'pessimistic', 'sell', 'short', 'risk',
            'concern', 'worry', 'underperform', 'downgrade', 'miss', 'disappoint'
        ]
        
        # Market-specific terms
        self.market_terms = [
            'earnings', 'revenue', 'profit', 'loss', 'dividend', 'ipo', 'merger', 'acquisition',
            'guidance', 'outlook', 'forecast', 'analyst', 'rating', 'target', 'price',
            'volume', 'volatility', 'liquidity', 'correlation', 'beta', 'alpha'
        ]
        
        # Initialize NLTK data
        try:
            nltk.download('vader_lexicon', quiet=True)
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
        except:
            pass
        
        # Load spaCy model (if available)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            self.nlp = None
            logger.warning("spaCy model not available, using basic NLP features")
    
    def extract_comprehensive_features(self, text: str) -> Dict:
        """Extract comprehensive NLP features from text"""
        try:
            features = {}
            
            # Basic text features
            features.update(self._extract_basic_features(text))
            
            # Sentiment features
            features.update(self._extract_sentiment_features(text))
            
            # Financial sentiment features
            features.update(self._extract_financial_sentiment(text))
            
            # Topic modeling features
            features.update(self._extract_topic_features(text))
            
            # Named entity recognition
            features.update(self._extract_entity_features(text))
            
            # Readability and complexity
            features.update(self._extract_readability_features(text))
            
            # Temporal features
            features.update(self._extract_temporal_features(text))
            
            # Market-specific features
            features.update(self._extract_market_features(text))
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting NLP features: {e}")
            return {}
    
    def _extract_basic_features(self, text: str) -> Dict:
        """Extract basic text features"""
        try:
            words = word_tokenize(text.lower())
            sentences = sent_tokenize(text)
            
            return {
                "word_count": len(words),
                "sentence_count": len(sentences),
                "avg_words_per_sentence": len(words) / len(sentences) if sentences else 0,
                "char_count": len(text),
                "unique_words": len(set(words)),
                "lexical_diversity": len(set(words)) / len(words) if words else 0,
                "avg_word_length": np.mean([len(word) for word in words]) if words else 0
            }
        except Exception as e:
            logger.error(f"Error extracting basic features: {e}")
            return {}
    
    def _extract_sentiment_features(self, text: str) -> Dict:
        """Extract comprehensive sentiment features"""
        try:
            # TextBlob sentiment
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            # VADER sentiment
            vader_scores = self.sia.polarity_scores(text)
            
            # Custom sentiment calculation
            words = word_tokenize(text.lower())
            bullish_count = sum(1 for word in words if word in self.bullish_words)
            bearish_count = sum(1 for word in words if word in self.bearish_words)
            
            financial_sentiment = (bullish_count - bearish_count) / len(words) if words else 0
            
            return {
                "textblob_polarity": polarity,
                "textblob_subjectivity": subjectivity,
                "vader_positive": vader_scores['pos'],
                "vader_negative": vader_scores['neg'],
                "vader_neutral": vader_scores['neu'],
                "vader_compound": vader_scores['compound'],
                "financial_sentiment": financial_sentiment,
                "bullish_word_count": bullish_count,
                "bearish_word_count": bearish_count,
                "sentiment_confidence": abs(polarity) + abs(vader_scores['compound'])
            }
        except Exception as e:
            logger.error(f"Error extracting sentiment features: {e}")
            return {}
    
    def _extract_financial_sentiment(self, text: str) -> Dict:
        """Extract financial-specific sentiment features"""
        try:
            text_lower = text.lower()
            words = word_tokenize(text_lower)
            
            # Market term density
            market_term_count = sum(1 for word in words if word in self.market_terms)
            market_term_density = market_term_count / len(words) if words else 0
            
            # Sentiment intensity by market context
            bullish_in_market_context = 0
            bearish_in_market_context = 0
            
            for i, word in enumerate(words):
                if word in self.bullish_words:
                    # Check if near market terms
                    context_window = words[max(0, i-3):min(len(words), i+4)]
                    if any(term in context_window for term in self.market_terms):
                        bullish_in_market_context += 1
                
                elif word in self.bearish_words:
                    context_window = words[max(0, i-3):min(len(words), i+4)]
                    if any(term in context_window for term in self.market_terms):
                        bearish_in_market_context += 1
            
            # Uncertainty indicators
            uncertainty_words = ['maybe', 'might', 'could', 'possibly', 'perhaps', 'uncertain', 'unclear']
            uncertainty_count = sum(1 for word in words if word in uncertainty_words)
            
            # Urgency indicators
            urgency_words = ['urgent', 'immediate', 'quickly', 'fast', 'rapid', 'sudden', 'emergency']
            urgency_count = sum(1 for word in words if word in urgency_words)
            
            return {
                "market_term_density": market_term_density,
                "bullish_market_context": bullish_in_market_context,
                "bearish_market_context": bearish_in_market_context,
                "uncertainty_score": uncertainty_count / len(words) if words else 0,
                "urgency_score": urgency_count / len(words) if words else 0,
                "financial_relevance": market_term_density
            }
        except Exception as e:
            logger.error(f"Error extracting financial sentiment: {e}")
            return {}
    
    def _extract_topic_features(self, text: str) -> Dict:
        """Extract topic modeling features"""
        try:
            # Simple topic classification based on keywords
            text_lower = text.lower()
            
            # Topic categories
            topics = {
                "earnings": ['earnings', 'revenue', 'profit', 'loss', 'quarterly', 'annual'],
                "market_movement": ['price', 'stock', 'market', 'trading', 'volume', 'volatility'],
                "corporate_actions": ['dividend', 'split', 'merger', 'acquisition', 'ipo', 'buyback'],
                "analyst_opinion": ['analyst', 'rating', 'target', 'upgrade', 'downgrade', 'recommendation'],
                "economic_indicators": ['gdp', 'inflation', 'interest', 'rate', 'fed', 'economy'],
                "sector_specific": ['technology', 'healthcare', 'finance', 'energy', 'consumer', 'industrial']
            }
            
            topic_scores = {}
            for topic, keywords in topics.items():
                score = sum(1 for keyword in keywords if keyword in text_lower)
                topic_scores[f"{topic}_score"] = score / len(keywords)
            
            # Dominant topic
            dominant_topic = max(topic_scores.items(), key=lambda x: x[1])[0] if topic_scores else "none"
            
            return {
                **topic_scores,
                "dominant_topic": dominant_topic,
                "topic_diversity": len([score for score in topic_scores.values() if score > 0])
            }
        except Exception as e:
            logger.error(f"Error extracting topic features: {e}")
            return {}
    
    def _extract_entity_features(self, text: str) -> Dict:
        """Extract named entity features"""
        try:
            if self.nlp:
                doc = self.nlp(text)
                
                # Count entities by type
                entity_counts = {}
                for ent in doc.ents:
                    entity_type = ent.label_
                    if entity_type not in entity_counts:
                        entity_counts[entity_type] = 0
                    entity_counts[entity_type] += 1
                
                # Financial entities
                financial_entities = ['MONEY', 'ORG', 'PERSON', 'GPE']  # Money, Organization, Person, Geopolitical
                financial_entity_count = sum(entity_counts.get(ent_type, 0) for ent_type in financial_entities)
                
                return {
                    "total_entities": len(doc.ents),
                    "financial_entities": financial_entity_count,
                    "entity_diversity": len(entity_counts),
                    **{f"entity_{k.lower()}": v for k, v in entity_counts.items()}
                }
            else:
                # Basic entity extraction without spaCy
                return self._extract_basic_entities(text)
        except Exception as e:
            logger.error(f"Error extracting entity features: {e}")
            return {}
    
    def _extract_basic_entities(self, text: str) -> Dict:
        """Basic entity extraction without spaCy"""
        try:
            # Simple regex patterns for basic entities
            money_pattern = r'\$[\d,]+\.?\d*[KMB]?'
            money_matches = len(re.findall(money_pattern, text))
            
            # Company names (simple heuristic)
            company_pattern = r'\b[A-Z][a-z]+ (Inc|Corp|Ltd|LLC|Co\.|Company)\b'
            company_matches = len(re.findall(company_pattern, text))
            
            # Numbers
            number_pattern = r'\b\d+\.?\d*\b'
            number_matches = len(re.findall(number_pattern, text))
            
            return {
                "money_mentions": money_matches,
                "company_mentions": company_matches,
                "number_mentions": number_matches,
                "total_entities": money_matches + company_matches
            }
        except Exception as e:
            logger.error(f"Error in basic entity extraction: {e}")
            return {}
    
    def _extract_readability_features(self, text: str) -> Dict:
        """Extract readability and complexity features"""
        try:
            sentences = sent_tokenize(text)
            words = word_tokenize(text.lower())
            
            if not sentences or not words:
                return {}
            
            # Flesch Reading Ease Score
            avg_sentence_length = len(words) / len(sentences)
            avg_syllables_per_word = np.mean([self._count_syllables(word) for word in words])
            
            flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
            
            # Sentence complexity
            complex_sentences = sum(1 for sent in sentences if len(word_tokenize(sent)) > 20)
            complex_sentence_ratio = complex_sentences / len(sentences)
            
            # Word complexity
            long_words = sum(1 for word in words if len(word) > 6)
            long_word_ratio = long_words / len(words)
            
            return {
                "flesch_score": flesch_score,
                "avg_sentence_length": avg_sentence_length,
                "avg_syllables_per_word": avg_syllables_per_word,
                "complex_sentence_ratio": complex_sentence_ratio,
                "long_word_ratio": long_word_ratio,
                "readability_level": self._classify_readability(flesch_score)
            }
        except Exception as e:
            logger.error(f"Error extracting readability features: {e}")
            return {}
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word"""
        try:
            word = word.lower()
            vowels = 'aeiouy'
            syllable_count = 0
            prev_was_vowel = False
            
            for char in word:
                is_vowel = char in vowels
                if is_vowel and not prev_was_vowel:
                    syllable_count += 1
                prev_was_vowel = is_vowel
            
            # Handle silent 'e'
            if word.endswith('e') and syllable_count > 1:
                syllable_count -= 1
            
            return max(1, syllable_count)
        except:
            return 1
    
    def _classify_readability(self, flesch_score: float) -> str:
        """Classify readability level based on Flesch score"""
        if flesch_score >= 90:
            return "very_easy"
        elif flesch_score >= 80:
            return "easy"
        elif flesch_score >= 70:
            return "fairly_easy"
        elif flesch_score >= 60:
            return "standard"
        elif flesch_score >= 50:
            return "fairly_difficult"
        elif flesch_score >= 30:
            return "difficult"
        else:
            return "very_difficult"
    
    def _extract_temporal_features(self, text: str) -> Dict:
        """Extract temporal features from text"""
        try:
            text_lower = text.lower()
            
            # Time references
            time_words = ['today', 'yesterday', 'tomorrow', 'week', 'month', 'year', 'quarter']
            time_mentions = sum(1 for word in time_words if word in text_lower)
            
            # Urgency indicators
            urgent_words = ['urgent', 'immediate', 'now', 'today', 'asap', 'quickly']
            urgent_mentions = sum(1 for word in urgent_words if word in text_lower)
            
            # Future vs past references
            future_words = ['will', 'going to', 'expected', 'forecast', 'projected', 'anticipated']
            past_words = ['was', 'were', 'had', 'did', 'completed', 'finished', 'achieved']
            
            future_mentions = sum(1 for phrase in future_words if phrase in text_lower)
            past_mentions = sum(1 for phrase in past_words if phrase in text_lower)
            
            return {
                "time_mentions": time_mentions,
                "urgent_mentions": urgent_mentions,
                "future_orientation": future_mentions,
                "past_orientation": past_mentions,
                "temporal_balance": (future_mentions - past_mentions) / (future_mentions + past_mentions + 1)
            }
        except Exception as e:
            logger.error(f"Error extracting temporal features: {e}")
            return {}
    
    def _extract_market_features(self, text: str) -> Dict:
        """Extract market-specific features"""
        try:
            text_lower = text.lower()
            
            # Market sentiment indicators
            positive_market_words = ['bull', 'rally', 'surge', 'gain', 'breakout', 'momentum']
            negative_market_words = ['bear', 'crash', 'fall', 'drop', 'breakdown', 'volatility']
            
            positive_count = sum(1 for word in positive_market_words if word in text_lower)
            negative_count = sum(1 for word in negative_market_words if word in text_lower)
            
            # Volatility indicators
            volatility_words = ['volatile', 'volatility', 'uncertain', 'unstable', 'fluctuate']
            volatility_count = sum(1 for word in volatility_words if word in text_lower)
            
            # Risk indicators
            risk_words = ['risk', 'danger', 'caution', 'warning', 'concern', 'threat']
            risk_count = sum(1 for word in risk_words if word in text_lower)
            
            # Opportunity indicators
            opportunity_words = ['opportunity', 'potential', 'chance', 'possibility', 'prospect']
            opportunity_count = sum(1 for word in opportunity_words if word in text_lower)
            
            return {
                "market_sentiment": (positive_count - negative_count) / (positive_count + negative_count + 1),
                "volatility_mentions": volatility_count,
                "risk_mentions": risk_count,
                "opportunity_mentions": opportunity_count,
                "market_confidence": (positive_count + opportunity_count) / (negative_count + risk_count + 1)
            }
        except Exception as e:
            logger.error(f"Error extracting market features: {e}")
            return {}
    
    def create_text_embeddings(self, texts: List[str]) -> np.ndarray:
        """Create text embeddings using TF-IDF"""
        try:
            if not texts:
                return np.array([])
            
            # Clean and preprocess texts
            cleaned_texts = [self._clean_text(text) for text in texts]
            
            # Create TF-IDF embeddings
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(cleaned_texts)
            
            return tfidf_matrix.toarray()
        except Exception as e:
            logger.error(f"Error creating text embeddings: {e}")
            return np.array([])
    
    def _clean_text(self, text: str) -> str:
        """Clean and preprocess text"""
        try:
            # Remove special characters and numbers
            text = re.sub(r'a-zA-Z\s]', '', text)
            
            # Convert to lowercase
            text = text.lower()
            
            # Remove extra whitespace
            text = ' '.join(text.split())
            
            return text
        except Exception as e:
            logger.error(f"Error cleaning text: {e}")
            return text
    
    def extract_sentiment_timeseries(self, texts: List[str], timestamps: List[datetime]) -> pd.DataFrame:
        """Extract sentiment time series from multiple texts"""
        try:
            if len(texts) != len(timestamps):
                raise ValueError("Texts and timestamps must have same length")
            
            data = []
            for text, timestamp in zip(texts, timestamps):
                features = self.extract_comprehensive_features(text)
                features['timestamp'] = timestamp
                data.append(features)
            
            df = pd.DataFrame(data)
            df = df.set_index('timestamp')
            
            # Calculate rolling averages
            for col in ['textblob_polarity', 'vader_compound', 'financial_sentiment']:
                if col in df.columns:
                    df[f'{col}_ma_1h'] = df[col].rolling('1H').mean()
                    df[f'{col}_ma_4h'] = df[col].rolling('4H').mean()
                    df[f'{col}_ma_24h'] = df[col].rolling('24H').mean()
            
            return df
        except Exception as e:
            logger.error(f"Error extracting sentiment timeseries: {e}")
            return pd.DataFrame()
    
    def get_sentiment_summary(self, texts: List[str]) -> Dict:
        """Get summary statistics for sentiment analysis"""
        try:
            if not texts:
                return {}
            
            sentiments = []
            for text in texts:
                features = self.extract_comprehensive_features(text)
                sentiments.append(features.get('textblob_polarity', 0))
            
            sentiments = np.array(sentiments)
            
            return {
                "mean_sentiment": np.mean(sentiments),
                "std_sentiment": np.std(sentiments),
                "min_sentiment": np.min(sentiments),
                "max_sentiment": np.max(sentiments),
                "positive_ratio": np.mean(sentiments > 0.1),
                "negative_ratio": np.mean(sentiments < -0.1),
                "neutral_ratio": np.mean(np.abs(sentiments) <= 0.1),
                "sentiment_volatility": np.std(sentiments),
                "sentiment_trend": np.polyfit(range(len(sentiments)), sentiments, 1)[0] if len(sentiments) > 1 else 0
            }
        except Exception as e:
            logger.error(f"Error getting sentiment summary: {e}")
            return {}
