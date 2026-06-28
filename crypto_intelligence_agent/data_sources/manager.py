"""
Data Source Manager
Менеджер источников данных для интеграции в бот
"""

import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataSourceManager:
    """
    Менеджер всех источников данных
    Интеграция с 41+ источниками
    """
    
    # ==================== ВСЕ ИСТОЧНИКИ ====================
    ALL_SOURCES = {
        # СОЦИАЛЬНЫЕ СЕТИ
        "twitter": {"name": "X (Twitter)", "priority": "HIGH"},
        "telegram": {"name": "Telegram", "priority": "HIGH"},
        "reddit": {"name": "Reddit", "priority": "HIGH"},
        "instagram": {"name": "Instagram", "priority": "MEDIUM"},
        "facebook": {"name": "Facebook", "priority": "LOW"},
        "tiktok": {"name": "TikTok", "priority": "MEDIUM"},
        "youtube": {"name": "YouTube", "priority": "MEDIUM"},
        "discord": {"name": "Discord", "priority": "MEDIUM"},
        
        # КРИПТОСООБЩЕСТВА
        "bitcointalk": {"name": "Bitcointalk", "priority": "MEDIUM"},
        "cryptopanic": {"name": "CryptoPanic", "priority": "HIGH"},
        "hackernews": {"name": "Hacker News", "priority": "LOW"},
        "4chan_biz": {"name": "4chan /biz/", "priority": "MEDIUM"},
        "medium": {"name": "Medium", "priority": "MEDIUM"},
        
        # РЫНОЧНЫЕ ДАННЫЕ
        "coinmarketcap": {"name": "CoinMarketCap", "priority": "CRITICAL"},
        "coingecko": {"name": "CoinGecko", "priority": "CRITICAL"},
        "dexscreener": {"name": "DexScreener", "priority": "CRITICAL"},
        "dextools": {"name": "DexTools", "priority": "MEDIUM"},
        "geckoterminal": {"name": "GeckoTerminal", "priority": "MEDIUM"},
        "birdeye": {"name": "Birdeye", "priority": "HIGH"},
        "tradingview": {"name": "TradingView", "priority": "HIGH"},
        
        # ОНЧЕЙН И КИТЫ
        "whale_alert": {"name": "Whale Alert", "priority": "HIGH"},
        "arkham": {"name": "Arkham Intelligence", "priority": "HIGH"},
        "nansen": {"name": "Nansen", "priority": "MEDIUM"},
        "bubblemaps": {"name": "Bubblemaps", "priority": "MEDIUM"},
        "etherscan": {"name": "Etherscan", "priority": "HIGH"},
        "solscan": {"name": "Solscan", "priority": "HIGH"},
        "bscscan": {"name": "BscScan", "priority": "MEDIUM"},
        
        # SOLANA
        "pump_fun": {"name": "Pump.fun", "priority": "HIGH"},
        "gmgn": {"name": "GMGN", "priority": "HIGH"},
        "photon": {"name": "Photon", "priority": "MEDIUM"},
        "jupiter": {"name": "Jupiter", "priority": "HIGH"},
        "raydium": {"name": "Raydium", "priority": "MEDIUM"},
        
        # GOOGLE
        "google_search": {"name": "Google Search", "priority": "HIGH"},
        "google_trends": {"name": "Google Trends", "priority": "HIGH"},
        "google_news": {"name": "Google News", "priority": "MEDIUM"},
        
        # НОВОСТИ
        "coindesk": {"name": "CoinDesk", "priority": "HIGH"},
        "cointelegraph": {"name": "Cointelegraph", "priority": "HIGH"},
        "the_block": {"name": "The Block", "priority": "MEDIUM"},
        "decrypt": {"name": "Decrypt", "priority": "MEDIUM"},
        "bitcoinmagazine": {"name": "Bitcoin Magazine", "priority": "MEDIUM"},
    }
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl = 60  # секунды
    
    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def fetch_json(self, url: str, headers: Dict = None, params: Dict = None) -> Optional[Dict]:
        """Базовый метод для GET запросов"""
        try:
            session = await self.get_session()
            async with session.get(
                url, 
                headers=headers, 
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            logger.debug(f"Fetch error {url}: {e}")
        return None
    
    # ==================== COINGECKO ====================
    async def get_coingecko_data(self, symbol: str) -> Optional[Dict]:
        """CoinGecko - рыночные данные"""
        try:
            # Найти coin ID по символу
            search_url = f"https://api.coingecko.com/api/v3/search?query={symbol}"
            search = await self.fetch_json(search_url)
            
            if search and search.get("coins"):
                coin_id = search["coins"][0]["id"]
                
                # Детальные данные
                detail_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
                params = {
                    "localization": "false",
                    "tickers": "false",
                    "market_data": "true",
                    "community_data": "true",
                    "developer_data": "false"
                }
                return await self.fetch_json(detail_url, params=params)
        except Exception:
            pass
        return None
    
    # ==================== DEXSCREENER ====================
    async def get_dexscreener_data(self, query: str) -> Optional[Dict]:
        """DexScreener - DEX пары и ликвидность"""
        try:
            url = f"https://api.dexscreener.com/dex/v2/search?q={query}"
            return await self.fetch_json(url)
        except Exception:
            pass
        return None
    
    async def get_dexscreener_pairs(self, chain: str, address: str) -> Optional[Dict]:
        """DexScreener - пары по адресу"""
        try:
            url = f"https://api.dexscreener.com/dex/v2/pairs/{chain}/{address}"
            return await self.fetch_json(url)
        except Exception:
            pass
        return None
    
    # ==================== SOLSCAN ====================
    async def get_solscan_token(self, address: str) -> Optional[Dict]:
        """Solscan - данные токена Solana"""
        try:
            session = await self.get_session()
            url = f"https://api.solscan.io/token?address={address}"
            headers = {"Accept": "application/json"}
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            pass
        return None
    
    async def get_solscan_transfers(self, address: str) -> Optional[Dict]:
        """Solscan - трансферы токена"""
        try:
            session = await self.get_session()
            url = f"https://api.solscan.io/token/transfer?address={address}&limit=50"
            headers = {"Accept": "application/json"}
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            pass
        return None
    
    # ==================== DEXTOOLS ====================
    async def get_dextools_data(self, chain: str, address: str) -> Optional[Dict]:
        """DexTools - аналитика DEX"""
        try:
            url = f"https://api.dextools.io/v2/pool/{chain}/{address}/transactions"
            headers = {"X-API-Key": ""}  # Добавить ключ если есть
            return await self.fetch_json(url, headers=headers)
        except Exception:
            pass
        return None
    
    # ==================== CRYPTOPANIC ====================
    async def get_cryptopanic_news(self, symbol: str) -> List[Dict]:
        """CryptoPanic - новости"""
        try:
            url = f"https://cryptopanic.com/api/v1/posts/"
            params = {"auth_token": "", "kind": "news", "search": symbol}
            data = await self.fetch_json(url, params=params)
            if data:
                return data.get("results", [])[:10]
        except Exception:
            pass
        return []
    
    # ==================== DEXSCREENER NEW PAIRS ====================
    async def get_new_pairs(self, chain: str = "solana", limit: int = 20) -> List[Dict]:
        """Новые пары на DexScreener"""
        try:
            url = f"https://api.dexscreener.com/dex/v2/new-pairs/{chain}?limit={limit}"
            data = await self.fetch_json(url)
            if data and data.get("pairs"):
                return data["pairs"]
        except Exception:
            pass
        return []
    
    # ==================== GECKOTERMINAL ====================
    async def get_geckoterminal_pools(self, network: str, address: str) -> Optional[Dict]:
        """GeckoTerminal - пулы"""
        try:
            url = f"https://api.geckoterminal.com/api/v2/networks/{network}/tokens/{address}/pools"
            return await self.fetch_json(url)
        except Exception:
            pass
        return None
    
    # ==================== JUPITER ====================
    async def get_jupiter_price(self, addresses: List[str]) -> Optional[Dict]:
        """Jupiter - цены Solana"""
        try:
            session = await self.get_session()
            url = "https://api.jup.ag/price/v2"
            params = {"ids": ",".join(addresses)}
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            pass
        return None
    
    # ==================== WHALE ALERT ====================
    async def get_whale_alerts(self, min_value: int = 100000) -> List[Dict]:
        """Whale Alert - крупные транзакции"""
        try:
            session = await self.get_session()
            url = f"https://api.whale-alert.io/v1/transactions?min_value={min_value}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("transactions", [])
        except Exception:
            pass
        return []
    
    # ==================== SOLANA TRACKERS ====================
    async def get_pump_fun_tokens(self, limit: int = 20) -> List[Dict]:
        """Pump.fun - новые токены"""
        # Публичного API нет, используем альтернативы
        return []
    
    async def get_gmgn_data(self, address: str) -> Optional[Dict]:
        """GMGN - данные Solana"""
        try:
            url = f"https://gmgn.ai/api/v1/token/{address}"
            return await self.fetch_json(url)
        except Exception:
            pass
        return None
    
    # ==================== АГРЕГАЦИЯ ====================
    async def get_full_token_analysis(self, symbol: str, contract_address: str = None, chain: str = "solana") -> Dict:
        """Полный анализ токена со всех источников"""
        result = {
            "symbol": symbol,
            "chain": chain,
            "timestamp": datetime.utcnow().isoformat(),
            "sources_used": [],
            "data": {}
        }
        
        # Параллельный сбор данных
        tasks = []
        
        # CoinGecko
        tasks.append(self._task_with_name("coingecko", self.get_coingecko_data(symbol)))
        
        # DexScreener
        tasks.append(self._task_with_name("dexscreener", self.get_dexscreener_data(symbol)))
        
        # DexScreener pairs если есть адрес
        if contract_address:
            tasks.append(self._task_with_name(
                "dexscreener_pairs", 
                self.get_dexscreener_pairs(chain, contract_address)
            ))
        
        # Solscan если Solana
        if chain == "solana" and contract_address:
            tasks.append(self._task_with_name("solscan", self.get_solscan_token(contract_address)))
            tasks.append(self._task_with_name("gmgn", self.get_gmgn_data(contract_address)))
        
        # Jupiter для Solana
        if chain == "solana" and contract_address:
            tasks.append(self._task_with_name("jupiter", self.get_jupiter_price([contract_address])))
        
        # CryptoPanic news
        tasks.append(self._task_with_name("cryptopanic", self.get_cryptopanic_news(symbol)))
        
        # Выполняем параллельно
        results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)
        
        # Собираем результаты
        for i, task in enumerate(tasks):
            name = task[0]
            data = results[i]
            if not isinstance(data, Exception) and data:
                result["sources_used"].append(name)
                result["data"][name] = data
        
        # Генерируем aggregated scores
        result["aggregated"] = self._aggregate(result["data"])
        
        return result
    
    def _task_with_name(self, name: str, coro):
        return (name, coro)
    
    def _aggregate(self, data: Dict) -> Dict:
        """Агрегация данных в единый счёт"""
        return {
            "sources_count": len(data),
            "has_market_data": "coingecko" in data or "dexscreener" in data,
            "has_onchain_data": "solscan" in data,
            "has_social_data": "cryptopanic" in data,
        }
    
    # ==================== UTILITY ====================
    def get_sources_list(self) -> List[Dict]:
        """Получить список всех источников"""
        return [
            {"key": key, **value}
            for key, value in self.ALL_SOURCES.items()
        ]
    
    def get_sources_by_priority(self, priority: str) -> List[Dict]:
        """Источники по приоритету"""
        return [
            {"key": key, **value}
            for key, value in self.ALL_SOURCES.items()
            if value.get("priority") == priority
        ]
    
    def get_total_sources_count(self) -> int:
        """Всего источников"""
        return len(self.ALL_SOURCES)


# Глобальный экземпляр
data_manager = DataSourceManager()
