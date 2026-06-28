"""
Volume Analyzer - Analyzes trading volume and liquidity
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import aiohttp
from loguru import logger
import numpy as np

from ..config.settings import API_ENDPOINTS


@dataclass
class VolumeMetrics:
    """Volume and liquidity metrics"""
    current_volume_24h: float = 0.0
    average_volume_7d: float = 0.0
    volume_change_24h: float = 0.0
    
    volume_spike: bool = False
    volume_trend: str = "stable"  # increasing, decreasing, stable
    
    liquidity: float = 0.0
    liquidity_score: float = 0.0
    
    buy_volume_24h: float = 0.0
    sell_volume_24h: float = 0.0
    buy_sell_ratio: float = 1.0
    
    market_cap: float = 0.0
    volume_to_mcap_ratio: float = 0.0


class VolumeAnalyzer:
    """
    Analyzes trading volume and liquidity metrics
    
    Sources:
    - CoinGecko API
    - CoinMarketCap API
    - DexScreener
    - DEX APIs
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.api_keys = self.config.get("api_keys", {})
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
        Perform volume analysis
        
        Args:
            token: Token symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Dict with volume analysis results including score (0-100)
        """
        try:
            logger.info(f"Starting volume analysis for {token}")
            
            # Get volume data
            volume_data = await self._get_volume_data(token)
            
            if not volume_data:
                return {
                    "success": False,
                    "score": 50,
                    "error": "Could not fetch volume data"
                }
            
            # Calculate metrics
            metrics = self._calculate_metrics(volume_data)
            
            # Calculate score
            score = self._calculate_volume_score(metrics)
            
            return {
                "success": True,
                "score": score,
                "liquidity": metrics.liquidity,
                "volume": {
                    "current_24h": metrics.current_volume_24h,
                    "average_7d": metrics.average_volume_7d,
                    "change_24h": metrics.volume_change_24h,
                    "spike": metrics.volume_spike,
                    "trend": metrics.volume_trend
                },
                "liquidity_score": metrics.liquidity_score,
                "buy_sell_ratio": metrics.buy_sell_ratio,
                "low_liquidity": metrics.liquidity < 50000,  # $50k threshold
                "volume_spike": metrics.volume_spike,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Volume analysis error: {e}")
            return {
                "success": False,
                "score": 50,
                "error": str(e)
            }
    
    async def _get_volume_data(self, token: str) -> Optional[Dict[str, Any]]:
        """Fetch volume data from CoinGecko"""
        try:
            session = await self._get_session()
            
            # Search for coin ID
            search_url = "https://api.coingecko.com/api/v3/search"
            
            async with session.get(search_url, params={"query": token}) as response:
                if response.status != 200:
                    return None
                
                search_data = await response.json()
                coins = search_data.get("coins", [])
                
                if not coins:
                    return None
                
                coin_id = coins[0].get("id")
                if not coin_id:
                    return None
            
            # Get market chart data
            chart_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            params = {
                "vs_currency": "usd",
                "days": "7",
                "interval": "hourly"
            }
            
            async with session.get(chart_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    volumes = [v[1] for v in data.get("total_volumes", [])]
                    market_caps = [m[1] for m in data.get("market_caps", [])]
                    prices = [p[1] for p in data.get("prices", [])]
                    
                    # Get current data
                    current_volume = volumes[-1] if volumes else 0
                    avg_volume_7d = np.mean(volumes) if volumes else 0
                    
                    return {
                        "volumes": volumes,
                        "market_caps": market_caps,
                        "prices": prices,
                        "current_volume": current_volume,
                        "avg_volume_7d": avg_volume_7d,
                        "market_cap": market_caps[-1] if market_caps else 0
                    }
            
            return None
            
        except Exception as e:
            logger.warning(f"Volume data fetch error: {e}")
            return None
    
    def _calculate_metrics(self, data: Dict[str, Any]) -> VolumeMetrics:
        """Calculate volume metrics"""
        metrics = VolumeMetrics()
        
        volumes = data.get("volumes", [])
        market_caps = data.get("market_caps", [])
        
        if not volumes:
            return metrics
        
        metrics.current_volume_24h = data.get("current_volume", 0)
        metrics.average_volume_7d = data.get("avg_volume_7d", 0)
        metrics.market_cap = data.get("market_cap", 0)
        
        # Volume change
        if len(volumes) >= 2:
            prev_volume = np.mean(volumes[:len(volumes)//2])
            curr_volume = np.mean(volumes[len(volumes)//2:])
            
            if prev_volume > 0:
                metrics.volume_change_24h = ((curr_volume - prev_volume) / prev_volume) * 100
        
        # Volume spike detection
        if metrics.average_volume_7d > 0:
            spike_ratio = metrics.current_volume_24h / metrics.average_volume_7d
            metrics.volume_spike = spike_ratio > 2.0  # 2x average = spike
        
        # Volume trend
        if len(volumes) >= 24:
            recent = np.mean(volumes[-24:])
            older = np.mean(volumes[:24])
            
            if recent > older * 1.2:
                metrics.volume_trend = "increasing"
            elif recent < older * 0.8:
                metrics.volume_trend = "decreasing"
            else:
                metrics.volume_trend = "stable"
        
        # Volume to market cap ratio
        if metrics.market_cap > 0:
            metrics.volume_to_mcap_ratio = metrics.current_volume_24h / metrics.market_cap
        
        # Estimate liquidity (simplified)
        # In reality, use DEX data or order book data
        metrics.liquidity = min(
            metrics.current_volume_24h * 5,  # Rough estimate
            metrics.current_volume_24h * 10  # Some tokens have higher liquidity
        )
        
        # Liquidity score
        if metrics.liquidity < 10000:
            metrics.liquidity_score = 0
        elif metrics.liquidity < 100000:
            metrics.liquidity_score = 25
        elif metrics.liquidity < 1000000:
            metrics.liquidity_score = 50
        elif metrics.liquidity < 10000000:
            metrics.liquidity_score = 75
        else:
            metrics.liquidity_score = 100
        
        # Buy/Sell ratio from volume analysis
        # For now, assume 50/50 split
        metrics.buy_volume_24h = metrics.current_volume_24h * 0.5
        metrics.sell_volume_24h = metrics.current_volume_24h * 0.5
        metrics.buy_sell_ratio = 1.0
        
        return metrics
    
    def _calculate_volume_score(self, metrics: VolumeMetrics) -> float:
        """
        Calculate volume score (0-100)
        
        Factors:
        - Volume trend: 30%
        - Liquidity: 30%
        - Volume spike: 20%
        - Buy/Sell ratio: 20%
        """
        score = 0
        
        # Volume trend score
        if metrics.volume_trend == "increasing":
            score += 30
        elif metrics.volume_trend == "stable":
            score += 15
        else:  # decreasing
            score += 5
        
        # Liquidity score (already 0-100)
        score += metrics.liquidity_score * 0.30
        
        # Volume spike score
        if metrics.volume_spike:
            score += 20  # Volume spike can indicate interest
        else:
            score += 10
        
        # Buy/Sell ratio score
        if metrics.buy_sell_ratio > 1.2:
            score += 20  # More buys than sells
        elif metrics.buy_sell_ratio > 1.0:
            score += 15
        elif metrics.buy_sell_ratio >= 0.8:
            score += 10
        else:
            score += 5
        
        return min(100, max(0, score))
