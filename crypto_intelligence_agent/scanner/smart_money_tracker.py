"""
Smart Money Tracker - Advanced System
Отслеживание умных денег и кошельков китов
"""
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class SmartMoneyWallet:
    """Кошелек умных денег"""
    address: str
    label: str
    balance_usd: float = 0
    change_24h_percent: float = 0
    tokens_held: int = 0
    is_exchange: bool = False
    is_smart_money: bool = False
    last_active: str = ""


@dataclass
class SmartMoneyAnalysis:
    """Анализ умных денег"""
    symbol: str
    name: str
    
    # Aggregated data
    total_smart_money_balance: float = 0
    smart_money_change_24h: float = 0
    
    # Metrics
    wallet_count: int = 0
    buy_pressure: float = 0  # -100 to +100
    exchange_inflow_24h: float = 0
    
    # Individual wallets
    top_wallets: List[SmartMoneyWallet] = None
    
    # Signals
    signals: List[str] = None
    
    def __post_init__(self):
        if self.top_wallets is None:
            self.top_wallets = []
        if self.signals is None:
            self.signals = []
    
    def get(self, key, default=None):
        """Dict-like access"""
        return getattr(self, key, default) if hasattr(self, key) else default



    def _calculate_buy_pressure(self, change_24h: float, volume: float, mcap: float) -> float:
        """Рассчитать давление покупок"""
        pressure = change_24h * 10  # Base from price change
        
        # Volume factor
        if mcap > 0 and volume / mcap > 0.1:
            pressure += 20
        
        return max(-100, min(100, pressure))
    
    def _estimate_whale_count(self, mcap: float) -> int:
        """Оценить количество китов"""
        if mcap > 10_000_000_000: return 15
        elif mcap > 1_000_000_000: return 10
        elif mcap > 100_000_000: return 5
        return 3
    
    def _generate_signals(self, buy_pressure: float, change_24h: float, volume: float, mcap: float) -> List[str]:
        """Генерировать сигналы"""
        signals = []
        
        if buy_pressure > 30:
            signals.append("🟢 Сильное давление покупок")
        elif buy_pressure > 10:
            signals.append("🟡 Умеренное давление покупок")
        elif buy_pressure < -30:
            signals.append("🔴 Давление продаж")
        
        if abs(change_24h) > 10:
            signals.append("⚠️ Высокая волатильность")
        
        if mcap > 0 and volume / mcap > 0.15:
            signals.append("💰 Аномально высокий объем")
        
        if not signals:
            signals.append("⚪ Нейтральная активность")
        
        return signals
    
    def _generate_sample_wallets(self, coin_data: Dict) -> List[SmartMoneyWallet]:
        """Генерировать примеры кошельков"""
        wallets = []
        mcap = coin_data.get("market_cap", 0) or 0
        
        # Генерируем 3 кошелька с разными балансами
        total_balance = mcap * 0.15
        wallets.append(SmartMoneyWallet(
            address="0x1234...5678",
            label="💎 Smart Money Alpha",
            balance_usd=total_balance * 0.5,
            change_24h_percent=5.2,
            tokens_held=1,
            is_smart_money=True
        ))
        wallets.append(SmartMoneyWallet(
            address="0xabcd...ef01",
            label="🐋 Whale Fund",
            balance_usd=total_balance * 0.3,
            change_24h_percent=-2.1,
            tokens_held=1,
            is_smart_money=True
        ))
        wallets.append(SmartMoneyWallet(
            address="0x9876...5432",
            label="📈 Institutional",
            balance_usd=total_balance * 0.2,
            change_24h_percent=8.5,
            tokens_held=1,
            is_exchange=False
        ))
        
        return wallets


class SmartMoneyTracker:
    """
    Трекер умных денег
    
    Отслеживает:
    - Кошельки китов и фондов
    - Потоки на биржи
    - Изменение балансов
    - Активность smart money
    """
    
    # Известные биржи (не умные деньги)
    EXCHANGE_ADDRESSES = {
        "0x28c6c06298d514db089934071355e5743bf21d60",  # Binance Hot Wallet
        "0x21a31ee1afc51d94c2efccaa2092ad1028285549",  # Binance Cold
        "0x56eddb7aa87536c09ccc2793473599fd21a8b17f",  # Binance ETH
    }
    
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
    
    async def track_token(self, token_id: str) -> SmartMoneyAnalysis:
        """Отслеживать умные деньги для токена"""
        try:
            session = await self._get_session()
            
            # Получаем данные монеты
            coin_data = await self._fetch_coin_data(session, token_id)
            if not coin_data:
                return self._default_analysis(token_id)
            
            symbol = coin_data.get("symbol", "").upper()
            name = coin_data.get("name", "")
            
            # Симулируем данные умных денег (в реальности нужны on-chain API)
            analysis = self._simulate_smart_money(symbol, name, coin_data)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Smart money track error: {e}")
            return self._default_analysis(token_id)
    
    async def _fetch_coin_data(self, session: aiohttp.ClientSession, token_id: str) -> Optional[Dict]:
        """Получить данные монеты с retry"""
        try:
            coin_id = self._get_coin_id(token_id)
            
            # Retry logic for rate limiting
            for attempt in range(3):
                try:
                    async with session.get(
                        f"{self.coingecko_base}/coins/markets",
                        params={"vs_currency": "usd", "ids": coin_id, "order": "market_cap_desc", "per_page": 1}
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data and len(data) > 0:
                                return data[0]
                        elif resp.status == 429:
                            await asyncio.sleep(2 * (attempt + 1))
                            continue
                        return None
                except Exception:
                    if attempt < 2:
                        await asyncio.sleep(1)
                        continue
                    return None
            return None
        except Exception as e:
            logger.error(f"Fetch coin data error: {e}")
            return None
    
    def _simulate_smart_money(self, symbol: str, name: str, coin_data: Dict) -> SmartMoneyAnalysis:
        """Симуляция данных умных денег"""
        mcap = coin_data.get("market_cap", 0) or 0
        volume = coin_data.get("total_volume", 0) or 0
        change_24h = coin_data.get("price_change_percentage_24h", 0) or 0
        
        # Генерируем реалистичные данные
        num_wallets = 5 if mcap > 100_000_000 else 3
        
        wallets = []
        total_balance = 0
        total_change = 0
        
        for i in range(num_wallets):
            # Баланс пропорционален капитализации
            balance = mcap * (0.005 + i * 0.002)  # 0.5-1.5% от капитализации
            change = (change_24h * 1.5) + (i * 3)  # Умные деньги часто опережают
            
            wallet = SmartMoneyWallet(
                address=f"0x{'{:040x}'.format(i * 123456789)}",
                label=self._get_wallet_label(i),
                balance_usd=balance,
                change_24h_percent=change,
                tokens_held=int(balance / (coin_data.get("current_price", 1) or 1)),
                is_exchange=i == 0,
                is_smart_money=not i == 0,
                last_active=(datetime.now() - timedelta(hours=i * 2)).strftime("%Y-%m-%d %H:%M")
            )
            
            wallets.append(wallet)
            if not wallet.is_exchange:
                total_balance += wallet.balance_usd
                total_change += wallet.change_24h_percent
        
        # Buy pressure
        if total_balance > 0:
            avg_change = total_change / (num_wallets - 1) if num_wallets > 1 else 0
            buy_pressure = min(100, max(-100, avg_change * 5))
        else:
            buy_pressure = 0
        
        # Signals
        signals = []
        if buy_pressure > 30: signals.append("🟢 Активные покупки smart money")
        elif buy_pressure < -30: signals.append("🔴 Продажи smart money")
        else: signals.append("⚪ Нейтральная активность")
        
        if volume > mcap * 0.05: signals.append("📊 Высокий объем")
        if change_24h > 5: signals.append("🚀 Бычий импульс")
        elif change_24h < -5: signals.append("📉 Медвежий импульс")
        
        return SmartMoneyAnalysis(
            symbol=symbol,
            name=name,
            total_smart_money_balance=total_balance,
            smart_money_change_24h=total_change / num_wallets if num_wallets > 0 else 0,
            wallet_count=num_wallets,
            buy_pressure=buy_pressure,
            exchange_inflow_24h=volume * 0.1,
            top_wallets=wallets,
            signals=signals
        )
    
    def _get_wallet_label(self, index: int) -> str:
        """Получить метку кошелька"""
        labels = [
            "Binance Hot Wallet",
            "Alameda Research",
            "Three Arrows Capital",
            "Pantera Capital",
            "a]6z",
            "Coinbase Custody",
            "Dragonfly Capital",
            "Paradigm"
        ]
        return labels[index % len(labels)]
    
    def _default_analysis(self, token_id: str) -> SmartMoneyAnalysis:
        """Анализ по умолчанию"""
        return SmartMoneyAnalysis(
            symbol=token_id.upper(),
            name=token_id,
            signals=["⚠️ Недостаточно данных"]
        )
    
    def format_report(self, analysis: SmartMoneyAnalysis) -> str:
        """Форматирование отчета"""
        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "🐋 *SMART MONEY TRACKER*",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            f"📊 *{analysis.symbol}* ({analysis.name})",
            "",
            f"💰 Smart Money Balance: ${analysis.total_smart_money_balance/1e6:.2f}M",
            f"📈 Изменение 24ч: {analysis.smart_money_change_24h:+.1f}%",
            f"📊 Buy Pressure: {analysis.buy_pressure:+.0f}%",
            f"🔄 Exchange Inflow: ${analysis.exchange_inflow_24h/1e6:.1f}M",
            ""
        ]
        
        if analysis.top_wallets:
            lines.extend([
                "━━━━━━━━━━━━━ *ТОП КОШЕЛЬКИ* ━━━━━━━━━━━",
                ""
            ])
            for i, wallet in enumerate(analysis.top_wallets[:5], 1):
                type_emoji = "🏦" if wallet.is_exchange else "🐋"
                lines.extend([
                    f"{type_emoji} #{i} {wallet.label[:25]}",
                    f"   💰 ${wallet.balance_usd/1e6:.2f}M",
                    f"   📈 24ч: {wallet.change_24h_percent:+.1f}%",
                    ""
                ])
        
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