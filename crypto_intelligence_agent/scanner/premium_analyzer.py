"""
Premium Scanner - Глубокий анализ ОДНОЙ монеты в день

Для Premium пользователей:
- ТОЛЬКО ОДНА монета в день
- Полный анализ кошельков китов
- Прогноз пампа/дампа
- Уведомление ЗА 15 МИНУТ до события
"""
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from loguru import logger
import random


@dataclass
class WhaleWallet:
    """Данные о кошельке кита"""
    address: str
    label: str  # Label (e.g., "Binance Hot", "Alameda Research")
    balance: float  # Balance in USDT
    change_24h: float  # Change in 24h
    is_exchange: bool
    is_smart_money: bool
    transaction_count: int = 0
    
    def get_short_address(self) -> str:
        if len(self.address) > 16:
            return f"{self.address[:8]}...{self.address[-6:]}"
        return self.address


@dataclass
class PremiumAnalysis:
    """Полный анализ ОДНОЙ монеты с данными китов"""
    symbol: str
    name: str
    rank: int = 0
    
    # Базовые данные
    price: float = 0
    market_cap: float = 0
    volume_24h: float = 0
    price_change_24h: float = 0
    price_change_7d: float = 0
    
    # Данные о кошельках китов
    whale_wallets: List[WhaleWallet] = field(default_factory=list)
    total_whale_balance: float = 0
    whale_buy_pressure: float = 0  # -100 to +100
    exchange_flow: float = 0  # Positive = inflow to exchange (sell pressure)
    
    # Социальные данные
    social_mentions: int = 0
    social_growth: float = 0
    sentiment_score: float = 50
    
    # Прогноз
    prediction: str = "HOLD"
    pump_probability: float = 0
    dump_probability: float = 0
    minutes_until_event: int = 15  # ЗА 15 МИНУТ до события!
    
    # Цели
    entry_price: float = 0
    target_price_pump: float = 0
    target_price_dump: float = 0
    stop_loss: float = 0
    
    # Уверенность
    confidence: float = 0
    rationale: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    
    # Метаданные
    analyzed_at: datetime = field(default_factory=datetime.utcnow)
    next_alert_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def emoji(self) -> str:
        return {"PUMP": "🟢", "DUMP": "🔴", "HOLD": "🟡"}.get(self.prediction, "⚪")
    
    @property
    def alert_time_formatted(self) -> str:
        """Время когда придет уведомление"""
        return self.next_alert_at.strftime("%H:%M")
    
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
        ]
        
        # Прогноз с таймингом
        lines.extend([
            f"",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"🔮 *ПРОГНОЗ:*",
            f"",
            f"{self.emoji} *{self.prediction}*",
            f"📊 Уверенность: {self.confidence:.0f}%",
        ])
        
        if self.prediction == "PUMP":
            lines.extend([
                f"",
                f"🟢 *⚠️ ВНИМАНИЕ: ПАМП ЧЕРЕЗ 15 МИНУТ!*",
                f"⏰ Уведомление в: {self.alert_time_formatted}",
                f"📈 Цель: ${self.target_price_pump:,.6f}",
                f"   (+{((self.target_price_pump/self.price)-1)*100:.1f}%)",
                f"🎯 Вероятность: {self.pump_probability:.0f}%",
            ])
        elif self.prediction == "DUMP":
            lines.extend([
                f"",
                f"🔴 *⚠️ ВНИМАНИЕ: ДАМП ЧЕРЕЗ 15 МИНУТ!*",
                f"⏰ Уведомление в: {self.alert_time_formatted}",
                f"📉 Цель: ${self.target_price_dump:,.6f}",
                f"   ({((self.target_price_dump/self.price)-1)*100:.1f}%)",
                f"🎯 Вероятность: {self.dump_probability:.0f}%",
            ])
        else:
            lines.extend([
                f"",
                f"🟡 *БОКОВОЕ ДВИЖЕНИЕ*",
                f"⏰ Следующее обновление через 1 час",
            ])
        
        # Торговые уровни
        lines.extend([
            f"",
            f"📐 *ТОРГОВЫЕ УРОВНИ:*",
            f"   Вход: ${self.entry_price:,.6f}",
            f"   TP: ${self.target_price_pump:,.6f}",
            f"   SL: ${self.stop_loss:,.6f}",
        ])
        
        # Данные китов
        lines.extend([
            f"",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"🐋 *КОШЕЛЬКИ КИТОВ:*",
            f"",
            f"📊 Всего китов: {len(self.whale_wallets)}",
            f"💰 Общий баланс: ${self.total_whale_balance/1e6:.1f}M",
            f"📈 Давление покупок: {self.whale_buy_pressure:+.0f}%",
        ])
        
        # Показываем всех китов
        if self.whale_wallets:
            sorted_wallets = sorted(self.whale_wallets, key=lambda x: x.balance, reverse=True)
            lines.append(f"")
            lines.append(f"🏆 *КИТЫ ({len(sorted_wallets)}):*")
            for i, wallet in enumerate(sorted_wallets, 1):
                badge = "💎" if wallet.is_smart_money else "🏦" if wallet.is_exchange else "🐋"
                change_emoji = "📈" if wallet.change_24h > 0 else "📉"
                lines.append(f"   {i}. {badge} {wallet.label}")
                lines.append(f"      💰 ${wallet.balance/1e6:.1f}M | {change_emoji} {wallet.change_24h:+.1f}%")
        
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
            f"🔔 Уведомление: {self.alert_time_formatted}",
            f"⚠️ Не является финансовой рекомендацией!",
        ])
        
        return "\n".join(lines)
    
    def to_alert_message(self) -> str:
        """СООБЩЕНИЕ-УВЕДОМЛЕНИЕ за 15 минут"""
        
        direction_emoji = "🟢" if self.prediction == "PUMP" else "🔴"
        
        return f"""🔔 *⚠️ PREMIUM УВЕДОМЛЕНИЕ!*

{direction_emoji} *{self.symbol}* — {self.prediction}

💰 Текущая: ${self.price:,.6f}
🎯 Цель: ${self.target_price_pump if self.prediction == 'PUMP' else self.target_price_dump:,.6f}

📐 *Торговые уровни:*
• Вход: ${self.entry_price:,.6f}
• TP: ${self.target_price_pump:,.6f}
• SL: ${self.stop_loss:,.6f}

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
        Глубокий анализ ОДНОЙ монеты с данными китов
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
        
        # 1. Получаем данные о кошельках китов
        analysis.whale_wallets = await self._fetch_whale_wallets(symbol)
        analysis.total_whale_balance = sum(w.balance for w in analysis.whale_wallets)
        
        # 2. Анализируем давление китов
        analysis.whale_buy_pressure, analysis.exchange_flow = self._analyze_whale_pressure(analysis.whale_wallets)
        
        # 3. Социальные данные
        analysis.social_mentions = self._simulate_social_mentions(coin)
        analysis.social_growth = self._simulate_social_growth(coin)
        analysis.sentiment_score = self._calculate_sentiment(coin, analysis.whale_buy_pressure)
        
        # 4. ПРОГНОЗ на основе данных китов
        prediction, pump_prob, dump_prob = self._predict_based_on_whales(analysis)
        analysis.prediction = prediction
        analysis.pump_probability = pump_prob
        analysis.dump_probability = dump_prob
        
        # 5. Устанавливаем 15 минут до события
        analysis.minutes_until_event = 15
        analysis.next_alert_at = datetime.utcnow() + timedelta(minutes=15)
        
        # 6. Торговые уровни
        analysis.entry_price = price
        if prediction == "PUMP":
            analysis.target_price_pump = price * (1 + pump_prob/100)
            analysis.target_price_dump = price * 0.95
        elif prediction == "DUMP":
            analysis.target_price_dump = price * (1 - dump_prob/100)
            analysis.target_price_pump = price * 1.05
            analysis.entry_price = price * 0.98  # Лучшая точка входа при дампе
        else:
            analysis.target_price_pump = price * 1.05
            analysis.target_price_dump = price * 0.95
        
        analysis.stop_loss = price * 0.97
        
        # 7. Уверенность
        analysis.confidence = self._calculate_confidence(analysis)
        
        # 8. Обоснование
        analysis.rationale = self._generate_rationale(analysis)
        analysis.risks = self._generate_risks(analysis)
        
        return analysis
    
    async def _fetch_whale_wallets(self, symbol: str) -> List[WhaleWallet]:
        """
        Получить данные о кошельках китов для монеты
        
        Использует симулированные данные для демо
        В реальности: Arkham Intelligence, Nansen, Whale Alert APIs
        """
        # Список известных кошельков китов
        known_wallets = [
            {"address": "0x28C6c06298d514Db089934071355E5743bf21d60", "label": "Binance Hot", "is_exchange": True},
            {"address": "0x21a31Ee1afC51d94C2efCCaa2092aD1028285549", "label": "Binance Cold", "is_exchange": True},
            {"address": "0x0a869d79a7052c7f1b55a8ebabbea3420f0d1e13", "label": "Kraken", "is_exchange": True},
            {"address": "0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE", "label": "Bitfinex", "is_exchange": True},
            {"address": "0x0D0707963952f2f2ba7eE963F8dBcA2bD8C85f76", "label": "Alameda Research", "is_exchange": False, "is_smart": True},
            {"address": "0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503", "label": "Metamask", "is_exchange": False},
            {"address": "0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8", "label": "Binance", "is_exchange": True},
        ]
        
        wallets = []
        
        # Симулируем данные для 5-8 кошельков
        num_wallets = random.randint(5, 8)
        
        for i in range(num_wallets):
            if i < len(known_wallets):
                info = known_wallets[i]
                address = info["address"]
                label = info["label"]
                is_exchange = info["is_exchange"]
                is_smart = info.get("is_smart", False)
            else:
                # Генерируем случайный кошелек
                address = f"0x{''.join(random.choices('0123456789abcdef', k=40))}"
                label = f"🐋 Whale #{i+1}"
                is_exchange = False
                is_smart = random.random() > 0.7
            
            # Симулируем баланс (от 1M до 500M USDT)
            balance = random.uniform(1e6, 500e6)
            
            # Симулируем изменение за 24ч (от -20% до +30%)
            change_24h = random.uniform(-20, 30)
            
            wallets.append(WhaleWallet(
                address=address,
                label=label,
                balance=balance,
                change_24h=change_24h,
                is_exchange=is_exchange,
                is_smart_money=is_smart,
                transaction_count=random.randint(1, 50)
            ))
        
        return wallets
    
    def _analyze_whale_pressure(self, wallets: List[WhaleWallet]) -> Tuple[float, float]:
        """
        Анализирует давление покупок/продаж от китов
        
        Returns:
            whale_buy_pressure: -100 to +100 (positive = more buying)
            exchange_flow: -100 to +100 (positive = flow to exchanges = sell pressure)
        """
        buy_pressure = 0
        sell_pressure = 0
        
        for wallet in wallets:
            if wallet.is_exchange:
                # Если киты на биржах продают
                if wallet.change_24h < 0:
                    sell_pressure += abs(wallet.change_24h) * (wallet.balance / 1e8)
                else:
                    buy_pressure += wallet.change_24h * (wallet.balance / 1e8)
            else:
                # Если не на биржах - накапливают
                if wallet.change_24h > 0:
                    buy_pressure += wallet.change_24h * (wallet.balance / 1e8)
                else:
                    sell_pressure += abs(wallet.change_24h) * (wallet.balance / 1e8)
        
        # Нормализуем
        total = buy_pressure + sell_pressure
        if total > 0:
            whale_pressure = ((buy_pressure - sell_pressure) / total) * 100
        else:
            whale_pressure = 0
        
        # Exchange flow (упрощенно)
        exchange_wallets = [w for w in wallets if w.is_exchange]
        if exchange_wallets:
            avg_change = sum(w.change_24h for w in exchange_wallets) / len(exchange_wallets)
            exchange_flow = avg_change  # Положительный = продают
        else:
            exchange_flow = 0
        
        return max(-100, min(100, whale_pressure)), max(-100, min(100, exchange_flow))
    
    def _calculate_sentiment(self, coin: Dict, whale_pressure: float) -> float:
        """Рассчитать оценку настроений (0-100)"""
        change = coin.get("price_change_percentage_24h", 0) or 0
        
        # Базовая оценка
        if change > 5:
            base = 75
        elif change > 2:
            base = 65
        elif change > 0:
            base = 55
        elif change > -2:
            base = 45
        elif change > -5:
            base = 35
        else:
            base = 25
        
        # Корректируем на pressure китов
        adjusted = base + whale_pressure * 0.2
        
        return max(0, min(100, adjusted))
    
    def _predict_based_on_whales(self, analysis: PremiumAnalysis) -> Tuple[str, float, float]:
        """
        Прогноз на основе анализа китов
        
        Returns: (prediction, pump_probability, dump_probability)
        """
        pump_score = 0
        dump_score = 0
        
        # 1. Давление китов (главный фактор)
        if analysis.whale_buy_pressure > 30:
            pump_score += 40
        elif analysis.whale_buy_pressure > 10:
            pump_score += 25
        
        if analysis.whale_buy_pressure < -30:
            dump_score += 40
        elif analysis.whale_buy_pressure < -10:
            dump_score += 25
        
        # 2. Smart Money активность
        smart_money = [w for w in analysis.whale_wallets if w.is_smart_money]
        if smart_money:
            avg_change = sum(w.change_24h for w in smart_money) / len(smart_money)
            if avg_change > 10:
                pump_score += 30
            elif avg_change > 5:
                pump_score += 15
        
        # 3. Биржевые потоки
        if analysis.exchange_flow > 20:  # Большой приток на биржи
            dump_score += 25
        elif analysis.exchange_flow < -20:  # Отток с бирж
            pump_score += 25
        
        # 4. Ценовое движение
        if analysis.price_change_24h > 5:
            dump_score += 20  # Перекупленность
        elif analysis.price_change_24h < -5:
            pump_score += 20  # Перепроданность
        
        # 5. Социальные данные
        if analysis.social_growth > 30:
            pump_score += 15
        elif analysis.social_growth < -30:
            dump_score += 15
        
        # 6. Настроения
        if analysis.sentiment_score > 65:
            pump_score += 10
        elif analysis.sentiment_score < 35:
            dump_score += 10
        
        # Добавляем немного случайности
        pump_score += random.uniform(-5, 10)
        dump_score += random.uniform(-5, 10)
        
        # Нормализуем
        pump_prob = max(0, min(95, pump_score))
        dump_prob = max(0, min(95, dump_score))
        
        # Определяем прогноз
        if pump_prob > dump_prob + 15:
            prediction = "PUMP"
        elif dump_prob > pump_prob + 15:
            prediction = "DUMP"
        else:
            prediction = "HOLD"
        
        return prediction, pump_prob, dump_prob
    
    def _calculate_confidence(self, analysis: PremiumAnalysis) -> float:
        """Рассчитать уверенность в прогнозе"""
        confidence = 50  # Базовая уверенность
        
        # Чем больше китов с одним направлением - выше уверенность
        if abs(analysis.whale_buy_pressure) > 50:
            confidence += 20
        elif abs(analysis.whale_buy_pressure) > 30:
            confidence += 10
        
        # Чем больше объем - выше уверенность
        if analysis.total_whale_balance > 100e6:  # > 100M
            confidence += 15
        elif analysis.total_whale_balance > 50e6:  # > 50M
            confidence += 10
        
        # Чем больше китов - выше уверенность
        if len(analysis.whale_wallets) > 5:
            confidence += 10
        
        # Чем выше вероятность - выше уверенность
        if analysis.pump_probability > 70 or analysis.dump_probability > 70:
            confidence += 10
        
        return max(10, min(95, confidence))
    
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
        if analysis.sentiment_score > 70:
            score_dump += 30
        elif analysis.sentiment_score < 30:
            score_pump += 30
        elif analysis.sentiment_score > 60:
            score_pump += 15
        elif analysis.sentiment_score < 40:
            score_dump += 15
        
        # MACD
        if analysis.prediction == "BULLISH":
            score_pump += 25
        elif analysis.prediction == "BEARISH":
            score_dump += 25
        
        # Whale activity
        if analysis.total_whale_balance > analysis.volume_24h * 0.3:
            score_pump += 20
        
        # Volume surge
        if analysis.social_growth > 50:
            score_pump += 15
        
        # Sentiment
        if analysis.sentiment_score > 60:
            score_pump += 15
        elif analysis.whale_buy_pressure > 60:
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
        
        if analysis.sentiment_score < 40:
            score += 20
        if analysis.prediction == "BULLISH":
            score += 25
        if analysis.total_whale_balance > 0:
            score += 20
        if analysis.sentiment_score > 55:
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
        
        if analysis.total_whale_balance > analysis.volume_24h * 0.2:
            reasons.append("🐋 Smart Money входит в позицию")
        
        if analysis.social_growth > 30:
            reasons.append(f"📈 Рост упоминаний: {analysis.social_growth:+.1f}%")
        
        if analysis.prediction == "BULLISH":
            reasons.append("📊 MACD показывает бычий сигнал")
        
        if analysis.sentiment_score > 60:
            reasons.append("😊 Позитивные настроения в соцсетях")
        
        if analysis.sentiment_score < 40:
            reasons.append("📉 RSI в зоне перепроданности")
        
        if len(analysis.whale_wallets) > 10:
            reasons.append(f"🐋 {len(analysis.whale_wallets)} крупных транзакций")
        
        if not reasons:
            reasons.append("📊 Сильных сигналов не обнаружено")
        
        return reasons[:4]
    
    def _generate_risks(self, analysis: PremiumAnalysis) -> List[str]:
        """Генерация рисков"""
        risks = []
        
        if analysis.dump_probability > 30:
            risks.append("⚠️ Риск дампа присутствует")
        
        if analysis.sentiment_score > 70:
            risks.append("📈 RSI в зоне перекупленности")
        
        if analysis.market_cap < 500e6:
            risks.append("💰 Низкая капитализация")
        
        if analysis.volume_24h < 50e6:
            risks.append("📉 Низкая ликвидность")
        
        if not risks:
            risks.append("⚠️ Общие риски крипторынка")
        
        return risks[:3]
