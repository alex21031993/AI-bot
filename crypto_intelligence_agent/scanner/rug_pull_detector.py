"""
Rug Pull Detector - Advanced System
Детекция скамов и рисков rug pull
"""
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class RugCheckResult:
    """Результат проверки на rug pull"""
    symbol: str
    name: str
    contract_address: str = ""
    is_suspicious: bool = False
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Факторы риска
    owner_balance_percent: float = 0
    top_10_holders_percent: float = 0
    locked_liquidity_percent: float = 0
    honeypot_score: float = 0
    
    # Metрики
    age_days: int = 0
    market_cap: float = 0
    liquidity: float = 0
    
    # Сигналы
    red_flags: List[str] = None
    green_flags: List[str] = None
    
    def __post_init__(self):
        if self.red_flags is None:
            self.red_flags = []
        if self.green_flags is None:
            self.green_flags = []


class RugPullDetector:
    """
    Детектор rug pull и скам-токенов
    
    Проверяет:
    - Концентрация токенов у владельцев
    - Ликвидность
    - Возраст токена
    - Metrika Honeypot
    - Флаги риска
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
    
    async def check_token(self, token_id: str) -> RugCheckResult:
        """Проверить токен на rug pull риски"""
        try:
            session = await self._get_session()
            
            # Получаем данные монеты
            async with session.get(
                f"{self.coingecko_base}/coins/{token_id}",
                params={"localization": "false", "community_data": "true"}
            ) as resp:
                if resp.status != 200:
                    return self._default_result(token_id)
                
                data = await resp.json()
            
            symbol = data.get("symbol", "").upper()
            name = data.get("name", "")
            
            # Получаем данные рынка
            async with session.get(
                f"{self.coingecko_base}/coins/markets",
                params={"vs_currency": "usd", "ids": token_id, "order": "market_cap_desc", "per_page": 1}
            ) as resp:
                if resp.status == 200:
                    markets = await resp.json()
                    market_data = markets[0] if markets else {}
                else:
                    market_data = {}
            
            # Анализируем риски
            return self._analyze_risks(symbol, name, data, market_data)
            
        except Exception as e:
            logger.error(f"Rug check error for {token_id}: {e}")
            return self._default_result(token_id)
    
    def _analyze_risks(self, symbol: str, name: str, data: Dict, market_data: Dict) -> RugCheckResult:
        """Анализ рисков rug pull"""
        red_flags = []
        green_flags = []
        
        # Возраст токена
        age_days = 0
        if "genesis_date" in data and data["genesis_date"]:
            try:
                genesis = datetime.strptime(data["genesis_date"], "%Y-%m-%d")
                age_days = (datetime.now() - genesis).days
            except:
                age_days = 0
        
        if age_days < 7:
            red_flags.append("⚠️ Токен младше 7 дней")
        elif age_days > 180:
            green_flags.append("✅ Токен старше 6 месяцев")
        
        # Капитализация и ликвидность
        mcap = market_data.get("market_cap", 0) or 0
        volume = market_data.get("total_volume", 0) or 0
        
        # Симулированные метрики концентрации (в реальности нужны on-chain данные)
        # Для демо используем приблизительные оценки
        owner_percent = self._estimate_owner_percent(data, mcap)
        top10_percent = self._estimate_top10_percent(data, mcap)
        locked_liq = self._estimate_locked_liquidity(data)
        honeypot = self._estimate_honeypot_score(data, market_data)
        
        # Проверки
        if owner_percent > 50:
            red_flags.append(f"🔴 Владелец holds {owner_percent:.0f}% токенов")
        elif owner_percent < 10:
            green_flags.append("✅ Распределение децентрализовано")
        
        if top10_percent > 80:
            red_flags.append(f"🔴 Топ-10 держателей: {top10_percent:.0f}%")
        elif top10_percent < 50:
            green_flags.append("✅ Хорошее распределение")
        
        if locked_liq < 50 and mcap > 1000000:
            red_flags.append("⚠️ Недостаточно заблокированной ликвидности")
        elif locked_liq > 80:
            green_flags.append("✅ Ликвидность заблокирована")
        
        if honeypot > 70:
            red_flags.append("⚠️ Высокий Honeypot score")
        elif honeypot < 30:
            green_flags.append("✅ Низкий риск honeypot")
        
        # Объем
        if mcap > 0:
            vol_ratio = volume / mcap
            if vol_ratio < 0.01:
                red_flags.append("⚠️ Очень низкий объем торгов")
        
        # Считаем общий уровень риска
        risk_score = len(red_flags) * 25 - len(green_flags) * 10
        risk_score = max(0, min(100, risk_score))
        
        if risk_score >= 75:
            risk_level = "CRITICAL"
        elif risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        is_suspicious = risk_level in ["HIGH", "CRITICAL"]
        
        return RugCheckResult(
            symbol=symbol,
            name=name,
            is_suspicious=is_suspicious,
            risk_level=risk_level,
            owner_balance_percent=owner_percent,
            top_10_holders_percent=top10_percent,
            locked_liquidity_percent=locked_liq,
            honeypot_score=honeypot,
            age_days=age_days,
            market_cap=mcap,
            liquidity=volume,
            red_flags=red_flags,
            green_flags=green_flags
        )
    
    def _estimate_owner_percent(self, data: Dict, mcap: float) -> float:
        """Оценка % токенов у владельца"""
        # В реальности нужны on-chain данные
        # Симулируем на основе данных
        community = data.get("community_data", {}) or {}
        twitter = community.get("twitter_followers", 0) or 0
        
        # Чем больше сообщество, тем более децентрализован
        if mcap > 1_000_000_000:
            return 5 + (1000000 / twitter) if twitter > 0 else 15
        elif mcap > 100_000_000:
            return 10 + (500000 / twitter) if twitter > 0 else 25
        else:
            return 30 + (100000 / twitter) if twitter > 0 else 50
    
    def _estimate_top10_percent(self, data: Dict, mcap: float) -> float:
        """Оценка % токенов у топ-10"""
        owner = self._estimate_owner_percent(data, mcap)
        # Обычно топ-10 держат в 2-3 раза больше чем основной владелец
        return min(95, owner * 2.5)
    
    def _estimate_locked_liquidity(self, data: Dict) -> float:
        """Оценка заблокированной ликвидности"""
        # Проверяем наличие ликвидности
        community = data.get("community_data", {}) or {}
        
        # Наличие большого сообщества обычно означает честный проект
        total_social = (
            (community.get("twitter_followers", 0) or 0) +
            (community.get("reddit_subscribers", 0) or 0) +
            (community.get("telegram_channel_users_count", 0) or 0)
        )
        
        if total_social > 500000:
            return 85
        elif total_social > 50000:
            return 70
        elif total_social > 5000:
            return 50
        else:
            return 30
    
    def _estimate_honeypot_score(self, data: Dict, market_data: Dict) -> float:
        """Оценка риска honeypot"""
        score = 30  # Базовый
        
        # Возраст
        if "genesis_date" in data and data["genesis_date"]:
            try:
                genesis = datetime.strptime(data["genesis_date"], "%Y-%m-%d")
                age = (datetime.now() - genesis).days
                if age < 30: score += 30
                elif age < 90: score += 15
            except:
                pass
        
        # Ликвидность
        mcap = market_data.get("market_cap", 0) or 0
        volume = market_data.get("total_volume", 0) or 0
        if mcap > 0:
            if volume / mcap < 0.005: score += 25
            elif volume / mcap < 0.02: score += 10
        
        # Описание
        desc = data.get("description", {}).get("en", "") or ""
        if len(desc) < 100: score += 15
        
        return min(100, score)
    
    def _default_result(self, token_id: str) -> RugCheckResult:
        """Результат по умолчанию"""
        return RugCheckResult(
            symbol=token_id.upper(),
            name=token_id,
            is_suspicious=False,
            risk_level="UNKNOWN",
            red_flags=["⚠️ Недостаточно данных для анализа"],
            green_flags=["✅ Требуется ручная проверка"]
        )
    
    def format_report(self, result: RugCheckResult) -> str:
        """Форматирование отчета"""
        risk_emoji = {
            "LOW": "🟢",
            "MEDIUM": "🟡",
            "HIGH": "🟠",
            "CRITICAL": "🔴",
            "UNKNOWN": "⚪"
        }
        
        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "🛡️ *RUG PULL DETECTOR*",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            f"{risk_emoji.get(result.risk_level, '⚪')} *{result.symbol}* ({result.name})",
            f"📊 Уровень риска: *{result.risk_level}*",
            ""
        ]
        
        if result.age_days > 0:
            lines.append(f"📅 Возраст токена: {result.age_days} дней")
        
        if result.market_cap > 0:
            lines.append(f"💰 Капитализация: ${result.market_cap/1e6:.1f}M")
        
        lines.extend([
            "",
            "📊 *РАСПРЕДЕЛЕНИЕ:*",
            f"   👤 Владелец: {result.owner_balance_percent:.0f}%",
            f"   👥 Топ-10: {result.top_10_holders_percent:.0f}%",
            f"   🔒 Ликвидность: {result.locked_liquidity_percent:.0f}%",
            f"   🍯 Honeypot: {result.honeypot_score:.0f}%",
            ""
        ])
        
        if result.red_flags:
            lines.extend(["🚨 *КРАСНЫЕ ФЛАГИ:*"])
            for flag in result.red_flags:
                lines.append(f"   {flag}")
            lines.append("")
        
        if result.green_flags:
            lines.extend(["✅ *ЗЕЛЕНЫЕ ФЛАГИ:*"])
            for flag in result.green_flags:
                lines.append(f"   {flag}")
            lines.append("")
        
        lines.extend([
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "⚠️ Это не финансовая рекомендация!",
            "🕐 " + datetime.now().strftime("%H:%M %d.%m.%Y")
        ])
        
        return "\n".join(lines)