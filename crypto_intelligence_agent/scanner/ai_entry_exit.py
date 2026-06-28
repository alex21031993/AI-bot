"""
AI Entry & Exit Scanner - Advanced System
AI-точки входа и выхода для торговли
"""
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass
class EntryExitPoint:
    """Точка входа/выхода"""
    type: str  # "ENTRY" or "EXIT"
    direction: str  # "LONG" or "SHORT"
    price: float
    confidence: float  # 0-100
    
    # Уровни
    stop_loss: float = 0
    take_profit_1: float = 0
    take_profit_2: float = 0
    take_profit_3: float = 0
    
    # Метрики риска
    risk_percent: float = 0  # Риск от входа до SL
    reward_percent: float = 0  # Потенциальная награда
    risk_reward_ratio: float = 0
    
    # Сигналы
    signals: List[str] = None
    
    def __post_init__(self):
        if self.signals is None:
            self.signals = []
    
    def get(self, key, default=None):
        return getattr(self, key, default) if hasattr(self, key) else default


@dataclass
class EntryExitAnalysis:
    """Полный анализ входа/выхода"""
    symbol: str
    name: str
    current_price: float
    
    # Текущее состояние
    trend: str = "NEUTRAL"  # BULLISH, BEARISH, NEUTRAL
    trend_strength: float = 0  # 0-100
    
    # Точки
    entry_point: Optional[EntryExitPoint] = None
    exit_point: Optional[EntryExitPoint] = None
    
    # Уровни
    support_levels: List[float] = None
    resistance_levels: List[float] = None
    
    # RSI и другие индикаторы
    rsi: float = 50
    macd_signal: str = "NEUTRAL"
    
    # Сигналы
    signals: List[str] = None
    
    def __post_init__(self):
        if self.support_levels is None:
            self.support_levels = []
        if self.resistance_levels is None:
            self.resistance_levels = []
        if self.signals is None:
            self.signals = []


class AIEntryExitScanner:
    """
    AI-сканер точек входа и выхода
    
    Анализирует:
    - Технические уровни поддержки/сопротивления
    - RSI, MACD, объемы
    - Тренды и паттерны
    - Риск/награда
    """
    
    # Symbol to CoinGecko ID mapping
    SYMBOL_TO_ID = {
        "btc": "bitcoin", "eth": "ethereum", "sol": "solana",
        "doge": "dogecoin", "shib": "shiba-inu", "pepe": "pepe",
        "xrp": "ripple", "ada": "cardano", "dot": "polkadot",
        "avax": "avalanche-2", "matic": "matic-network",
        "link": "chainlink", "uni": "uniswap", "atom": "cosmos",
        "ltc": "litecoin", "bch": "bitcoin-cash", "near": "near",
        "aave": "aave", "sui": "sui", "pump": "pump"
    }
    
    def _get_coin_id(self, token: str) -> str:
        """Конвертируем symbol в coin_id"""
        token_lower = token.lower()
        return self.SYMBOL_TO_ID.get(token_lower, token_lower)

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
    
    async def analyze(self, token_id: str) -> EntryExitAnalysis:
        """Проанализировать точки входа/выхода"""
        try:
            session = await self._get_session()
            
            # Получаем данные рынка
            coin_id = self._get_coin_id(token_id)
            coin_data = await self._fetch_market_data(session, coin_id)
            if not coin_data:
                return self._default_analysis(token_id)
            
            symbol = coin_data.get("symbol", "").upper()
            name = coin_data.get("name", "")
            price = coin_data.get("current_price", 0) or 0
            mcap = coin_data.get("market_cap", 0) or 0
            change_24h = coin_data.get("price_change_percentage_24h", 0) or 0
            
            # Рассчитываем уровни
            support, resistance = self._calculate_levels(price, mcap, coin_data)
            
            # RSI
            rsi = self._calculate_rsi(change_24h, coin_data)
            
            # MACD
            macd = self._calculate_macd(change_24h)
            
            # Trend
            trend, trend_strength = self._determine_trend(change_24h, rsi, macd)
            
            # Entry point
            entry = self._calculate_entry_point(price, support, trend, rsi)
            
            # Exit point
            exit_pt = self._calculate_exit_point(price, resistance, trend, rsi)
            
            # Signals
            signals = self._extract_signals(trend, rsi, macd, change_24h)
            
            return EntryExitAnalysis(
                symbol=symbol,
                name=name,
                current_price=price,
                trend=trend,
                trend_strength=trend_strength,
                entry_point=entry,
                exit_point=exit_pt,
                support_levels=support,
                resistance_levels=resistance,
                rsi=rsi,
                macd_signal=macd,
                signals=signals
            )
            
        except Exception as e:
            logger.error(f"Entry/Exit analysis error: {e}")
            return self._default_analysis(token_id)
    
    async def _fetch_market_data(self, session: aiohttp.ClientSession, token_id: str) -> Optional[Dict]:
        """Получить рыночные данные"""
        try:
            async with session.get(
                f"{self.coingecko_base}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "ids": token_id,
                    "order": "market_cap_desc",
                    "per_page": 1,
                    "sparkline": "true",
                    "price_change_percentage": "1h,24h,7d,30d"
                }
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data[0] if data else None
            return None
        except Exception as e:
            logger.error(f"Fetch market data error: {e}")
            return None
    
    def _calculate_levels(self, price: float, mcap: float, data: Dict) -> Tuple[List[float], List[float]]:
        """Расчет уровней поддержки и сопротивления"""
        change_24h = data.get("price_change_percentage_24h", 0) or 0
        high_24h = data.get("high_24h", 0) or price * 1.02
        low_24h = data.get("low_24h", 0) or price * 0.98
        
        # Процент изменения
        volatility = abs(change_24h) / 100 + 0.01
        
        # Поддержка
        support = [
            low_24h,
            price * (1 - volatility * 1.5),
            price * (1 - volatility * 3)
        ]
        
        # Сопротивление
        resistance = [
            high_24h,
            price * (1 + volatility * 1.5),
            price * (1 + volatility * 3)
        ]
        
        return sorted(support, reverse=True), sorted(resistance)
    
    def _calculate_rsi(self, change_24h: float, data: Dict) -> float:
        """Расчет RSI (упрощенный)"""
        # Упрощенный RSI на основе изменения цены
        base_rsi = 50 + (change_24h * 5)
        return max(0, min(100, base_rsi))
    
    def _calculate_macd(self, change_24h: float) -> str:
        """Расчет MACD сигнала"""
        if change_24h > 3: return "BULLISH"
        elif change_24h < -3: return "BEARISH"
        else: return "NEUTRAL"
    
    def _determine_trend(self, change_24h: float, rsi: float, macd: str) -> Tuple[str, float]:
        """Определение тренда"""
        bullish_signals = 0
        total_signals = 3
        
        if change_24h > 2: bullish_signals += 1
        elif change_24h < -2: bullish_signals -= 1
        
        if rsi > 55: bullish_signals += 1
        elif rsi < 45: bullish_signals -= 1
        
        if macd == "BULLISH": bullish_signals += 1
        elif macd == "BEARISH": bullish_signals -= 1
        
        strength = abs(bullish_signals) / total_signals * 100
        
        if bullish_signals >= 2: return "BULLISH", strength
        elif bullish_signals <= -2: return "BEARISH", strength
        else: return "NEUTRAL", strength
    
    def _calculate_entry_point(self, price: float, support: List[float], 
                               trend: str, rsi: float) -> EntryExitPoint:
        """Расчет точки входа"""
        if trend == "BULLISH":
            # Вход на откате к поддержке
            entry_price = support[0] if support else price * 0.98
            stop_loss = support[-1] if len(support) > 1 else price * 0.95
            tp1 = price * 1.03
            tp2 = price * 1.05
            tp3 = price * 1.08
            direction = "LONG"
        elif trend == "BEARISH":
            # Вход на росте к сопротивлению
            entry_price = price * 1.02
            stop_loss = price * 1.05
            tp1 = price * 0.97
            tp2 = price * 0.95
            tp3 = price * 0.92
            direction = "SHORT"
        else:
            # Нейтральный - ждем
            entry_price = price
            stop_loss = price * 0.97
            tp1 = price * 1.02
            tp2 = price * 1.03
            tp3 = price * 1.05
            direction = "LONG"
        
        risk = abs(entry_price - stop_loss) / entry_price * 100
        reward = abs(tp3 - entry_price) / entry_price * 100
        rr_ratio = reward / risk if risk > 0 else 0
        
        # Confidence
        confidence = 50 + rsi * 0.4 if 40 < rsi < 60 else 40
        
        signals = []
        if risk < 2: signals.append("✅ Низкий риск")
        if rr_ratio > 2: signals.append("📊 Хороший R/R")
        if trend == "BULLISH": signals.append("🟢 Бычий тренд")
        
        return EntryExitPoint(
            type="ENTRY",
            direction=direction,
            price=entry_price,
            confidence=confidence,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            take_profit_3=tp3,
            risk_percent=risk,
            reward_percent=reward,
            risk_reward_ratio=rr_ratio,
            signals=signals
        )
    
    def _calculate_exit_point(self, price: float, resistance: List[float],
                              trend: str, rsi: float) -> EntryExitPoint:
        """Расчет точки выхода"""
        if trend == "BULLISH":
            exit_price = resistance[0] if resistance else price * 1.03
            stop_loss = price * 0.97
        else:
            exit_price = price * 0.97
            stop_loss = price * 1.03
        
        risk = abs(exit_price - stop_loss) / exit_price * 100
        reward = abs(price - exit_price) / exit_price * 100
        
        return EntryExitPoint(
            type="EXIT",
            direction="LONG" if trend == "BULLISH" else "SHORT",
            price=exit_price,
            confidence=50,
            stop_loss=stop_loss,
            risk_percent=risk,
            reward_percent=reward,
            signals=["📊 Фиксация прибыли"]
        )
    
    def _extract_signals(self, trend: str, rsi: float, macd: str, change_24h: float) -> List[str]:
        """Извлечение сигналов"""
        signals = []
        
        if trend == "BULLISH": signals.append("🟢 Бычий тренд")
        elif trend == "BEARISH": signals.append("🔴 Медвежий тренд")
        else: signals.append("⚪ Нейтральный тренд")
        
        if rsi > 70: signals.append("⚠️ RSI перекуплен")
        elif rsi < 30: signals.append("⚠️ RSI перепродан")
        
        if macd == "BULLISH": signals.append("📈 MACD бычий")
        elif macd == "BEARISH": signals.append("📉 MACD медвежий")
        
        if change_24h > 5: signals.append("🚀 Сильный рост")
        elif change_24h < -5: signals.append("📉 Сильное падение")
        
        return signals
    
    def _default_analysis(self, token_id: str) -> EntryExitAnalysis:
        """Анализ по умолчанию"""
        return EntryExitAnalysis(
            symbol=token_id.upper(),
            name=token_id,
            current_price=0,
            signals=["⚠️ Недостаточно данных"]
        )
    
    def format_report(self, analysis: EntryExitAnalysis) -> str:
        """Форматирование отчета"""
        trend_emoji = {"BULLISH": "🟢", "BEARISH": "🔴", "NEUTRAL": "⚪"}
        
        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "🧠 *AI ENTRY & EXIT*",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            f"📊 *{analysis.symbol}* ({analysis.name})",
            f"💰 Текущая цена: ${analysis.current_price:.6f}",
            "",
            f"{trend_emoji.get(analysis.trend, '⚪')} Тренд: *{analysis.trend}* ({analysis.trend_strength:.0f}%)",
            f"📊 RSI: {analysis.rsi:.1f}",
            f"📈 MACD: {analysis.macd_signal}",
            ""
        ]
        
        # Уровни
        if analysis.support_levels:
            lines.append("📍 *Уровни поддержки:*")
            for i, lvl in enumerate(analysis.support_levels[:3], 1):
                lines.append(f"   S{i}: ${lvl:.6f}")
            lines.append("")
        
        if analysis.resistance_levels:
            lines.append("📍 *Уровни сопротивления:*")
            for i, lvl in enumerate(analysis.resistance_levels[:3], 1):
                lines.append(f"   R{i}: ${lvl:.6f}")
            lines.append("")
        
        # Entry point
        if analysis.entry_point:
            ep = analysis.entry_point
            lines.extend([
                "━━━━━━━━━━━━━ *ТОЧКА ВХОДА* ━━━━━━━━━━━",
                f"💰 Цена: ${ep.price:.6f}",
                f"📊 Направление: *{ep.direction}*",
                f"🎯 Confidence: {ep.confidence:.0f}%",
                "",
                f"🛡️ Stop Loss: ${ep.stop_loss:.6f} ({ep.risk_percent:.1f}%)",
                f"🎯 TP1: ${ep.take_profit_1:.6f}",
                f"🎯 TP2: ${ep.take_profit_2:.6f}",
                f"🎯 TP3: ${ep.take_profit_3:.6f} ({ep.reward_percent:.1f}%)",
                f"📊 R/R: {ep.risk_reward_ratio:.1f}",
                ""
            ])
        
        # Signals
        if analysis.signals:
            lines.extend(["━━━━━━━━━━━━━ *СИГНАЛЫ* ━━━━━━━━━━━", ""])
            for signal in analysis.signals:
                lines.append(f"   {signal}")
            lines.append("")
        
        lines.extend([
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "⚠️ Это не финансовая рекомендация!",
            "🕐 " + datetime.now().strftime("%H:%M %d.%m.%Y")
        ])
        
        return "\n".join(lines)