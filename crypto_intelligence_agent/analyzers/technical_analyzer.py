"""
Technical Analyzer - Analyzes technical indicators and price data
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
class TechnicalIndicators:
    """Technical analysis indicators"""
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    
    ema_9: Optional[float] = None
    ema_21: Optional[float] = None
    ema_50: Optional[float] = None
    ema_200: Optional[float] = None
    
    vwap: Optional[float] = None
    
    support_levels: List[float] = None
    resistance_levels: List[float] = None
    
    current_price: float = 0.0
    price_change_24h: float = 0.0
    price_change_7d: float = 0.0
    
    volatility: float = 0.0
    atr: Optional[float] = None
    
    bollinger_upper: Optional[float] = None
    bollinger_lower: Optional[float] = None
    
    def __post_init__(self):
        if self.support_levels is None:
            self.support_levels = []
        if self.resistance_levels is None:
            self.resistance_levels = []


class TechnicalAnalyzer:
    """
    Performs technical analysis on cryptocurrency price data
    
    Indicators:
    - RSI (Relative Strength Index)
    - MACD (Moving Average Convergence Divergence)
    - EMA (Exponential Moving Average)
    - VWAP (Volume Weighted Average Price)
    - Support/Resistance levels
    - Bollinger Bands
    - ATR (Average True Range)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.api_keys = self.config.get("api_keys", {})
        self.session: Optional[aiohttp.ClientSession] = None
        
        # CoinGecko API (free tier available)
        self.coingecko_key = self.api_keys.get("coingecko", "")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def analyze(self, token: str) -> Dict[str, Any]:
        """
        Perform technical analysis
        
        Args:
            token: Token symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Dict with technical analysis results including score (0-100)
        """
        try:
            logger.info(f"Starting technical analysis for {token}")
            
            # Get price data
            price_data = await self._get_price_data(token)
            
            if not price_data or not price_data.get("prices"):
                return {
                    "success": False,
                    "score": 50,
                    "error": "Could not fetch price data"
                }
            
            # Calculate indicators
            indicators = self._calculate_indicators(price_data)
            
            # Detect patterns
            patterns = self._detect_patterns(indicators)
            
            # Calculate support/resistance
            levels = self._calculate_support_resistance(price_data)
            indicators.support_levels = levels["support"]
            indicators.resistance_levels = levels["resistance"]
            
            # Calculate technical score
            score = self._calculate_technical_score(indicators, patterns)
            
            return {
                "success": True,
                "score": score,
                "price": indicators.current_price,
                "market_cap": price_data.get("market_cap"),
                "indicators": {
                    "rsi": indicators.rsi,
                    "macd": indicators.macd,
                    "macd_signal": indicators.macd_signal,
                    "macd_histogram": indicators.macd_histogram,
                    "macd_bullish": indicators.macd_histogram > 0 if indicators.macd_histogram else False,
                    "ema_9": indicators.ema_9,
                    "ema_21": indicators.ema_21,
                    "ema_50": indicators.ema_50,
                    "vwap": indicators.vwap,
                    "volatility": indicators.volatility,
                    "high_volatility": indicators.volatility > 0.15,
                    "support_levels": indicators.support_levels,
                    "resistance_levels": indicators.resistance_levels
                },
                "patterns": patterns,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Technical analysis error: {e}")
            return {
                "success": False,
                "score": 50,
                "error": str(e)
            }
    
    async def _get_price_data(self, token: str) -> Dict[str, Any]:
        """Fetch price data from CoinGecko"""
        try:
            session = await self._get_session()
            
            # First, get the coin ID
            search_url = "https://api.coingecko.com/api/v3/search"
            
            async with session.get(search_url, params={"query": token}) as response:
                if response.status != 200:
                    return {}
                
                search_data = await response.json()
                coins = search_data.get("coins", [])
                
                if not coins:
                    return {}
                
                coin_id = coins[0].get("id")
                if not coin_id:
                    return {}
            
            # Get market data
            market_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            params = {
                "vs_currency": "usd",
                "days": "30",  # 30 days of data for analysis
                "interval": "daily"
            }
            
            async with session.get(market_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    prices = [p[1] for p in data.get("prices", [])]
                    volumes = data.get("total_volumes", [])
                    market_caps = data.get("market_caps", [])
                    
                    return {
                        "prices": prices,
                        "volumes": [v[1] for v in volumes],
                        "market_caps": [m[1] for m in market_caps],
                        "coin_id": coin_id,
                        "current_price": prices[-1] if prices else 0,
                        "price_24h_ago": prices[1] if len(prices) > 1 else prices[0] if prices else 0,
                        "price_7d_ago": prices[7] if len(prices) > 7 else prices[0] if prices else 0
                    }
            
            return {}
            
        except Exception as e:
            logger.warning(f"Price data fetch error: {e}")
            return {}
    
    def _calculate_indicators(self, data: Dict[str, Any]) -> TechnicalIndicators:
        """Calculate technical indicators"""
        prices = np.array(data.get("prices", []))
        volumes = np.array(data.get("volumes", []))
        
        indicators = TechnicalIndicators()
        
        if len(prices) < 2:
            return indicators
        
        # Current price and changes
        indicators.current_price = prices[-1]
        indicators.price_change_24h = (
            (prices[-1] - data.get("price_24h_ago", prices[-1])) / 
            data.get("price_24h_ago", prices[-1]) * 100
            if data.get("price_24h_ago") else 0
        )
        indicators.price_change_7d = (
            (prices[-1] - data.get("price_7d_ago", prices[-1])) / 
            data.get("price_7d_ago", prices[-1]) * 100
            if data.get("price_7d_ago") else 0
        )
        
        # RSI (14-period)
        indicators.rsi = self._calculate_rsi(prices, period=14)
        
        # MACD (12, 26, 9)
        macd_result = self._calculate_macd(prices)
        indicators.macd = macd_result["macd"]
        indicators.macd_signal = macd_result["signal"]
        indicators.macd_histogram = macd_result["histogram"]
        
        # EMAs
        indicators.ema_9 = self._calculate_ema(prices, 9)
        indicators.ema_21 = self._calculate_ema(prices, 21)
        indicators.ema_50 = self._calculate_ema(prices, 50) if len(prices) >= 50 else None
        indicators.ema_200 = self._calculate_ema(prices, 200) if len(prices) >= 200 else None
        
        # VWAP
        if len(prices) == len(volumes) and len(volumes) > 0:
            indicators.vwap = self._calculate_vwap(prices, volumes)
        
        # Volatility (standard deviation of returns)
        indicators.volatility = self._calculate_volatility(prices)
        
        # Bollinger Bands
        bb = self._calculate_bollinger_bands(prices)
        indicators.bollinger_upper = bb["upper"]
        indicators.bollinger_lower = bb["lower"]
        
        # ATR approximation
        indicators.atr = indicators.volatility * indicators.current_price
        
        return indicators
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi)
    
    def _calculate_macd(
        self, 
        prices: np.ndarray, 
        fast: int = 12, 
        slow: int = 26, 
        signal: int = 9
    ) -> Dict[str, float]:
        """Calculate MACD"""
        if len(prices) < slow:
            return {"macd": 0, "signal": 0, "histogram": 0}
        
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        
        macd_line = ema_fast - ema_slow
        
        # Signal line (EMA of MACD)
        macd_values = []
        for i in range(slow - 1, len(prices)):
            ema_f = self._calculate_ema(prices[:i+1], fast)
            ema_s = self._calculate_ema(prices[:i+1], slow)
            macd_values.append(ema_f - ema_s)
        
        if len(macd_values) >= signal:
            signal_line = self._calculate_ema(np.array(macd_values), signal)
        else:
            signal_line = macd_line
        
        histogram = macd_line - signal_line
        
        return {
            "macd": float(macd_line),
            "signal": float(signal_line),
            "histogram": float(histogram)
        }
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """Calculate EMA"""
        if len(prices) < period:
            return float(prices[-1]) if len(prices) > 0 else 0
        
        multiplier = 2 / (period + 1)
        ema = np.mean(prices[:period])
        
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        
        return float(ema)
    
    def _calculate_vwap(self, prices: np.ndarray, volumes: np.ndarray) -> float:
        """Calculate VWAP"""
        if len(prices) != len(volumes) or len(volumes) == 0:
            return float(prices[-1]) if len(prices) > 0 else 0
        
        return float(np.sum(prices * volumes) / np.sum(volumes))
    
    def _calculate_volatility(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate volatility (standard deviation of returns)"""
        if len(prices) < period:
            return 0.0
        
        returns = np.diff(prices[-period:]) / prices[-period:-1]
        return float(np.std(returns))
    
    def _calculate_bollinger_bands(
        self, 
        prices: np.ndarray, 
        period: int = 20, 
        std_dev: float = 2.0
    ) -> Dict[str, float]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return {"upper": 0, "middle": 0, "lower": 0}
        
        recent_prices = prices[-period:]
        sma = np.mean(recent_prices)
        std = np.std(recent_prices)
        
        return {
            "upper": float(sma + std_dev * std),
            "middle": float(sma),
            "lower": float(sma - std_dev * std)
        }
    
    def _calculate_support_resistance(self, data: Dict) -> Dict[str, List[float]]:
        """Calculate support and resistance levels"""
        prices = np.array(data.get("prices", []))
        
        if len(prices) < 10:
            return {"support": [], "resistance": []}
        
        # Simple approach: use recent highs and lows
        recent = prices[-30:] if len(prices) >= 30 else prices
        
        # Find local maxima and minima
        support_levels = []
        resistance_levels = []
        
        for i in range(2, len(recent) - 2):
            # Support: local minimum
            if recent[i] < recent[i-1] and recent[i] < recent[i-2] and \
               recent[i] < recent[i+1] and recent[i] < recent[i+2]:
                support_levels.append(float(recent[i]))
            
            # Resistance: local maximum
            if recent[i] > recent[i-1] and recent[i] > recent[i-2] and \
               recent[i] > recent[i+1] and recent[i] > recent[i+2]:
                resistance_levels.append(float(recent[i]))
        
        # Get top 3 levels
        support_levels = sorted(set(support_levels))[-3:] if support_levels else []
        resistance_levels = sorted(set(resistance_levels))[-3:] if resistance_levels else []
        
        return {
            "support": support_levels,
            "resistance": resistance_levels
        }
    
    def _detect_patterns(self, indicators: TechnicalIndicators) -> Dict[str, bool]:
        """Detect common chart patterns"""
        patterns = {}
        
        # RSI patterns
        if indicators.rsi:
            patterns["rsi_oversold"] = indicators.rsi < 30
            patterns["rsi_overbought"] = indicators.rsi > 70
            patterns["rsi_divergence"] = False  # Would need more data for proper detection
        
        # MACD patterns
        patterns["macd_bullish_crossover"] = (
            indicators.macd_histogram is not None and 
            indicators.macd_histogram > 0
        )
        
        # EMA patterns
        if indicators.ema_9 and indicators.ema_21:
            patterns["ema_bullish_cross"] = indicators.ema_9 > indicators.ema_21
        
        # Bollinger patterns
        if indicators.bollinger_upper and indicators.bollinger_lower and indicators.current_price:
            bb_width = indicators.bollinger_upper - indicators.bollinger_lower
            position = (indicators.current_price - indicators.bollinger_lower) / bb_width if bb_width > 0 else 0.5
            patterns["bb_lower_touch"] = position < 0.1
            patterns["bb_upper_touch"] = position > 0.9
        
        return patterns
    
    def _calculate_technical_score(
        self, 
        indicators: TechnicalIndicators,
        patterns: Dict[str, bool]
    ) -> float:
        """
        Calculate technical analysis score (0-100)
        
        Factors:
        - RSI: 20%
        - MACD: 25%
        - Trend (EMAs): 25%
        - Volatility: 15%
        - Price momentum: 15%
        """
        score = 0
        
        # RSI score (lower is better for buying)
        if indicators.rsi:
            if indicators.rsi < 30:
                score += 20  # Oversold - potential buy
            elif indicators.rsi < 40:
                score += 15
            elif indicators.rsi < 60:
                score += 10
            elif indicators.rsi < 70:
                score += 5
            else:
                score += 0  # Overbought
        
        # MACD score
        if indicators.macd_histogram:
            if indicators.macd_histogram > 0:
                score += 25  # Bullish
            else:
                score += 5
        
        # Trend score (EMAs)
        trend_score = 0
        if indicators.current_price and indicators.ema_9:
            if indicators.current_price > indicators.ema_9:
                trend_score += 10
            else:
                trend_score -= 5
        
        if indicators.ema_9 and indicators.ema_21:
            if indicators.ema_9 > indicators.ema_21:
                trend_score += 10
            else:
                trend_score -= 5
        
        if indicators.ema_21 and indicators.ema_50:
            if indicators.ema_21 > indicators.ema_50:
                trend_score += 5
            else:
                trend_score -= 2
        
        score += max(0, min(25, trend_score + 12))  # Normalize to 0-25
        
        # Volatility score (moderate is best)
        if indicators.volatility:
            if 0.02 <= indicators.volatility <= 0.08:
                score += 15
            elif indicators.volatility < 0.02:
                score += 5  # Low volatility
            else:
                score += 0  # High volatility
        
        # Price momentum score
        if indicators.price_change_24h:
            if 1 <= indicators.price_change_24h <= 5:
                score += 10  # Good momentum
            elif indicators.price_change_24h > 5:
                score += 5  # Strong but may reverse
            elif indicators.price_change_24h < -5:
                score += 0  # Strong selloff
            else:
                score += 5  # Mild decline
        
        return min(100, max(0, score))
