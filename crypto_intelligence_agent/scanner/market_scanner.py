"""
Market Scanner - Автоматический поиск лучших монет для покупки

Сканирует рынок и находит монеты с высоким потенциалом роста.
ИСКЛЮЧАЕТ стейблкоины (USDT, USDC, BUSD и т.д.)
"""
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from loguru import logger


# Стейблкоины для исключения
STABLECOINS: Set[str] = {
    "usdt", "usdc", "busd", "dai", "husd", "susd", "nusd", 
    "frax", "lusd", "alusd", "musd", "ousd", "usdp", "usdd",
    "tusd", "xidr", "jpyx", "eurx", "gbpx", "cnhx", "btcx"
}

# Символы стейблкоинов для исключения
STABLECOIN_SYMBOLS: Set[str] = {
    "USDT", "USDC", "BUSD", "DAI", "HUSD", "SUSD", "NUSD",
    "FRAX", "LUSD", "ALUSD", "MUSD", "OUSD", "USDP", "USDD",
    "TUSD", "XIDR", "JPYX", "EURX", "GBPX", "CNHX", "BTCX",
    "UST", "USTC", "LUNA", "LUNA2",  # Крашнувшие стейблкоины
    "USD1", "USD1",  # Worldcoin stablecoin
    "GUSD", "SUSD",  # Gemini, Silvergate
    "EURI", "SEUR",  # Euro stablecoins
    "XAUT", "PAXG",  # Precious metal backed
}


@dataclass
class CoinAnalysis:
    """Анализ одной монеты"""
    symbol: str
    name: str
    rank: int = 0
    
    # Market data
    price: float = 0
    market_cap: float = 0
    volume_24h: float = 0
    price_change_24h: float = 0
    price_change_7d: float = 0
    
    # Scores (0-100)
    social_score: float = 0
    sentiment_score: float = 0
    whale_score: float = 0
    technical_score: float = 0
    volume_score: float = 0
    
    # Final scores
    total_score: float = 0
    growth_potential: float = 0
    
    # Signals
    recommendation: str = "HOLD"
    rationale: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def emoji(self) -> str:
        return {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(self.recommendation, "⚪")
    
    def to_short_card(self) -> str:
        change = f"{self.price_change_24h:+.1f}%"
        return f"{self.emoji} *{self.symbol}*\n   💰 ${self.price:,.4f} | {change} | 📊 {self.total_score:.0f}%"
    
    def to_full_card(self) -> str:
        lines = [
            f"{self.emoji} *{self.symbol}* ({self.name})",
            f"#{self.rank} по капитализации\n",
            f"💰 *Цена:* ${self.price:,.6f}",
            f"📊 *Капитализация:* ${self.market_cap/1e9:.1f}B",
            f"📈 *Изменение 24ч:* {self.price_change_24h:+.1f}%",
            f"📉 *Изменение 7д:* {self.price_change_7d:+.1f}%\n",
            f"🎯 *Рекомендация:* {self.recommendation}",
            f"📊 *Общий балл:* {self.total_score:.0f}/100",
            f"📈 *Потенциал роста:* {self.growth_potential:.0f}%\n",
        ]
        
        if self.rationale:
            lines.append("💡 *Почему покупать:*")
            for r in self.rationale[:3]:
                lines.append(f"• {r}")
            lines.append("")
        
        if self.risks:
            lines.append("⚠️ *Риски:*")
            for r in self.risks[:2]:
                lines.append(f"• {r}")
        
        return "\n".join(lines)


class MarketScanner:
    """Автоматический сканер рынка"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self._last_scan: Optional[datetime] = None
        self._scan_cache: List[CoinAnalysis] = []
        self._scan_interval = timedelta(minutes=15)
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def scan_market(self, limit: int = 100) -> List[CoinAnalysis]:
        """Полное сканирование рынка (без стейблкоинов)"""
        logger.info(f"Starting market scan (limit={limit})...")
        
        session = await self._get_session()
        
        try:
            # Получаем данные с CoinGecko
            coins_data = await self._fetch_coingecko_data(session, limit)
            
            if not coins_data:
                return self._scan_cache
            
            # Фильтруем стейблкоины
            filtered_coins = []
            for coin in coins_data:
                symbol = coin.get("symbol", "").upper()
                name = coin.get("name", "").lower()
                
                # Пропускаем стейблкоины
                if symbol in STABLECOIN_SYMBOLS:
                    continue
                if name in STABLECOINS:
                    continue
                # Также исключаем wrapped токены
                if symbol.startswith("W") and len(symbol) <= 5:
                    continue
                
                filtered_coins.append(coin)
            
            logger.info(f"Filtered {len(coins_data) - len(filtered_coins)} stablecoins, analyzing {len(filtered_coins)} coins")
            
            # Анализируем каждую монету
            tasks = [self._analyze_coin(session, coin) for coin in filtered_coins[:50]]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            analyses = [r for r in results if isinstance(r, CoinAnalysis)]
            analyses.sort(key=lambda x: x.total_score, reverse=True)
            
            # Рассчитываем потенциал
            for coin in analyses:
                coin.growth_potential = self._calculate_growth_potential(coin)
                coin.recommendation = self._get_recommendation(coin)
            
            self._scan_cache = analyses
            self._last_scan = datetime.utcnow()
            
            logger.info(f"Scan complete: {len(analyses)} coins analyzed (no stablecoins)")
            return analyses
            
        except Exception as e:
            logger.error(f"Scan error: {e}")
            return self._scan_cache
    
    async def _fetch_coingecko_data(self, session: aiohttp.ClientSession, limit: int) -> List[Dict]:
        try:
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": min(limit, 250),
                "page": 1,
                "sparkline": "false",
                "price_change_percentage": "24h,7d"
            }
            
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data
                return []
        except Exception as e:
            logger.error(f"CoinGecko error: {e}")
            return []
    
    async def _analyze_coin(self, session: aiohttp.ClientSession, coin_data: Dict) -> CoinAnalysis:
        symbol = coin_data.get("symbol", "").upper()
        name = coin_data.get("name", "")
        rank = coin_data.get("market_cap_rank", 0)
        
        analysis = CoinAnalysis(
            symbol=symbol,
            name=name,
            rank=rank,
            price=coin_data.get("current_price", 0) or 0,
            market_cap=coin_data.get("market_cap", 0) or 0,
            volume_24h=coin_data.get("total_volume", 0) or 0,
            price_change_24h=coin_data.get("price_change_percentage_24h", 0) or 0,
            price_change_7d=coin_data.get("price_change_percentage_7d_in_currency", 0) or 0
        )
        
        analysis.social_score = self._calculate_social_score(coin_data)
        analysis.sentiment_score = self._calculate_sentiment_score(coin_data)
        analysis.whale_score = self._calculate_whale_score(coin_data)
        analysis.technical_score = self._calculate_technical_score(coin_data)
        analysis.volume_score = self._calculate_volume_score(coin_data)
        
        analysis.total_score = (
            analysis.social_score * 0.25 +
            analysis.sentiment_score * 0.20 +
            analysis.whale_score * 0.20 +
            analysis.technical_score * 0.20 +
            analysis.volume_score * 0.15
        )
        
        analysis.rationale = self._generate_rationale(analysis)
        analysis.risks = self._generate_risks(analysis)
        
        return analysis
    
    def _calculate_social_score(self, coin: Dict) -> float:
        score = 50
        volume = coin.get("total_volume", 0) or 0
        market_cap = coin.get("market_cap", 0) or 1
        
        volume_ratio = volume / market_cap if market_cap > 0 else 0
        score += min(20, volume_ratio * 500)
        
        change = abs(coin.get("price_change_percentage_24h", 0) or 0)
        if change > 5:
            score += 15
        elif change > 10:
            score += 25
        elif change > 20:
            score += 35
        
        return min(100, max(0, score))
    
    def _calculate_sentiment_score(self, coin: Dict) -> float:
        score = 50
        change_24h = coin.get("price_change_percentage_24h", 0) or 0
        change_7d = coin.get("price_change_percentage_7d_in_currency", 0) or 0
        
        if change_24h > 0:
            score += min(25, change_24h * 2)
        else:
            if change_24h < -10:
                score += 20
            elif change_24h < -5:
                score += 10
        
        if change_7d > 0:
            score += min(15, change_7d)
        
        return min(100, max(0, score))
    
    def _calculate_whale_score(self, coin: Dict) -> float:
        score = 50
        volume = coin.get("total_volume", 0) or 0
        market_cap = coin.get("market_cap", 0) or 1
        
        volume_millions = volume / 1e6
        if volume_millions > 100:
            score += 30
        elif volume_millions > 50:
            score += 20
        elif volume_millions > 10:
            score += 10
        
        liquidity = volume / market_cap if market_cap > 0 else 0
        if liquidity > 0.1:
            score += 15
        elif liquidity > 0.05:
            score += 10
        
        return min(100, max(0, score))
    
    def _calculate_technical_score(self, coin: Dict) -> float:
        score = 50
        change_24h = coin.get("price_change_percentage_24h", 0) or 0
        change_7d = coin.get("price_change_percentage_7d_in_currency", 0) or 0
        
        if -5 < change_24h < 10:
            score += 20
        elif -10 < change_24h < 20:
            score += 10
        
        if change_7d > 0:
            score += 15
        elif change_7d < -20:
            score += 10
        
        if change_24h > 15:
            score -= 10
        
        return min(100, max(0, score))
    
    def _calculate_volume_score(self, coin: Dict) -> float:
        score = 50
        volume = coin.get("total_volume", 0) or 0
        volume_millions = volume / 1e6
        
        if volume_millions > 500:
            score += 40
        elif volume_millions > 200:
            score += 30
        elif volume_millions > 100:
            score += 20
        elif volume_millions > 50:
            score += 10
        
        return min(100, max(0, score))
    
    def _calculate_growth_potential(self, coin: CoinAnalysis) -> float:
        base = coin.total_score
        
        if coin.market_cap < 1e9:
            base += 15
        elif coin.market_cap < 10e9:
            base += 10
        elif coin.market_cap < 100e9:
            base += 5
        
        if coin.price_change_24h > 5:
            base += 10
        if coin.price_change_7d > 0:
            base += 5
        
        return min(100, max(0, base))
    
    def _get_recommendation(self, coin: CoinAnalysis) -> str:
        if coin.total_score >= 70:
            return "BUY"
        elif coin.total_score >= 55:
            return "HOLD"
        elif coin.total_score < 40:
            return "SELL"
        return "HOLD"
    
    def _generate_rationale(self, coin: CoinAnalysis) -> List[str]:
        reasons = []
        
        if coin.price_change_24h > 10:
            reasons.append(f"Сильный рост 24ч: {coin.price_change_24h:+.1f}%")
        elif coin.price_change_24h > 5:
            reasons.append(f"Позитивная динамика: {coin.price_change_24h:+.1f}%")
        
        if coin.volume_24h > 1e9:
            reasons.append("Высокий объем торгов")
        
        if coin.whale_score > 70:
            reasons.append("Активность крупных игроков")
        
        if coin.sentiment_score > 65:
            reasons.append("Бычьи настроения рынка")
        
        if coin.price_change_24h < -15:
            reasons.append("Возможен отскок от поддержки")
        
        if not reasons:
            reasons.append("Хорошее соотношение риск/награда")
        
        return reasons
    
    def _generate_risks(self, coin: CoinAnalysis) -> List[str]:
        risks = []
        
        if coin.price_change_24h > 20:
            risks.append("Высокая волатильность")
        
        if coin.market_cap < 100e6:
            risks.append("Низкая капитализация")
        
        if coin.price_change_7d < -30:
            risks.append("Длительный нисходящий тренд")
        
        if not risks:
            risks.append("Общие риски крипторынка")
        
        return risks[:3]
    
    def get_top_coins(self, n: int = 10, recommendation: str = None) -> List[CoinAnalysis]:
        if not self._scan_cache:
            return []
        
        coins = self._scan_cache[:n]
        if recommendation:
            coins = [c for c in coins if c.recommendation == recommendation]
        return coins
    
    def get_buy_signals(self, n: int = 5) -> List[CoinAnalysis]:
        if not self._scan_cache:
            return []
        return [c for c in self._scan_cache if c.recommendation == "BUY"][:n]
    
    @property
    def last_scan_time(self) -> Optional[datetime]:
        return self._last_scan
    
    @property
    def needs_rescan(self) -> bool:
        if not self._last_scan:
            return True
        return datetime.utcnow() - self._last_scan > self._scan_interval
