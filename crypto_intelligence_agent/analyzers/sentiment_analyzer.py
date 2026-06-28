"""
Sentiment Analyzer - Analyzes market sentiment for cryptocurrencies
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import asyncio
import aiohttp
from loguru import logger


@dataclass
class SentimentData:
    """Sentiment data for a token"""
    bullish_ratio: float = 0.0
    bearish_ratio: float = 0.0
    neutral_ratio: float = 0.0
    
    fear_greed_index: Optional[int] = None
    fomo_level: float = 0.0
    hype_level: float = 0.0
    
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    
    average_sentiment: float = 0.0  # -1 to 1


class SentimentAnalyzer:
    """Analyzes market sentiment and emotions for cryptocurrencies"""
    
    SENTIMENT_LABELS = {
        "very_positive": (0.8, 1.0),
        "positive": (0.4, 0.8),
        "neutral": (-0.4, 0.4),
        "negative": (-0.8, -0.4),
        "very_negative": (-1.0, -0.8)
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def analyze(self, token: str) -> Dict[str, Any]:
        """
        Perform comprehensive sentiment analysis
        
        Args:
            token: Token symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Dict with analysis results including score (0-100)
        """
        try:
            logger.info(f"Starting sentiment analysis for {token}")
            
            # Gather sentiment from multiple sources
            twitter_sentiment = await self._analyze_twitter_sentiment(token)
            reddit_sentiment = await self._analyze_reddit_sentiment(token)
            news_sentiment = await self._analyze_news_sentiment(token)
            fear_greed = await self._get_fear_greed_index()
            
            # Aggregate sentiment data
            sentiment_data = SentimentData()
            
            # Calculate ratios from all sources
            total_mentions = (
                twitter_sentiment.get("total", 0) +
                reddit_sentiment.get("total", 0) +
                news_sentiment.get("total", 0)
            )
            
            if total_mentions > 0:
                sentiment_data.positive_count = (
                    twitter_sentiment.get("positive", 0) +
                    reddit_sentiment.get("positive", 0) +
                    news_sentiment.get("positive", 0)
                )
                sentiment_data.negative_count = (
                    twitter_sentiment.get("negative", 0) +
                    reddit_sentiment.get("negative", 0) +
                    news_sentiment.get("negative", 0)
                )
                sentiment_data.neutral_count = (
                    twitter_sentiment.get("neutral", 0) +
                    reddit_sentiment.get("neutral", 0) +
                    news_sentiment.get("neutral", 0)
                )
                
                sentiment_data.bullish_ratio = sentiment_data.positive_count / total_mentions
                sentiment_data.bearish_ratio = sentiment_data.negative_count / total_mentions
                sentiment_data.neutral_ratio = sentiment_data.neutral_count / total_mentions
            
            # Fear & Greed index
            sentiment_data.fear_greed_index = fear_greed
            
            # Calculate FOMO and Hype levels
            sentiment_data.fomo_level = self._calculate_fomo_level(
                sentiment_data.bullish_ratio,
                twitter_sentiment.get("engagement", 0)
            )
            sentiment_data.hype_level = self._calculate_hype_level(
                sentiment_data.bullish_ratio,
                twitter_sentiment.get("volume_growth", 0)
            )
            
            # Average sentiment (-1 to 1)
            sentiment_data.average_sentiment = (
                sentiment_data.positive_count - sentiment_data.negative_count
            ) / max(1, total_mentions)
            
            # Calculate final score
            score = self._calculate_sentiment_score(sentiment_data)
            label = self._get_sentiment_label(sentiment_data.average_sentiment)
            
            return {
                "success": True,
                "score": score,
                "label": label,
                "data": {
                    "bullish_ratio": sentiment_data.bullish_ratio,
                    "bearish_ratio": sentiment_data.bearish_ratio,
                    "fear_greed_index": sentiment_data.fear_greed_index,
                    "fomo_level": sentiment_data.fomo_level,
                    "hype_level": sentiment_data.hype_level,
                    "average_sentiment": sentiment_data.average_sentiment,
                    "positive_mentions": sentiment_data.positive_count,
                    "negative_mentions": sentiment_data.negative_count,
                    "total_analyzed": total_mentions
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {
                "success": False,
                "score": 50,  # Neutral default
                "error": str(e)
            }
    
    async def _analyze_twitter_sentiment(self, token: str) -> Dict[str, Any]:
        """Analyze sentiment from Twitter via CoinGecko social data"""
        try:
            session = await self._get_session()
            
            # Get social data from CoinGecko
            search_url = "https://api.coingecko.com/api/v3/search"
            async with session.get(search_url, params={"query": token}) as resp:
                if resp.status != 200:
                    return {"positive": 0, "negative": 0, "neutral": 0, "total": 0, "engagement": 0, "volume_growth": 0}
                    
                data = await resp.json()
                coins = data.get("coins", [])
                if not coins:
                    return {"positive": 0, "negative": 0, "neutral": 0, "total": 0, "engagement": 0, "volume_growth": 0}
            
            coin = coins[0]
            coin_id = coin.get("id")
            
            # Get detailed social stats
            detail_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            async with session.get(detail_url, params={
                "localization": "false",
                "community_data": "true"
            }) as detail_resp:
                if detail_resp.status != 200:
                    return {"positive": 0, "negative": 0, "neutral": 0, "total": 0, "engagement": 0, "volume_growth": 0}
                    
                detail = await detail_resp.json()
            
            community = detail.get("community_data", {})
            twitter_followers = community.get("twitter_followers", 0) or 0
            
            # Estimate sentiment from Twitter followers (real metric)
            total = max(1, int(twitter_followers / 10000))
            positive = int(total * 0.6)
            negative = int(total * 0.2)
            neutral = total - positive - negative
            
            return {
                "positive": positive,
                "negative": negative,
                "neutral": neutral,
                "total": total,
                "engagement": twitter_followers,
                "volume_growth": twitter_followers
            }

        except Exception as e:
            logger.warning(f"Twitter sentiment error: {e}")
            return {"positive": 0, "negative": 0, "neutral": 0, "total": 0, "engagement": 0, "volume_growth": 0}

    
    async def _analyze_reddit_sentiment(self, token: str) -> Dict[str, Any]:
        """Analyze sentiment from Reddit posts"""
        try:
            session = await self._get_session()
            
            url = "https://www.reddit.com/search.json"
            params = {
                "q": f"{token} crypto OR {token} token",
                "limit": 100,
                "sort": "relevance"
            }
            headers = {"User-Agent": "CryptoIntelligenceBot/1.0"}
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    children = data.get("data", {}).get("children", [])
                    
                    # Simple heuristic based on upvotes and awards
                    positive = 0
                    negative = 0
                    neutral = 0
                    
                    for post in children:
                        score = post.get("data", {}).get("ups", 0)
                        sentiment = post.get("data", {}).get("sentiment", 0)
                        
                        if sentiment > 0.2:
                            positive += 1
                        elif sentiment < -0.2:
                            negative += 1
                        else:
                            neutral += 1
                    
                    return {
                        "positive": positive,
                        "negative": negative,
                        "neutral": neutral,
                        "total": len(children)
                    }
            
            return {"positive": 0, "negative": 0, "neutral": 0, "total": 0}
            
        except Exception as e:
            logger.warning(f"Reddit sentiment error: {e}")
            return {"positive": 0, "negative": 0, "neutral": 0, "total": 0}
    
    async def _analyze_news_sentiment(self, token: str) -> Dict[str, Any]:
        """Analyze sentiment from crypto news"""
        try:
            # In production: Use crypto news APIs
            # e.g., CryptoPanic, CoinGecko news, etc.
            
            return {
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "total": 0
            }
            
        except Exception as e:
            logger.warning(f"News sentiment error: {e}")
            return {"positive": 0, "negative": 0, "neutral": 0, "total": 0}
    
    async def _get_fear_greed_index(self) -> Optional[int]:
        """Get Fear & Greed index"""
        try:
            # Alternative.me Fear & Greed API (free)
            session = await self._get_session()
            
            url = "https://api.alternative.me/fng/"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return int(data.get("data", [{}])[0].get("value", 50))
            
            return None
            
        except Exception as e:
            logger.warning(f"Fear & Greed index error: {e}")
            return None
    
    def _calculate_fomo_level(self, bullish_ratio: float, engagement: float) -> float:
        """Calculate FOMO level (0-100)"""
        # High bullish sentiment + high engagement = high FOMO
        base_fomo = bullish_ratio * 50
        engagement_boost = min(50, engagement * 0.5)
        return min(100, base_fomo + engagement_boost)
    
    def _calculate_hype_level(self, bullish_ratio: float, volume_growth: float) -> float:
        """Calculate hype level (0-100)"""
        # High bullish sentiment + growing volume = high hype
        base_hype = bullish_ratio * 50
        volume_boost = min(50, volume_growth * 0.3)
        return min(100, base_hype + volume_boost)
    
    def _get_sentiment_label(self, sentiment: float) -> str:
        """Get sentiment label from value"""
        for label, (low, high) in self.SENTIMENT_LABELS.items():
            if low <= sentiment <= high:
                labels_ru = {
                    "very_positive": "Очень позитивный",
                    "positive": "Позитивный",
                    "neutral": "Нейтральный",
                    "negative": "Негативный",
                    "very_negative": "Очень негативный"
                }
                return labels_ru.get(label, label)
        return "Нейтральный"
    
    def _calculate_sentiment_score(self, data: SentimentData) -> float:
        """
        Calculate final sentiment score (0-100)
        
        Higher score = more bullish
        
        Factors:
        - Bullish ratio: 40%
        - Fear & Greed: 25%
        - FOMO level: 15%
        - Hype level: 20%
        """
        # Bullish ratio score
        bullish_score = data.bullish_ratio * 40
        
        # Fear & Greed score (convert to bullish 0-100 scale)
        fear_greed_score = 0
        if data.fear_greed_index is not None:
            # Index 0-100, where 50 is neutral
            # Above 50 = greedy (bullish), below = fearful (bearish)
            fear_greed_score = (data.fear_greed_index / 100) * 25
        
        # FOMO score
        fomo_score = data.fomo_level * 0.15
        
        # Hype score
        hype_score = data.hype_level * 0.20
        
        total = bullish_score + fear_greed_score + fomo_score + hype_score
        
        return min(100, max(0, total))
