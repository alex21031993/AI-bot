"""
Meme Coin Scanner - Advanced System
Поиск потенциальных мем-коинов с высоким риском/наградой
"""
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from loguru import logger


@dataclass
class MemeCoinAnalysis:
    """Анализ мем-коина"""
    symbol: str
    name: str
    price: float
    price_change_1h: float = 0
    price_change_24h: float = 0
    volume_24h: float = 0
    market_cap: float = 0
    liquidity: float = 0
    
    # Meme-specific metrics
    social_score: float = 0
    holder_count: int = 0
    meme_potential: float = 0
    
    # Risk assessment
    risk_score: float = 0
    pump_probability: float = 0
    
    # Analysis
    signals: List[str] = None
    risks: List[str] = None
    recommendation: str = "HOLD"
    
    def __post_init__(self):
        if self.signals is None:
            self.signals = []
        if self.risks is None:
            self.risks = []


class MemeCoinScanner:
    """
    Сканер мем-коинов для Advanced System
    
    Ищет монеты с признаками потенциального пампа:
    - Резкий рост социальной активности
    - Аномальные объемы
    - Новые кошельки
    - Паттерны, характерные для мем-коинов
    """
    
    # Известные мем-токены для отслеживания
    KNOWN_MEME_TOKENS = [
        "dogecoin", "shiba-inu", "pepe", "dogwifcoin", "brett", "popcat",
        "hodl", "mog", "neiro", "chillguy", "act-i", "ai16z", "luna",
        "dogwiftoken", "bonk", "floki", "baby-doge-coin", "samoyedcoin",
        " render-token", "goatseus-maximum"
    ]
    
    def __init__(self):
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session:
            await self.session.close()
    
    async def scan_meme_coins(self, limit: int = 20) -> List[MemeCoinAnalysis]:
        """Сканирует мем-коины и возвращает топ по потенциалу"""
        try:
            session = await self._get_session()
            meme_coins = await self._fetch_meme_coins(session, limit)
            
            analyses = []
            for coin in meme_coins:
                analysis = await self._analyze_meme_coin(session, coin)
                if analysis:
                    analyses.append(analysis)
            
            analyses.sort(key=lambda x: x.meme_potential, reverse=True)
            return analyses[:limit]
            
        except Exception as e:
            logger.error(f"Meme scan error: {e}")
            return []
    
    async def _fetch_meme_coins(self, session: aiohttp.ClientSession, limit: int) -> List[Dict]:
        """Получить список мем-коинов"""
        try:
            # Сначала пробуем искать по категории
            async with session.get(
                f"{self.coingecko_base}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "category": "meme-coin",
                    "order": "volume_desc",
                    "per_page": min(limit * 2, 100),
                    "sparkline": "false",
                    "price_change_percentage": "1h,24h,7d"
                }
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        return data
            
            # Fallback: ищем по известным токенам
            meme_ids = ",".join(self.KNOWN_MEME_TOKENS[:limit])
            async with session.get(
                f"{self.coingecko_base}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "ids": meme_ids,
                    "order": "volume_desc",
                    "per_page": limit,
                    "sparkline": "false",
                    "price_change_percentage": "1h,24h,7d"
                }
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
            return []
            
        except Exception as e:
            logger.error(f"Fetch meme coins error: {e}")
            return []
    
    async def _analyze_meme_coin(self, session: aiohttp.ClientSession, coin: Dict) -> Optional[MemeCoinAnalysis]:
        """Анализ отдельного мем-коина"""
        try:
            symbol = coin.get("symbol", "").upper()
            name = coin.get("name", "")
            price = coin.get("current_price", 0) or 0
            mcap = coin.get("market_cap", 0) or 0
            volume = coin.get("total_volume", 0) or 0
            
            coin_id = coin.get("id", "")
            detail = await self._fetch_coin_detail(session, coin_id)
            
            change_1h = coin.get("price_change_percentage_1h_in_currency", 0) or 0
            change_24h = coin.get("price_change_percentage_24h", 0) or 0
            
            meme_potential = self._calculate_meme_potential(coin, detail)
            risk_score = self._calculate_risk_score(coin, detail)
            pump_prob = self._calculate_pump_probability(change_1h, change_24h, volume, mcap)
            signals = self._extract_signals(coin, detail)
            risks = self._extract_risks(coin, detail)
            recommendation = self._get_recommendation(pump_prob, risk_score)
            social_score = self._calculate_social_score(detail)
            
            return MemeCoinAnalysis(
                symbol=symbol, name=name, price=price,
                price_change_1h=change_1h, price_change_24h=change_24h,
                volume_24h=volume, market_cap=mcap,
                social_score=social_score, meme_potential=meme_potential,
                risk_score=risk_score, pump_probability=pump_prob,
                signals=signals, risks=risks, recommendation=recommendation
            )
            
        except Exception as e:
            logger.error(f"Analyze meme coin error: {e}")
            return None
    
    async def _fetch_coin_detail(self, session: aiohttp.ClientSession, coin_id: str) -> Dict:
        """Получить детальную информацию о монете"""
        try:
            for attempt in range(3):
                async with session.get(
                    f"{self.coingecko_base}/coins/{coin_id}",
                    params={"localization": "false", "community_data": "true", "tickers": "false"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 429:
                        await asyncio.sleep(2 ** attempt)
                        continue
            return {}
        except Exception as e:
            logger.error(f"Fetch coin detail error: {e}")
            return {}
    
    def _calculate_meme_potential(self, coin: Dict, detail: Dict) -> float:
        """Расчет потенциала мем-коина (0-100)"""
        score = 0
        change_1h = abs(coin.get("price_change_percentage_1h_in_currency", 0) or 0)
        change_24h = abs(coin.get("price_change_percentage_24h", 0) or 0)
        
        if change_1h > 20: score += 20
        elif change_1h > 10: score += 15
        elif change_1h > 5: score += 10
        
        if change_24h > 50: score += 20
        elif change_24h > 20: score += 15
        elif change_24h > 10: score += 10
        
        volume = coin.get("total_volume", 0) or 0
        mcap = coin.get("market_cap", 0) or 1
        volume_ratio = volume / mcap if mcap > 0 else 0
        
        if volume_ratio > 0.3: score += 30
        elif volume_ratio > 0.15: score += 20
        elif volume_ratio > 0.05: score += 10
        
        community = detail.get("community_data", {}) or {}
        twitter = community.get("twitter_followers", 0) or 0
        reddit = community.get("reddit_subscribers", 0) or 0
        telegram = community.get("telegram_channel_users_count", 0) or 0
        social_total = twitter + reddit + telegram
        
        if social_total > 1000000: score += 30
        elif social_total > 100000: score += 20
        elif social_total > 10000: score += 10
        
        return min(100, score)
    
    def _calculate_risk_score(self, coin: Dict, detail: Dict) -> float:
        """Расчет риска (0-100, выше = рискованнее)"""
        risk = 30
        mcap = coin.get("market_cap", 0) or 0
        
        if mcap < 10_000_000: risk += 30
        elif mcap < 100_000_000: risk += 20
        elif mcap < 1_000_000_000: risk += 10
        
        change_24h = abs(coin.get("price_change_percentage_24h", 0) or 0)
        if change_24h > 100: risk += 20
        elif change_24h > 50: risk += 10
        
        volume = coin.get("total_volume", 0) or 0
        if mcap > 0 and volume / mcap < 0.02: risk += 20
        elif mcap > 0 and volume / mcap < 0.05: risk += 10
        
        return min(100, risk)
    
    def _calculate_pump_probability(self, change_1h: float, change_24h: float, volume: float, mcap: float) -> float:
        """Расчет вероятности пампа"""
        prob = 30
        if change_1h > 10: prob += 25
        elif change_1h > 5: prob += 15
        elif change_1h > 2: prob += 10
        elif change_1h < -5: prob -= 10
        
        if mcap > 0:
            vol_ratio = volume / mcap
            if vol_ratio > 0.2: prob += 25
            elif vol_ratio > 0.1: prob += 15
            elif vol_ratio > 0.05: prob += 10
        
        if mcap < 500_000_000: prob += 10
        elif mcap > 10_000_000_000: prob -= 15
        
        return max(5, min(95, prob))
    
    def _calculate_social_score(self, detail: Dict) -> float:
        """Расчет социального score"""
        community = detail.get("community_data", {}) or {}
        twitter = community.get("twitter_followers", 0) or 0
        reddit = community.get("reddit_subscribers", 0) or 0
        telegram = community.get("telegram_channel_users_count", 0) or 0
        
        score = 0
        if twitter > 1000000: score += 40
        elif twitter > 100000: score += 25
        elif twitter > 10000: score += 10
        
        if telegram > 50000: score += 30
        elif telegram > 10000: score += 20
        elif telegram > 1000: score += 10
        
        if reddit > 100000: score += 30
        elif reddit > 10000: score += 20
        elif reddit > 1000: score += 10
        
        return min(100, score)
    
    def _extract_signals(self, coin: Dict, detail: Dict) -> List[str]:
        """Извлечение бычьих сигналов"""
        signals = []
        change_1h = coin.get("price_change_percentage_1h_in_currency", 0) or 0
        change_24h = coin.get("price_change_percentage_24h", 0) or 0
        
        if change_1h > 10: signals.append(f"🚀 Сильный рост 1ч: {change_1h:.1f}%")
        elif change_1h > 5: signals.append(f"📈 Рост 1ч: {change_1h:.1f}%")
        
        if change_24h > 30: signals.append(f"🟢 Сильный рост 24ч: {change_24h:.1f}%")
        elif change_24h > 10: signals.append(f"📊 Рост 24ч: {change_24h:.1f}%")
        
        community = detail.get("community_data", {}) or {}
        if community.get("twitter_followers", 0) > 100000: signals.append("🐦 Активное Twitter")
        if community.get("telegram_channel_users_count", 0) > 10000: signals.append("💬 Активный Telegram")
        
        mcap = coin.get("market_cap", 0) or 1
        volume = coin.get("total_volume", 0) or 0
        if mcap > 0 and volume / mcap > 0.15: signals.append("💰 Аномально высокий объем")
        
        if not signals: signals.append("⚪ Стабильная динамика")
        return signals
    
    def _extract_risks(self, coin: Dict, detail: Dict) -> List[str]:
        """Извлечение рисков"""
        risks = []
        mcap = coin.get("market_cap", 0) or 0
        
        if mcap < 10_000_000: risks.append("🔴 Очень низкая капитализация")
        elif mcap < 100_000_000: risks.append("🟠 Низкая капитализация")
        
        change_24h = abs(coin.get("price_change_percentage_24h", 0) or 0)
        if change_24h > 100: risks.append("⚠️ Экстремальная волатильность")
        elif change_24h > 50: risks.append("⚠️ Высокая волатильность")
        
        volume = coin.get("total_volume", 0) or 0
        if mcap > 0 and volume / mcap < 0.02: risks.append("⚠️ Низкая ликвидность")
        
        if not risks: risks.append("✅ Стандартные риски мем-коинов")
        return risks
    
    def _get_recommendation(self, pump_prob: float, risk_score: float) -> str:
        """Рекомендация на основе анализа"""
        adjusted = pump_prob - (risk_score * 0.3)
        if adjusted > 60: return "🟢 STRONG BUY"
        elif adjusted > 40: return "🟡 BUY"
        elif adjusted > 20: return "⚪ HOLD"
        else: return "🔴 AVOID"
    
    def format_report(self, analyses: List[MemeCoinAnalysis]) -> str:
        """Форматирование отчета"""
        if not analyses: return "❌ Не удалось найти мем-коины"
        
        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "🌀 *MEME COIN SCANNER*",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            f"📊 Найдено монет: {len(analyses)}",
            ""
        ]
        
        for i, coin in enumerate(analyses[:5], 1):
            emoji = "🟢" if coin.recommendation.startswith("🟢") else "🟡" if coin.recommendation.startswith("🟡") else "⚪"
            lines.extend([
                f"{emoji} *#{i} {coin.symbol}*",
                f"   💰 ${coin.price:.8f}",
                f"   📈 1ч: {coin.price_change_1h:+.1f}% | 24ч: {coin.price_change_24h:+.1f}%",
                f"   🎯 Pump: {coin.pump_probability:.0f}% | Риск: {coin.risk_score:.0f}%",
                f"   🌀 Потенциал: {coin.meme_potential:.0f}%",
                f"   {coin.recommendation}",
                ""
            ])
        
        lines.extend([
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "⚠️ Это не финансовая рекомендация!",
            "🕐 " + datetime.now().strftime("%H:%M %d.%m.%Y")
        ])
        
        return "\n".join(lines)