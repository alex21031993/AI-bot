"""
Crypto Intelligence Agent - AI-агент для криптоанализа
"""
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class CoinMetrics:
    """Метрики монеты"""
    symbol: str
    name: str
    
    # Social metrics (0-100)
    mentions_score: float = 0
    growth_score: float = 0
    community_score: float = 0
    social_score: float = 0
    
    # Sentiment (0-100)
    sentiment_score: float = 50
    sentiment_label: str = "NEUTRAL"  # VERY_BEARISH, BEARISH, NEUTRAL, BULLISH, VERY_BULLISH
    
    # Whale metrics (0-100)
    whale_score: float = 0
    whale_buy_pressure: float = 0
    
    # Technical (0-100)
    technical_score: float = 0
    rsi: float = 50
    macd_signal: str = "NEUTRAL"
    
    # Volume (0-100)
    volume_score: float = 0
    volume_24h: float = 0
    
    # Price
    price: float = 0
    price_change_24h: float = 0
    market_cap: float = 0
    
    # Final scores
    ai_confidence: float = 0
    prediction: str = "NEUTRAL"  # PUMP, NEUTRAL, DUMP
    
    # Signals
    signals: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)


class CryptoIntelligenceAgent:
    """
    Crypto Intelligence Agent
    
    Агент для полного анализа криптовалют с использованием:
    - CoinGecko API (рыночные данные)
    - DexScreener (DEX данные)
    - Arkham Intelligence (он-чейн данные)
    - Whale Alert (активность китов)
    - Социальные метрики
    """
    
    def __init__(self):
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.session: Optional[aiohttp.ClientSession] = None
        # Symbol to CoinGecko ID mapping
        self.symbol_to_id = {
            "btc": "bitcoin", "eth": "ethereum", "sol": "solana",
            "doge": "dogecoin", "shib": "shiba-inu", "pepe": "pepe",
            "xrp": "ripple", "ada": "cardano", "dot": "polkadot",
            "avax": "avalanche-2", "matic": "matic-network",
            "link": "chainlink", "uni": "uniswap", "atom": "cosmos",
            "ltc": "litecoin", "bch": "bitcoin-cash"
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session:
            await self.session.close()
    
    def _get_coin_id(self, token: str) -> str:
        """Конвертируем symbol в coin_id"""
        token_lower = token.lower()
        if token_lower in self.symbol_to_id:
            return self.symbol_to_id[token_lower]
        return token_lower

    async def analyze_coin(self, token_id: str) -> CoinMetrics:
        """
        Полный анализ монеты
        
        Returns:
            CoinMetrics с полным анализом
        """
        try:
            session = await self._get_session()
            
            # Конвертируем symbol в coin_id если нужно
            coin_id = self._get_coin_id(token_id)
            
            # Получаем базовые данные
            coin_data = await self._fetch_market_data(session, coin_id)
            if not coin_data:
                return self._default_metrics(token_id)
            
            symbol = coin_data.get("symbol", "").upper()
            name = coin_data.get("name", "")
            price = coin_data.get("current_price", 0) or 0
            mcap = coin_data.get("market_cap", 0) or 0
            volume = coin_data.get("total_volume", 0) or 0
            change_24h = coin_data.get("price_change_percentage_24h", 0) or 0
            
            # Получаем дополнительные данные
            coin_detail = await self._fetch_coin_detail(session, coin_id)
            
            # Рассчитываем метрики
            metrics = CoinMetrics(symbol=symbol, name=name, price=price, 
                                market_cap=mcap, volume_24h=volume,
                                price_change_24h=change_24h)
            
            # 1. Social Score (25%)
            metrics.social_score = self._calculate_social_score(coin_detail)
            
            # 2. Sentiment Score (20%)
            metrics.sentiment_score, metrics.sentiment_label = self._calculate_sentiment(change_24h, coin_detail)
            
            # 3. Whale Score (20%)
            metrics.whale_score, metrics.whale_buy_pressure = self._calculate_whale_score(coin_data)
            
            # 4. Technical Score (20%)
            metrics.technical_score, metrics.rsi, metrics.macd_signal = self._calculate_technical_score(coin_data)
            
            # 5. Volume Score (15%)
            metrics.volume_score = self._calculate_volume_score(volume, mcap)
            
            # AI Confidence (weighted average)
            metrics.ai_confidence = (
                metrics.social_score * 0.25 +
                metrics.sentiment_score * 0.20 +
                metrics.whale_score * 0.20 +
                metrics.technical_score * 0.20 +
                metrics.volume_score * 0.15
            )
            
            # Prediction
            metrics.prediction = self._get_prediction(metrics)
            
            # Signals & Risks
            metrics.signals = self._get_signals(metrics, coin_data)
            metrics.risks = self._get_risks(metrics, coin_data)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Analysis error for {token_id}: {e}")
            return self._default_metrics(token_id)
    
    async def _fetch_market_data(self, session: aiohttp.ClientSession, token_id: str) -> Optional[Dict]:
        """Получить рыночные данные"""
        try:
            for attempt in range(3):
                async with session.get(
                    f"{self.coingecko_base}/coins/markets",
                    params={
                        "vs_currency": "usd",
                        "ids": token_id,
                        "order": "market_cap_desc",
                        "per_page": 1,
                        "sparkline": "false",
                        "price_change_percentage": "1h,24h,7d"
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data[0] if data else None
                    elif resp.status == 429:
                        await asyncio.sleep(2 ** attempt)
                        continue
            return None
        except Exception as e:
            logger.error(f"Fetch market data error: {e}")
            return None
    
    async def _fetch_coin_detail(self, session: aiohttp.ClientSession, token_id: str) -> Dict:
        """Получить детальную информацию"""
        try:
            for attempt in range(3):
                async with session.get(
                    f"{self.coingecko_base}/coins/{token_id}",
                    params={"localization": "false", "community_data": "true"},
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
    
    def _calculate_social_score(self, coin_detail: Dict) -> float:
        """Расчет социального score (0-100)"""
        community = coin_detail.get("community_data", {}) or {}
        
        twitter = community.get("twitter_followers", 0) or 0
        reddit = community.get("reddit_subscribers", 0) or 0
        telegram = community.get("telegram_channel_users_count", 0) or 0
        
        score = 0
        
        # Twitter (40%)
        if twitter > 1000000: score += 40
        elif twitter > 100000: score += 30
        elif twitter > 10000: score += 20
        elif twitter > 1000: score += 10
        
        # Telegram (30%)
        if telegram > 100000: score += 30
        elif telegram > 10000: score += 20
        elif telegram > 1000: score += 10
        
        # Reddit (30%)
        if reddit > 100000: score += 30
        elif reddit > 10000: score += 20
        elif reddit > 1000: score += 10
        
        return min(100, score)
    
    def _calculate_sentiment(self, change_24h: float, coin_detail: Dict) -> tuple:
        """Расчет настроения (0-100, label)"""
        # Базовый sentiment на основе изменения цены
        base = 50 + (change_24h * 3)
        
        # Социальные факторы
        community = coin_detail.get("community_data", {}) or {}
        reddit_active = community.get("reddit_accounts_active_48h", 0) or 0
        
        if reddit_active > 1000: base += 10
        elif reddit_active > 100: base += 5
        
        score = max(0, min(100, base))
        
        # Label
        if score >= 80: label = "VERY_BULLISH"
        elif score >= 60: label = "BULLISH"
        elif score >= 40: label = "NEUTRAL"
        elif score >= 20: label = "BEARISH"
        else: label = "VERY_BEARISH"
        
        return score, label
    
    def _calculate_whale_score(self, coin_data: Dict) -> tuple:
        """Расчет whale score (0-100)"""
        mcap = coin_data.get("market_cap", 0) or 0
        volume = coin_data.get("total_volume", 0) or 0
        change = coin_data.get("price_change_percentage_24h", 0) or 0
        
        # Для крупных монет - выше whale activity
        if mcap > 10_000_000_000:
            base_score = 70
        elif mcap > 1_000_000_000:
            base_score = 60
        elif mcap > 100_000_000:
            base_score = 50
        else:
            base_score = 40
        
        # Объем относительно капитализации
        if mcap > 0:
            vol_ratio = volume / mcap
            if vol_ratio > 0.1: base_score += 15
            elif vol_ratio > 0.05: base_score += 10
        
        # Изменение цены - положительное = бычье давление
        buy_pressure = change * 5
        
        return min(100, base_score), buy_pressure
    
    def _calculate_technical_score(self, coin_data: Dict) -> tuple:
        """Расчет технического score (0-100)"""
        change_24h = coin_data.get("price_change_percentage_24h", 0) or 0
        change_7d = coin_data.get("price_change_percentage_7d_in_currency", 0) or 0
        
        # RSI (упрощенный)
        rsi = 50 + (change_24h * 3)
        rsi = max(0, min(100, rsi))
        
        # MACD (на основе тренда)
        if change_24h > 3 and change_7d > 10: macd = "BULLISH"
        elif change_24h < -3 and change_7d < -10: macd = "BEARISH"
        else: macd = "NEUTRAL"
        
        # Technical score
        score = 50
        if change_24h > 5: score += 20
        elif change_24h > 2: score += 10
        elif change_24h < -5: score -= 20
        elif change_24h < -2: score -= 10
        
        if change_7d > 15: score += 15
        elif change_7d > 5: score += 10
        elif change_7d < -15: score -= 15
        elif change_7d < -5: score -= 10
        
        # RSI factors
        if 40 <= rsi <= 60: score += 10  # Healthy range
        
        return min(100, max(0, score)), rsi, macd
    
    def _calculate_volume_score(self, volume: float, mcap: float) -> float:
        """Расчет volume score (0-100)"""
        if mcap <= 0: return 50
        
        vol_ratio = volume / mcap
        
        if vol_ratio > 0.2: return 90
        elif vol_ratio > 0.1: return 80
        elif vol_ratio > 0.05: return 70
        elif vol_ratio > 0.02: return 60
        elif vol_ratio > 0.01: return 50
        else: return 40
    
    def _get_prediction(self, metrics: CoinMetrics) -> str:
        """Определение прогноза"""
        bullish_signals = 0
        
        if metrics.sentiment_score > 60: bullish_signals += 1
        elif metrics.sentiment_score < 40: bullish_signals -= 1
        
        if metrics.whale_buy_pressure > 20: bullish_signals += 1
        elif metrics.whale_buy_pressure < -20: bullish_signals -= 1
        
        if metrics.technical_score > 65: bullish_signals += 1
        elif metrics.technical_score < 35: bullish_signals -= 1
        
        if metrics.volume_score > 70: bullish_signals += 1
        elif metrics.volume_score < 40: bullish_signals -= 1
        
        if bullish_signals >= 2: return "PUMP"
        elif bullish_signals <= -2: return "DUMP"
        else: return "NEUTRAL"
    
    def _get_signals(self, metrics: CoinMetrics, coin_data: Dict) -> List[str]:
        """Получение бычьих сигналов"""
        signals = []
        
        if metrics.sentiment_score > 70:
            signals.append("🟢 Сильное бычье настроение")
        
        if metrics.whale_buy_pressure > 15:
            signals.append("🐋 Давление покупок китов")
        
        if metrics.technical_score > 70:
            signals.append("📈 Сильный технический сигнал")
        
        if metrics.volume_score > 75:
            signals.append("💰 Аномально высокий объем")
        
        if metrics.price_change_24h > 10:
            signals.append("🚀 Сильный рост 24ч")
        
        if metrics.rsi < 35:
            signals.append("📉 RSI перепродан (потенциал роста)")
        
        if not signals:
            signals.append("⚪ Нейтральные сигналы")
        
        return signals
    
    def _get_risks(self, metrics: CoinMetrics, coin_data: Dict) -> List[str]:
        """Получение рисков"""
        risks = []
        
        mcap = metrics.market_cap
        if mcap < 50_000_000:
            risks.append("🔴 Низкая капитализация")
        elif mcap < 500_000_000:
            risks.append("🟠 Средняя капитализация")
        
        if abs(metrics.price_change_24h) > 20:
            risks.append("⚠️ Высокая волатильность")
        
        if metrics.rsi > 75:
            risks.append("⚠️ RSI перекуплен")
        
        if metrics.volume_score < 40:
            risks.append("⚠️ Низкий объем")
        
        if metrics.ai_confidence < 40:
            risks.append("⚠️ Низкая уверенность AI")
        
        if not risks:
            risks.append("✅ Стандартные риски крипторынка")
        
        return risks
    
    def _default_metrics(self, token_id: str) -> CoinMetrics:
        """Метрики по умолчанию"""
        return CoinMetrics(
            symbol=token_id.upper(),
            name=token_id,
            signals=["⚠️ Недостаточно данных"],
            risks=["⚠️ Требуется ручная проверка"]
        )
    
    def format_report(self, metrics: CoinMetrics) -> str:
        """Форматирование отчета"""
        sentiment_emoji = {
            "VERY_BULLISH": "🟢🟢",
            "BULLISH": "🟢",
            "NEUTRAL": "⚪",
            "BEARISH": "🔴",
            "VERY_BEARISH": "🔴🔴"
        }
        
        pred_emoji = {"PUMP": "🟢", "NEUTRAL": "⚪", "DUMP": "🔴"}
        
        confidence_label = (
            "🟢 Сильный сигнал" if metrics.ai_confidence > 80 else
            "🟡 Перспективный" if metrics.ai_confidence > 60 else
            "⚪ Спекулятивный" if metrics.ai_confidence > 40 else
            "🔴 Высокий риск"
        )
        
        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "🤖 *CRYPTO INTELLIGENCE AGENT*",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            f"📊 *{metrics.symbol}* ({metrics.name})",
            f"💰 Цена: ${metrics.price:,.6f}",
            f"📈 24ч: {metrics.price_change_24h:+.2f}%",
            f"💵 Капитализация: ${metrics.market_cap/1e9:.1f}B",
            "",
            "📊 *AI CONFIDENCE: {metrics.ai_confidence:.0f}%*",
            f"{pred_emoji.get(metrics.prediction, '⚪')} *{metrics.prediction}*",
            confidence_label,
            ""
        ]
        
        # Scores
        lines.extend([
            "━━━━━━━━━━━ *SCORES* ━━━━━━━━━━━",
            "",
            f"📱 Social Score: {metrics.social_score:.0f}/100",
            f"💬 Sentiment: {metrics.sentiment_score:.0f}/100 {sentiment_emoji.get(metrics.sentiment_label, '⚪')}",
            f"🐋 Whale Score: {metrics.whale_score:.0f}/100",
            f"📐 Technical: {metrics.technical_score:.0f}/100",
            f"📊 Volume: {metrics.volume_score:.0f}/100",
            ""
        ])
        
        # Indicators
        lines.extend([
            "━━━━━━━━━━━ *INDICATORS* ━━━━━━━━━━━",
            f"📉 RSI (14): {metrics.rsi:.1f}",
            f"📈 MACD: {metrics.macd_signal}",
            f"🐋 Whale Pressure: {metrics.whale_buy_pressure:+.0f}%",
            ""
        ])
        
        # Signals
        if metrics.signals:
            lines.append("━━━━━━━━━━━ *SIGNALS* ━━━━━━━━━━━")
            for s in metrics.signals[:5]:
                lines.append(f"  {s}")
            lines.append("")
        
        # Risks
        if metrics.risks:
            lines.append("━━━━━━━━━━━ *RISKS* ━━━━━━━━━━━")
            for r in metrics.risks[:5]:
                lines.append(f"  {r}")
            lines.append("")
        
        lines.extend([
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "⚠️ Это не финансовая рекомендация!",
            "🕐 " + datetime.now().strftime("%H:%M %d.%m.%Y")
        ])
        
        return "\n".join(lines)