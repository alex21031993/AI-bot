"""
History Analyzer - Analyzes token history and events
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import aiohttp
from loguru import logger


@dataclass
class TokenHistory:
    """Token historical data"""
    launch_date: Optional[datetime] = None
    age_days: int = 0
    
    price_history: List[Dict] = None
    liquidity_history: List[Dict] = None
    
    major_events: List[Dict] = None
    token_unlocks: List[Dict] = None
    
    holder_count: int = 0
    holder_changes: List[Dict] = None
    
    pump_events: List[Dict] = None
    dump_events: List[Dict] = None
    
    def __post_init__(self):
        if self.price_history is None:
            self.price_history = []
        if self.liquidity_history is None:
            self.liquidity_history = []
        if self.major_events is None:
            self.major_events = []
        if self.token_unlocks is None:
            self.token_unlocks = []
        if self.holder_changes is None:
            self.holder_changes = []
        if self.pump_events is None:
            self.pump_events = []
        if self.dump_events is None:
            self.dump_events = []


class HistoryAnalyzer:
    """
    Analyzes token history, events, and lifecycle
    
    Tracks:
    - Launch date and age
    - Price history
    - Major events (listings, partnerships, etc.)
    - Token unlock schedules
    - Holder changes
    - Pump and dump patterns
    """
    
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
        Analyze token history
        
        Args:
            token: Token symbol
            
        Returns:
            Dict with history analysis
        """
        try:
            logger.info(f"Starting history analysis for {token}")
            
            # Get basic token info
            token_info = await self._get_token_info(token)
            
            # Get historical price data
            price_history = await self._get_price_history(token)
            
            # Analyze patterns
            history = TokenHistory()
            
            if token_info:
                history.launch_date = token_info.get("launch_date")
                history.age_days = token_info.get("age_days", 0)
                history.holder_count = token_info.get("holders", 0)
            
            history.price_history = price_history
            
            # Detect pump/dump events
            history.pump_events = self._detect_pumps(price_history)
            history.dump_events = self._detect_dumps(price_history)
            
            # Calculate history score
            score = self._calculate_history_score(history)
            
            return {
                "success": True,
                "score": score,
                "age_days": history.age_days,
                "holder_count": history.holder_count,
                "launch_date": history.launch_date.isoformat() if history.launch_date else None,
                "pump_events_count": len(history.pump_events),
                "dump_events_count": len(history.dump_events),
                "analysis": {
                    "pumps": history.pump_events,
                    "dumps": history.dump_events,
                    "patterns": self._analyze_patterns(history)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"History analysis error: {e}")
            return {
                "success": False,
                "score": 50,
                "error": str(e)
            }
    
    async def _get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get basic token information"""
        try:
            session = await self._get_session()
            
            # Search for coin
            search_url = "https://api.coingecko.com/api/v3/search"
            
            async with session.get(search_url, params={"query": token}) as response:
                if response.status == 200:
                    data = await response.json()
                    coins = data.get("coins", [])
                    
                    if coins:
                        coin = coins[0]
                        
                        # Estimate launch date from market data
                        # In production, use more accurate sources
                        market_cap_rank = coin.get("market_cap_rank", 0)
                        
                        return {
                            "name": coin.get("name"),
                            "symbol": coin.get("symbol"),
                            "holders": 0,  # CoinGecko doesn't always provide this
                            "age_days": self._estimate_age(market_cap_rank),
                            "launch_date": None  # Would need separate API call
                        }
            
            return None
            
        except Exception as e:
            logger.warning(f"Token info error: {e}")
            return None
    
    def _estimate_age(self, market_cap_rank: int) -> int:
        """Estimate token age based on market cap rank"""
        # Rough estimates based on typical market dynamics
        if market_cap_rank == 0:
            return 0
        
        if market_cap_rank <= 10:
            return 365 * 5  # Top 10 = ~5+ years
        elif market_cap_rank <= 50:
            return 365 * 3  # Top 50 = ~3 years
        elif market_cap_rank <= 100:
            return 365 * 2  # Top 100 = ~2 years
        elif market_cap_rank <= 500:
            return 365  # Top 500 = ~1 year
        elif market_cap_rank <= 1000:
            return 180  # Top 1000 = ~6 months
        else:
            return 90  # Below = ~3 months
        
        return 0
    
    async def _get_price_history(self, token: str) -> List[Dict]:
        """Get historical price data"""
        try:
            session = await self._get_session()
            
            # Search for coin ID
            search_url = "https://api.coingecko.com/api/v3/search"
            
            async with session.get(search_url, params={"query": token}) as response:
                if response.status != 200:
                    return []
                
                search_data = await response.json()
                coins = search_data.get("coins", [])
                
                if not coins:
                    return []
                
                coin_id = coins[0].get("id")
            
            # Get market chart
            chart_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            params = {
                "vs_currency": "usd",
                "days": "365",  # 1 year
                "interval": "daily"
            }
            
            async with session.get(chart_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    prices = data.get("prices", [])
                    
                    history = []
                    for ts, price in prices:
                        history.append({
                            "date": datetime.fromtimestamp(ts / 1000),
                            "price": price
                        })
                    
                    return history
            
            return []
            
        except Exception as e:
            logger.warning(f"Price history error: {e}")
            return []
    
    def _detect_pumps(self, price_history: List[Dict]) -> List[Dict]:
        """Detect pump events (>50% increase in 24h)"""
        pumps = []
        
        if len(price_history) < 2:
            return pumps
        
        for i in range(1, len(price_history)):
            prev_price = price_history[i-1]["price"]
            curr_price = price_history[i]["price"]
            
            if prev_price > 0:
                change = ((curr_price - prev_price) / prev_price) * 100
                
                if change >= 50:  # 50%+ pump
                    pumps.append({
                        "date": price_history[i]["date"],
                        "price_before": prev_price,
                        "price_after": curr_price,
                        "change_percent": change
                    })
        
        return pumps
    
    def _detect_dumps(self, price_history: List[Dict]) -> List[Dict]:
        """Detect dump events (>30% decrease in 24h)"""
        dumps = []
        
        if len(price_history) < 2:
            return dumps
        
        for i in range(1, len(price_history)):
            prev_price = price_history[i-1]["price"]
            curr_price = price_history[i]["price"]
            
            if prev_price > 0:
                change = ((curr_price - prev_price) / prev_price) * 100
                
                if change <= -30:  # 30%+ dump
                    dumps.append({
                        "date": price_history[i]["date"],
                        "price_before": prev_price,
                        "price_after": curr_price,
                        "change_percent": change
                    })
        
        return dumps
    
    def _analyze_patterns(self, history: TokenHistory) -> List[str]:
        """Analyze historical patterns"""
        patterns = []
        
        # Check for pump/dump ratio
        pump_count = len(history.pump_events)
        dump_count = len(history.dump_events)
        
        if pump_count > dump_count * 2:
            patterns.append("Частые пампы - осторожно")
        elif dump_count > pump_count * 2:
            patterns.append("Частые дампы - высокий риск")
        
        # Check for recent activity
        recent_pumps = [
            p for p in history.pump_events
            if (datetime.utcnow() - p["date"]).days < 30
        ]
        
        if len(recent_pumps) >= 3:
            patterns.append("Недавние пампы - риск дампа")
        
        # Age analysis
        if history.age_days < 30:
            patterns.append("Новый токен - высокий риск")
        elif history.age_days > 365:
            patterns.append("Зрелый токен")
        
        return patterns
    
    def _calculate_history_score(self, history: TokenHistory) -> float:
        """
        Calculate history score (0-100)
        
        Factors:
        - Age: 30%
        - Stability (dump frequency): 30%
        - Holder growth: 20%
        - Recent pumps: 20%
        """
        score = 0
        
        # Age score (older = more established = higher score)
        if history.age_days == 0:
            score += 0
        elif history.age_days < 30:
            score += 10
        elif history.age_days < 90:
            score += 20
        elif history.age_days < 180:
            score += 30
        elif history.age_days < 365:
            score += 40
        else:
            score += 50
        
        # Stability score (fewer dumps = better)
        total_events = len(history.pump_events) + len(history.dump_events)
        if total_events > 0:
            dump_ratio = len(history.dump_events) / total_events
            stability_score = (1 - dump_ratio) * 30
            score += stability_score
        else:
            score += 30  # No major events = stable
        
        # Holder score
        if history.holder_count > 100000:
            score += 20
        elif history.holder_count > 10000:
            score += 15
        elif history.holder_count > 1000:
            score += 10
        elif history.holder_count > 100:
            score += 5
        
        # Recent pumps penalty
        recent_pumps = [
            p for p in history.pump_events
            if (datetime.utcnow() - p["date"]).days < 30
        ]
        
        if len(recent_pumps) >= 5:
            score -= 10  # Too many recent pumps = suspicious
        elif len(recent_pumps) >= 3:
            score -= 5
        
        return min(100, max(0, score))
