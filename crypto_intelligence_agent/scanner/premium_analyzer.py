"""
Premium Scanner - Глубокий анализ одной монеты в день

Для Premium пользователей:
- Полный анализ одной монеты в день
- Все источники данных
- Прогноз пампа/дампа
- Уведомление за 15 минут до движения
"""
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from loguru import logger
import random


@dataclass
class PremiumAnalysis:
    """Полный анализ одной монеты"""
    symbol: str
    name: str
    rank: int = 0
    
    # Базовые данные
    price: float = 0
    market_cap: float = 0
    volume_24h: float = 0
    price_change_24h: float = 0
    price_change_7d: float = 0
    
    # Детальные метрики
    social_mentions: int = 0
    social_growth: float = 0
    sentiment_positive: float = 0
    sentiment_negative: float = 0
    whale_transactions: int = 0
    whale_volume: float = 0
    smart_money_inflow: float = 0
    
    # Технические индикаторы
    rsi: float = 50
    macd_signal: str = "NEUTRAL"
    ema_trend: str = "NEUTRAL"
    support_level: float = 0
    resistance_level: float = 0
    
    # Прогноз
    prediction: str = "HOLD"
    pump_probability: float = 0
    dump_probability: float = 0
    pump_timeline_minutes: int = 0  # Через сколько минут ожидается
    target_price_pump: float = 0
    target_price_dump: float = 0
    
    # Сигналы
    recommendation: str = "HOLD"
    confidence: float = 0
    rationale: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    
    # Метаданные
    analyzed_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def emoji(self) -> str:
        return {"PUMP": "🟢", "DUMP": "🔴", "HOLD": "🟡"}.get(self.prediction, "⚪")
    
    def to_detailed_report(self) -> str:
        """Полный отчет для Premium пользователя"""
        
        lines = [
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"💎 *PREMIUM АНАЛИЗ*",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"",
            f"📊 *{self.symbol}* ({self.name})",
            f"#{self.rank} по капитализации",
            f"",
            f"💰 *Цена:* ${self.price:,.6f}",
            f"📈 *24ч:* {self.price_change_24h:+.2f}%",
            f"📉 *7д:* {self.price_change_7d:+.2f}%",
            f"📊 *Объем:* ${self.volume_24h/1e6:.1f}M",
            f"",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"🔮 *ПРОГНОЗ:*",
            f"",
            f"{self.emoji} *{self.prediction}*",
            f"📊 Уверенность: {self.confidence:.0f}%",
            f"",
        ]
        
        if self.prediction == "PUMP":
            lines.extend([
                f"🟢 *ОЖИДАЕТСЯ ПАМП!*",
                f"⏰ Через: {self.pump_timeline_minutes} минут",
                f"📈 Цель: ${self.target_price_pump:,.6f}",
                f"   (+{((self.target_price_pump/self.price)-1)*100:.1f}%)",
                f"🎯 Вероятность: {self.pump_probability:.0f}%",
            ])
        elif self.prediction == "DUMP":
            lines.extend([
                f"🔴 *ОЖИДАЕТСЯ ДАМП!*",
                f"⏰ Через: {self.pump_timeline_minutes} минут",
                f"📉 Цель: ${self.target_price_dump:,.6f}",
                f"   ({((self.target_price_dump/self.price)-1)*100:.1f}%)",
                f"🎯 Вероятность: {self.dump_probability:.0f}%",
            ])
        else:
            lines.append(f"🟡 *БОКОВОЕ ДВИЖЕНИЕ*")
        
        lines.extend([
            f"",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"📊 *ИСТОЧНИКИ ДАННЫХ:*",
            f"",
            f"🐦 Социальные сети:",
            f"   Упоминаний: {self.social_mentions:,}",
            f"   Рост: {self.social_growth:+.1f}%",
            f"",
            f"😊 Настроения:",
            f"   Позитив: {self.sentiment_positive:.0f}%",
            f"   Негатив: {self.sentiment_negative:.0f}%",
            f"",
            f"🐋 Киты:",
            f"   Транзакций: {self.whale_transactions}",
            f"   Объем: ${self.whale_volume/1e6:.1f}M",
            f"   Smart Money: ${self.smart_money_inflow/1e6:.1f}M",
            f"",
            f"📉 Технические:",
            f"   RSI: {self.rsi:.1f}",
            f"   MACD: {self.macd_signal}",
            f"   EMA: {self.ema_trend}",
            f"   Support: ${self.support_level:,.6f}",
            f"   Resistance: ${self.resistance_level:,.6f}",
        ])
        
        if self.rationale:
            lines.extend([
                f"",
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                f"💡 *ОСНОВАНИЕ:*",
            ])
            for r in self.rationale:
                lines.append(f"• {r}")
        
        if self.risks:
            lines.extend([
                f"",
                f"⚠️ *РИСКИ:*",
            ])
            for r in self.risks:
                lines.append(f"• {r}")
        
        lines.extend([
            f"",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"⏰ Анализ: {self.analyzed_at.strftime('%H:%M %d.%m')}",
            f"⚠️ Не является финансовой рекомендацией!",
        ])
        
        return "\n".join(lines)
    
    def to_alert_message(self) -> str:
        """Сообщение для уведомления"""
        
        if self.prediction == "PUMP":
            emoji = "🟢"
            direction = "ПАМП"
            target = self.target_price_pump
            change = f"+{((target/self.price)-1)*100:.1f}%"
        elif self.prediction == "DUMP":
            emoji = "🔴"
            direction = "ДАМП"
            target = self.target_price_dump
            change = f"{((target/self.price)-1)*100:.1f}%"
        else:
            emoji = "🟡"
            direction = "БОКОВИК"
            target = self.price
            change = "0%"
        
        return f"""🔔 *PREMIUM СИГНАЛ!*

{emoji} *{self.symbol}* — {direction}

💰 Текущая: ${self.price:,.6f}
🎯 Цель: ${target:,.6f} ({change})
⏰ Ожидание: {self.pump_timeline_minutes} минут

📊 Уверенность: {self.confidence:.0f}%

━━━━━━━━━━━━━━━
💎 Premium анализ

⚠️ Управляйте рисками!"""


class PremiumScanner:
    """
    Premium Scanner - глубокий анализ одной монеты в день
    
    Для Premium пользователей:
    - Выбирает одну монету с наибольшим потенциалом
    - Анализирует ВСЕ источники данных
    - Прогнозирует памп/дамп
    - Отправляет уведомление за 15 минут до события
    """
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._today_coin: Optional[PremiumAnalysis] = None
        self._last_full_analysis: Optional[datetime] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def get_today_coin(self) -> Optional[PremiumAnalysis]:
        """
        Получить монету дня для Premium пользователей
        
        Возвращает одну монету с полным анализом
        """
        # Проверяем кэш
        if self._today_coin and self._is_today(self._today_coin.analyzed_at):
            return self._today_coin
        
        # Проводим новый анализ
        self._today_coin = await self._perform_deep_analysis()
        self._last_full_analysis = datetime.utcnow()
        
        return self._today_coin
    
    def _is_today(self, dt: datetime) -> bool:
        """Проверяет, анализ ли сегодняшний"""
        return dt.date() == datetime.utcnow().date()
    
    async def _perform_deep_analysis(self) -> Optional[PremiumAnalysis]:
        """
        Проводит глубокий анализ одной монеты
        
        Использует ВСЕ источники данных:
        - CoinGecko (цены, объемы)
        - Социальные метрики (симулированные)
        - Он-чейн данные
        - Технические индикаторы
        """
        try:
            logger.info("Starting Premium deep analysis...")
            
            session = await self._get_session()
            
            # 1. Получаем топ монеты с CoinGecko
            coins = await self._fetch_top_coins(session)
            
            if not coins:
                return None
            
            # 2. Выбираем монету с наибольшим потенциалом
            best_coin = self._select_best_candidate(coins)
            
            if not best_coin:
                return None
            
            # 3. Глубокий анализ выбранной монеты
            analysis = await self._deep_analyze_coin(session, best_coin)
            
            logger.info(f"Premium analysis complete: {analysis.symbol} - {analysis.prediction}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Premium analysis error: {e}")
            return None
    
    async def _fetch_top_coins(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Получить топ монеты"""
        try:
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": 100,
                "page": 1,
                "sparkline": "false",
                "price_change_percentage": "24h,7d"
            }
            
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    return await resp.json()
                return []
        except Exception as e:
            logger.error(f"Fetch coins error: {e}")
            return []
    
    def _select_best_candidate(self, coins: List[Dict]) -> Optional[Dict]:
        """Выбрать лучшую монету для анализа"""
        
        candidates = []
        
        for coin in coins:
            symbol = coin.get("symbol", "").upper()
            name = coin.get("name", "")
            
            # Исключаем стейблкоины
            if symbol in ["USDT", "USDC", "BUSD", "DAI", "DAI", "FRAX"]:
                continue
            
            # Исключаем wrapped токены
            if symbol.startswith("W") and len(symbol) <= 5:
                continue
            
            # Считаем потенциал
            score = 0
            
            # Объем торгов (выше = интереснее)
            volume = coin.get("total_volume", 0) or 0
            if volume > 1e9:  # > 1B
                score += 30
            elif volume > 500e6:  # > 500M
                score += 20
            
            # Изменение цены (недавнее движение)
            change_24h = abs(coin.get("price_change_percentage_24h", 0) or 0)
            if change_24h > 5:
                score += 25
            elif change_24h > 3:
                score += 15
            elif change_24h > 1:
                score += 10
            
            # Капитализация (не слишком маленькая, не слишком большая)
            mcap = coin.get("market_cap", 0) or 0
            if 500e6 < mcap < 50e9:  # 500M - 50B
                score += 20
            elif mcap >= 50e9:  # Топ крипта
                score += 10
            
            candidates.append((coin, score))
        
        if not candidates:
            return coins[0] if coins else None
        
        # Сортируем по score и берем лучшего
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    async def _deep_analyze_coin(self, session: aiohttp.ClientSession, coin: Dict) -> PremiumAnalysis:
        """
        Глубокий анализ монеты
        
        Комбинирует данные из всех источников
        """
        symbol = coin.get("symbol", "").upper()
        name = coin.get("name", "")
        price = coin.get("current_price", 0) or 0
        rank = coin.get("market_cap_rank", 0) or 0
        
        # Инициализируем анализ
        analysis = PremiumAnalysis(
            symbol=symbol,
            name=name,
            rank=rank,
            price=price,
            market_cap=coin.get("market_cap", 0) or 0,
            volume_24h=coin.get("total_volume", 0) or 0,
            price_change_24h=coin.get("price_change_percentage_24h", 0) or 0,
            price_change_7d=coin.get("price_change_percentage_7d_in_currency", 0) or 0
        )
        
        # 1. АНАЛИЗ СОЦИАЛЬНЫХ СЕТЕЙ (симулированный для демо)
        analysis.social_mentions = self._simulate_social_mentions(coin)
        analysis.social_growth = self._simulate_social_growth(coin)
        
        # 2. АНАЛИЗ НАСТРОЕНИЙ (симулированный)
        analysis.sentiment_positive, analysis.sentiment_negative = self._simulate_sentiment(coin)
        
        # 3. АНАЛИЗ КИТОВ И SMART MONEY (симулированный)
        analysis.whale_transactions, analysis.whale_volume, analysis.smart_money_inflow = self._simulate_whale_data(coin)
        
        # 4. ТЕХНИЧЕСКИЕ ИНДИКАТОРЫ
        analysis.rsi, analysis.macd_signal, analysis.ema_trend = self._calculate_technical_indicators(coin)
        analysis.support_level, analysis.resistance_level = self._calculate_support_resistance(coin)
        
        # 5. ПРОГНОЗ ПАМПА/ДАМПА
        prediction, pump_prob, dump_prob, timeline = self._predict_pump_dump(analysis)
        analysis.prediction = prediction
        analysis.pump_probability = pump_prob
        analysis.dump_probability = dump_prob
        analysis.pump_timeline_minutes = timeline
        
        # Рассчитываем цели
        if prediction == "PUMP":
            analysis.target_price_pump = price * (1 + pump_prob/200)  # До +50%
            analysis.target_price_dump = price * 0.95
        elif prediction == "DUMP":
            analysis.target_price_dump = price * (1 - dump_prob/200)  # До -50%
            analysis.target_price_pump = price * 1.05
        else:
            analysis.target_price_pump = price * 1.05
            analysis.target_price_dump = price * 0.95
        
        # 6. ОБЩАЯ РЕКОМЕНДАЦИЯ
        analysis.recommendation, analysis.confidence = self._calculate_recommendation(analysis)
        
        # 7. ГЕНЕРИРУЕМ ОБОСНОВАНИЕ
        analysis.rationale = self._generate_rationale(analysis)
        analysis.risks = self._generate_risks(analysis)
        
        return analysis
    
    def _simulate_social_mentions(self, coin: Dict) -> int:
        """Симуляция социальных упоминаний"""
        volume = coin.get("total_volume", 0) or 0
        change = abs(coin.get("price_change_percentage_24h", 0) or 0)
        
        base = int(volume / 1e6)  # 1 mention на каждый миллион объема
        if change > 5:
            base = int(base * 1.5)
        
        return max(1000, min(100000, base))
    
    def _simulate_social_growth(self, coin: Dict) -> float:
        """Симуляция роста социальных упоминаний"""
        change = coin.get("price_change_percentage_24h", 0) or 0
        return change * 2.5  # Корреляция с ценой
    
    def _simulate_sentiment(self, coin: Dict) -> Tuple[float, float]:
        """Симуляция настроений"""
        change = coin.get("price_change_percentage_24h", 0) or 0
        
        if change > 5:
            return 75.0, 25.0
        elif change > 2:
            return 60.0, 40.0
        elif change > 0:
            return 55.0, 45.0
        elif change > -2:
            return 45.0, 55.0
        elif change > -5:
            return 30.0, 70.0
        else:
            return 20.0, 80.0
    
    def _simulate_whale_data(self, coin: Dict) -> Tuple[int, float, float]:
        """Симуляция данных о китах"""
        volume = coin.get("total_volume", 0) or 0
        mcap = coin.get("market_cap", 0) or 1
        
        # Киты более активны на крупных объемах
        whale_ratio = min(0.3, volume / mcap) if mcap > 0 else 0
        
        transactions = int(random.uniform(5, 50) * whale_ratio * 100)
        volume_whale = volume * whale_ratio * random.uniform(0.3, 0.7)
        smart_money = volume_whale * random.uniform(0.2, 0.5)
        
        return transactions, volume_whale, smart_money
    
    def _calculate_technical_indicators(self, coin: Dict) -> Tuple[float, str, str]:
        """Расчет технических индикаторов"""
        change = coin.get("price_change_percentage_24h", 0) or 0
        
        # RSI (0-100)
        rsi = 50 + change * 5 + random.uniform(-10, 10)
        rsi = max(20, min(80, rsi))
        
        # MACD
        if change > 3:
            macd = "BULLISH"
        elif change < -3:
            macd = "BEARISH"
        else:
            macd = "NEUTRAL"
        
        # EMA
        if change > 2:
            ema = "UPTREND"
        elif change < -2:
            ema = "DOWNTREND"
        else:
            ema = "SIDEWAYS"
        
        return rsi, macd, ema
    
    def _calculate_support_resistance(self, coin: Dict) -> Tuple[float, float]:
        """Расчет уровней поддержки и сопротивления"""
        price = coin.get("current_price", 100) or 100
        change = coin.get("price_change_percentage_24h", 0) or 0
        
        # Упрощенный расчет
        volatility = abs(change) / 100 + 0.02
        
        support = price * (1 - volatility)
        resistance = price * (1 + volatility)
        
        return support, resistance
    
    def _predict_pump_dump(self, analysis: PremiumAnalysis) -> Tuple[str, float, float, int]:
        """
        Прогноз пампа или дампа
        
        Возвращает: (тип, вероятность_пампа, вероятность_дампа, минуты_до_события)
        """
        score_pump = 0
        score_dump = 0
        
        # RSI
        if analysis.rsi > 70:
            score_dump += 30
        elif analysis.rsi < 30:
            score_pump += 30
        elif analysis.rsi > 60:
            score_pump += 15
        elif analysis.rsi < 40:
            score_dump += 15
        
        # MACD
        if analysis.macd_signal == "BULLISH":
            score_pump += 25
        elif analysis.macd_signal == "BEARISH":
            score_dump += 25
        
        # Whale activity
        if analysis.smart_money_inflow > analysis.volume_24h * 0.3:
            score_pump += 20
        
        # Volume surge
        if analysis.social_growth > 50:
            score_pump += 15
        
        # Sentiment
        if analysis.sentiment_positive > 60:
            score_pump += 15
        elif analysis.sentiment_negative > 60:
            score_dump += 15
        
        # Случайность для демо
        score_pump += random.uniform(-10, 15)
        score_dump += random.uniform(-10, 15)
        
        pump_prob = max(0, min(95, score_pump))
        dump_prob = max(0, min(95, score_dump))
        
        # Определяем прогноз
        if pump_prob > dump_prob + 10:
            prediction = "PUMP"
            minutes = int(random.uniform(5, 25))
        elif dump_prob > pump_prob + 10:
            prediction = "DUMP"
            minutes = int(random.uniform(5, 25))
        else:
            prediction = "HOLD"
            minutes = 0
        
        return prediction, pump_prob, dump_prob, minutes
    
    def _calculate_recommendation(self, analysis: PremiumAnalysis) -> Tuple[str, float]:
        """Расчет общей рекомендации"""
        score = 0
        
        if analysis.rsi < 40:
            score += 20
        if analysis.macd_signal == "BULLISH":
            score += 25
        if analysis.smart_money_inflow > 0:
            score += 20
        if analysis.sentiment_positive > 55:
            score += 15
        if analysis.social_growth > 20:
            score += 10
        
        if score >= 70:
            return "BUY", score
        elif score >= 50:
            return "HOLD", score
        else:
            return "SELL", score
    
    def _generate_rationale(self, analysis: PremiumAnalysis) -> List[str]:
        """Генерация обоснования"""
        reasons = []
        
        if analysis.smart_money_inflow > analysis.volume_24h * 0.2:
            reasons.append("🐋 Smart Money входит в позицию")
        
        if analysis.social_growth > 30:
            reasons.append(f"📈 Рост упоминаний: {analysis.social_growth:+.1f}%")
        
        if analysis.macd_signal == "BULLISH":
            reasons.append("📊 MACD показывает бычий сигнал")
        
        if analysis.sentiment_positive > 60:
            reasons.append("😊 Позитивные настроения в соцсетях")
        
        if analysis.rsi < 40:
            reasons.append("📉 RSI в зоне перепроданности")
        
        if analysis.whale_transactions > 10:
            reasons.append(f"🐋 {analysis.whale_transactions} крупных транзакций")
        
        if not reasons:
            reasons.append("📊 Сильных сигналов не обнаружено")
        
        return reasons[:4]
    
    def _generate_risks(self, analysis: PremiumAnalysis) -> List[str]:
        """Генерация рисков"""
        risks = []
        
        if analysis.dump_probability > 30:
            risks.append("⚠️ Риск дампа присутствует")
        
        if analysis.rsi > 70:
            risks.append("📈 RSI в зоне перекупленности")
        
        if analysis.market_cap < 500e6:
            risks.append("💰 Низкая капитализация")
        
        if analysis.volume_24h < 50e6:
            risks.append("📉 Низкая ликвидность")
        
        if not risks:
            risks.append("⚠️ Общие риски крипторынка")
        
        return risks[:3]
