"""
Social Media Analyzer - Analyzes social media presence and growth
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import aiohttp
from loguru import logger

from ..config.settings import API_ENDPOINTS


@dataclass
class SocialMetrics:
    """Social media metrics for a token"""
    twitter_mentions: int = 0
    reddit_mentions: int = 0
    telegram_members: int = 0
    discord_members: int = 0
    total_mentions: int = 0
    
    mentions_growth_24h: float = 0.0
    mentions_growth_7d: float = 0.0
    
    engagement_rate: float = 0.0
    influencer_count: int = 0
    
    viral_score: float = 0.0
    trend_score: float = 0.0


class SocialAnalyzer:
    """Analyzes social media presence and engagement for cryptocurrencies"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.api_keys = self.config.get("api_keys", {})
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def analyze(self, token: str) -> Dict[str, Any]:
        """
        Perform comprehensive social media analysis
        
        Args:
            token: Token symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Dict with analysis results including score (0-100)
        """
        try:
            logger.info(f"Starting social analysis for {token}")
            
            # Gather data from all sources
            twitter_data = await self._analyze_twitter(token)
            reddit_data = await self._analyze_reddit(token)
            telegram_data = await self._analyze_telegram(token)
            
            # Calculate metrics
            metrics = SocialMetrics()
            
            metrics.twitter_mentions = twitter_data.get("mentions", 0)
            metrics.reddit_mentions = reddit_data.get("mentions", 0)
            metrics.telegram_members = telegram_data.get("members", 0)
            
            metrics.total_mentions = (
                metrics.twitter_mentions + 
                metrics.reddit_mentions + 
                metrics.telegram_members // 100  # Scale down telegram
            )
            
            metrics.mentions_growth_24h = twitter_data.get("growth_24h", 0)
            metrics.mentions_growth_7d = twitter_data.get("growth_7d", 0)
            
            metrics.engagement_rate = self._calculate_engagement(
                twitter_data.get("likes", 0),
                twitter_data.get("retweets", 0),
                twitter_data.get("replies", 0),
                metrics.twitter_mentions
            )
            
            metrics.influencer_count = twitter_data.get("influencer_mentions", 0)
            metrics.viral_score = self._calculate_viral_score(
                metrics.total_mentions,
                metrics.mentions_growth_24h,
                metrics.engagement_rate
            )
            
            # Calculate final score
            score = self._calculate_social_score(metrics)
            
            return {
                "success": True,
                "score": score,
                "metrics": {
                    "twitter_mentions": metrics.twitter_mentions,
                    "reddit_mentions": metrics.reddit_mentions,
                    "telegram_members": metrics.telegram_members,
                    "total_mentions": metrics.total_mentions,
                    "mentions_growth_24h": metrics.mentions_growth_24h,
                    "mentions_growth_7d": metrics.mentions_growth_7d,
                    "engagement_rate": metrics.engagement_rate,
                    "influencer_count": metrics.influencer_count,
                    "viral_score": metrics.viral_score
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Social analysis error: {e}")
            return {
                "success": False,
                "score": 0,
                "error": str(e)
            }
    
    async def _analyze_twitter(self, token: str) -> Dict[str, Any]:
        """Analyze Twitter/X mentions"""
        try:
            # Simulated data - in production, use Twitter API
            # Note: Twitter API requires elevated access for search
            
            # For demo purposes, we'll use web scraping or alternative APIs
            session = await self._get_session()
            
            # Placeholder for actual Twitter analysis
            # In production, integrate with:
            # - Twitter API v2
            # - Social media aggregators
            # - Alternative data providers
            
            return {
                "mentions": 0,
                "growth_24h": 0,
                "growth_7d": 0,
                "likes": 0,
                "retweets": 0,
                "replies": 0,
                "influencer_mentions": 0
            }
            
        except Exception as e:
            logger.warning(f"Twitter analysis error: {e}")
            return {"mentions": 0, "growth_24h": 0, "growth_7d": 0}
    
    async def _analyze_reddit(self, token: str) -> Dict[str, Any]:
        """Analyze Reddit discussions"""
        try:
            # Reddit API (no key required for basic usage)
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
                    
                    mentions = len(children)
                    upvotes = sum(
                        post["data"].get("ups", 0) 
                        for post in children
                    )
                    
                    return {
                        "mentions": mentions,
                        "total_upvotes": upvotes,
                        "communities": self._extract_communities(children)
                    }
                    
            return {"mentions": 0}
            
        except Exception as e:
            logger.warning(f"Reddit analysis error: {e}")
            return {"mentions": 0}
    
    async def _analyze_telegram(self, token: str) -> Dict[str, Any]:
        """Analyze Telegram groups"""
        try:
            # Telegram group analysis
            # Note: Requires Telegram Bot API or scraping
            
            # For demo - simulate data
            # In production, use Telegram API or data providers
            
            return {
                "groups_found": 0,
                "members": 0,
                "activity_score": 0
            }
            
        except Exception as e:
            logger.warning(f"Telegram analysis error: {e}")
            return {"members": 0}
    
    def _extract_communities(self, posts: List[Dict]) -> List[str]:
        """Extract unique subreddit names"""
        communities = set()
        for post in posts:
            subreddit = post.get("data", {}).get("subreddit", "")
            if subreddit:
                communities.add(subreddit)
        return list(communities)[:10]
    
    def _calculate_engagement(
        self, 
        likes: int, 
        retweets: int, 
        replies: int,
        mentions: int
    ) -> float:
        """Calculate engagement rate"""
        if mentions == 0:
            return 0.0
        
        total_engagement = likes + (retweets * 2) + (replies * 3)
        return min(100, (total_engagement / mentions) * 100)
    
    def _calculate_viral_score(
        self,
        total_mentions: int,
        growth_24h: float,
        engagement_rate: float
    ) -> float:
        """
        Calculate viral spread score (0-100)
        
        Factors:
        - Volume of mentions
        - Growth rate
        - Engagement rate
        """
        # Base score from mention volume (logarithmic scale)
        volume_score = min(30, (total_mentions / 1000) * 30) if total_mentions > 0 else 0
        
        # Growth score
        growth_score = min(40, growth_24h) if growth_24h > 0 else 0
        
        # Engagement score
        engagement_score = min(30, engagement_rate)
        
        return volume_score + growth_score + engagement_score
    
    def _calculate_social_score(self, metrics: SocialMetrics) -> float:
        """
        Calculate final social score (0-100)
        
        Weights:
        - Mention Volume: 25%
        - Growth Rate: 30%
        - Engagement: 25%
        - Influencer Activity: 20%
        """
        # Mention volume score (log scale)
        if metrics.total_mentions > 0:
            volume_score = min(25, (total_mentions / 10000) * 25) * 0.25
        else:
            volume_score = 0
        
        # Growth rate score
        growth_score = min(30, metrics.mentions_growth_24h * 0.3) * 0.30
        
        # Engagement score
        engagement_score = (metrics.engagement_rate / 100) * 25 * 0.25
        
        # Influencer score
        influencer_score = min(20, metrics.influencer_count * 2) * 0.20
        
        # Viral boost
        viral_boost = (metrics.viral_score / 100) * 10
        
        total = volume_score + growth_score + engagement_score + influencer_score + viral_boost
        
        return min(100, max(0, total))
