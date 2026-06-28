"""
Early Pump Detector - Advanced System
Обнаружение ранних признаков пампа
"""
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class PumpSignal:
    """Сигнал потенциального пампа"""
    symbol: str
    name: str
    price: float
    price_change_1h: float = 0
    price_change_24h: float = 0
    
    # Сигналы
    volume_spike: float = 0  # Насколько объем больше обычного
    social_spike: float = 0  # Рост социальной активности
    whale_activity: float = 0  # Активность китов
    
    # Оценки
    pump_probability: float = 0
    confidence: float = 0
    time_to_pump_hours: float = 0
    
    # Metрики
    market_cap: float = 0
    volume_24h: float = 0
    
    # Сигналы
    signals: List[str] = None
    reasons: List[str] = None
    
    def __post_init__(self):
        if self.signals is None:
            self.signals = []
        if self.reasons is None:
            self.reasons = []


class EarlyPumpDetector:
    """
    Детектор ранних пампов
    
    Ищет монеты с ранними признаками пампа:
    - Аномальный рост объема
    - Рост социальной активности
    - Активность китов
    - Технические сигналы
    """
    
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
    
    async def detect_pumps(self, limit: int = 20) -> List[PumpSignal]:
        """Обнаружить потенциальные пампы"""
        try:
            session = await self._get_session()
            
            # Получаем топ монеты с высоким объемом
            coins = await self._fetch_active_coins(session, limit * 3)
            
            signals = []
            for coin in coins:
                signal = await self._analyze_pump_signal(session, coin)
                if signal and signal.pump_probability > 40:
                    signals.append(signal)
            
            # Сортируем по вероятности пампа
            signals.sort(key=lambda x: x.pump_probability, reverse=True)
            return signals[:limit]
            
        except Exception as e:
            logger.error(f"Pump detection error: {e}")
            return []
    
    async def _fetch_active_coins(self, session: aiohttp.ClientSession, limit: int) -> List[Dict]:
        """Получить активные монеты"""
        try:
            async with session.get(
                f"{self.coingecko_base}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "order": "volume_desc",
                    "per_page": limit,
                    "page": 1,
                    "sparkline": "false",
                    "price_change_percentage": "1h,24h,7d"
                }
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
            return []
        except Exception as e:
            logger.error(f"Fetch active coins error: {e}")
            return []
    
    async def _analyze_pump_signal(self, session: aiohttp.ClientSession, coin: Dict) -> Optional[PumpSignal]:
        """Анализ сигнала пампа"""
        try:
            symbol = coin.get("symbol", "").upper()
            name = coin.get("name", "")
            price = coin.get("current_price", 0) or 0
            mcap = coin.get("market_cap", 0) or 0
            volume = coin.get("total_volume", 0) or 0
            
            coin_id = coin.get("id", "")
            detail = await self._fetch_detail(session, coin_id)
            
            # Метрики изменения
            change_1h = coin.get("price_change_percentage_1h_in_currency", 0) or 0
            change_24h = coin.get("price_change_percentage_24h", 0) or 0
            
            # Volume spike
            volume_spike = self._calculate_volume_spike(volume, mcap, coin)
            
            # Social spike
            social_spike = self._calculate_social_spike(detail)
            
            # Whale activity
            whale_activity = self._calculate_whale_activity(coin, detail)
            
            # Pump probability
            pump_prob = self._calculate_pump_probability(
                change_1h, change_24h, volume_spike, social_spike, whale_activity, mcap
            )
            
            # Confidence
            confidence = self._calculate_confidence(coin, detail)
            
            # Time to pump
            time_to_pump = self._estimate_time_to_pump(change_1h, volume_spike)
            
            # Signals and reasons
            signals = self._extract_signals(coin, detail, volume_spike, social_spike)
            reasons = self._extract_reasons(change_1h, change_24h, volume_spike, social_spike, whale_activity)
            
            return PumpSignal(
                symbol=symbol, name=name, price=price,
                price_change_1h=change_1h, price_change_24h=change_24h,
                volume_spike=volume_spike, social_spike=social_spike,
                whale_activity=whale_activity, pump_probability=pump_prob,
                confidence=confidence, time_to_pump_hours=time_to_pump,
                market_cap=mcap, volume_24h=volume,
                signals=signals, reasons=reasons
            )
            
        except Exception as e:
            logger.error(f"Analyze pump signal error: {e}")
            return None
    
    async def _fetch_detail(self, session: aiohttp.ClientSession, coin_id: str) -> Dict:
        """Получить детали монеты"""
        try:
            for attempt in range(3):
                async with session.get(
                    f"{self.coingecko_base}/coins/{coin_id}",
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
            logger.error(f"Fetch detail error: {e}")
            return {}
    
    def _calculate_volume_spike(self, volume: float, mcap: float, coin: Dict) -> float:
        """Расчет аномальности объема (0-100)"""
        if mcap <= 0: return 0
        
        vol_ratio = volume / mcap
        
        # Нормальный объем для разных типов монет
        if mcap > 10_000_000_000:
            normal_ratio = 0.03
        elif mcap > 1_000_000_000:
            normal_ratio = 0.05
        elif mcap > 100_000_000:
            normal_ratio = 0.08
        else:
            normal_ratio = 0.15
        
        # Насколько объем превышает нормальный
        spike = (vol_ratio / normal_ratio - 1) * 100
        return max(0, min(100, spike))
    
    def _calculate_social_spike(self, detail: Dict) -> float:
        """Расчет роста социальной активности"""
        community = detail.get("community_data", {}) or {}
        
        twitter = community.get("twitter_followers", 0) or 0
        reddit = community.get("reddit_subscribers", 0) or 0
        telegram = community.get("telegram_channel_users_count", 0) or 0
        
        total = twitter + reddit + telegram
        
        if total > 5000000: return 80
        elif total > 500000: return 60
        elif total > 50000: return 40
        elif total > 5000: return 20
        else: return 10
    
    def _calculate_whale_activity(self, coin: Dict, detail: Dict) -> float:
        """Расчет активности китов"""
        mcap = coin.get("market_cap", 0) or 0
        
        # Для больших монет активность китов выше
        if mcap > 10_000_000_000:
            return 70
        elif mcap > 1_000_000_000:
            return 55
        elif mcap > 100_000_000:
            return 40
        else:
            return 25
    
    def _calculate_pump_probability(self, change_1h: float, change_24h: float, 
                                    volume_spike: float, social_spike: float,
                                    whale_activity: float, mcap: float) -> float:
        """Расчет вероятности пампа"""
        prob = 25  # Базовый
        
        # Ценовое движение (важный фактор)
        if change_1h > 15: prob += 30
        elif change_1h > 8: prob += 20
        elif change_1h > 3: prob += 10
        elif change_1h < -5: prob -= 15
        
        if change_24h > 30: prob += 20
        elif change_24h > 15: prob += 10
        elif change_24h > 5: prob += 5
        
        # Volume spike
        if volume_spike > 100: prob += 25
        elif volume_spike > 50: prob += 15
        elif volume_spike > 20: prob += 10
        
        # Social spike
        if social_spike > 60: prob += 15
        elif social_spike > 40: prob += 10
        
        # Whale activity
        if whale_activity > 60: prob += 10
        
        # Размер капитализации (меньше = выше потенциал)
        if mcap < 50_000_000: prob += 10
        elif mcap < 500_000_000: prob += 5
        elif mcap > 10_000_000_000: prob -= 10
        
        return max(5, min(95, prob))
    
    def _calculate_confidence(self, coin: Dict, detail: Dict) -> float:
        """Расчет уверенности в сигнале"""
        conf = 50
        
        # Наличие социальных данных
        community = detail.get("community_data", {}) or {}
        if community:
            conf += 20
        
        # Возраст
        if "genesis_date" in detail and detail["genesis_date"]:
            conf += 15
        
        # Объем
        volume = coin.get("total_volume", 0) or 0
        if volume > 10_000_000: conf += 15
        
        return min(95, conf)
    
    def _estimate_time_to_pump(self, change_1h: float, volume_spike: float) -> float:
        """Оценка времени до пампа в часах"""
        if change_1h > 10 and volume_spike > 50:
            return 1  # Очень скоро
        elif change_1h > 5 and volume_spike > 30:
            return 3
        elif change_1h > 2:
            return 12
        else:
            return 24
    
    def _extract_signals(self, coin: Dict, detail: Dict, volume_spike: float, social_spike: float) -> List[str]:
        """Извлечение технических сигналов"""
        signals = []
        
        change_1h = coin.get("price_change_percentage_1h_in_currency", 0) or 0
        change_24h = coin.get("price_change_percentage_24h", 0) or 0
        
        if change_1h > 5: signals.append("🚀 Быстрый рост 1ч")
        if volume_spike > 50: signals.append("📊 Аномальный объем")
        if social_spike > 50: signals.append("🐦 Социальный всплеск")
        
        if change_24h > 20: signals.append("🟢 Сильный бычий тренд")
        elif change_24h > 10: signals.append("📈 Постепенный рост")
        
        if not signals:
            signals.append("⚪ Формирование базы")
        
        return signals
    
    def _extract_reasons(self, change_1h: float, change_24h: float,
                         volume_spike: float, social_spike: float,
                         whale_activity: float) -> List[str]:
        """Извлечение причин"""
        reasons = []
        
        if change_1h > 10: reasons.append(f"Рост 1ч: {change_1h:.1f}%")
        if volume_spike > 50: reasons.append(f"Объем вырос на {volume_spike:.0f}%")
        if social_spike > 40: reasons.append("Рост социальной активности")
        if whale_activity > 50: reasons.append("Активность китов")
        
        if not reasons:
            reasons.append("Накапливание перед движением")
        
        return reasons
    
    def format_report(self, signals: List[PumpSignal]) -> str:
        """Форматирование отчета"""
        if not signals:
            return "❌ Не обнаружено сигналов пампа"
        
        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "📈 *EARLY PUMP DETECTOR*",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            f"🔍 Найдено сигналов: {len(signals)}",
            ""
        ]
        
        for i, signal in enumerate(signals[:5], 1):
            emoji = "🟢" if signal.pump_probability > 70 else "🟡" if signal.pump_probability > 50 else "⚪"
            
            time_str = f"~{signal.time_to_pump_hours:.0f}ч" if signal.time_to_pump_hours < 24 else "1д+"
            
            lines.extend([
                f"{emoji} *#{i} {signal.symbol}*",
                f"   💰 ${signal.price:.8f}",
                f"   📈 1ч: {signal.price_change_1h:+.1f}% | 24ч: {signal.price_change_24h:+.1f}%",
                f"   🎯 Pump: {signal.pump_probability:.0f}% | ⏱️ ~{time_str}",
                f"   📊 Vol spike: +{signal.volume_spike:.0f}%",
                f"   🐋 Whale: {signal.whale_activity:.0f}%",
                ""
            ])
        
        lines.extend([
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "⚠️ Это не финансовая рекомендация!",
            "🕐 " + datetime.now().strftime("%H:%M %d.%m.%Y")
        ])
        
        return "\n".join(lines)