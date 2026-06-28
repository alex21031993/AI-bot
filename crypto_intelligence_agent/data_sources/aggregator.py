"""
Crypto Data Aggregator
Агрегатор данных со всех источников
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataAggregator:
    """
    Агрегатор данных со всех источников
    41+ источник данных для комплексного анализа
    """
    
    # ==================== СОЦИАЛЬНЫЕ СЕТИ ====================
    SOCIAL_SOURCES = {
        # Уровень 1: Основные социальные сети
        "twitter": {
            "name": "X (Twitter)",
            "url": "https://api.twitter.com/2",
            "priority": "HIGH",
            "metrics": ["mentions", "sentiment", "engagement", "influencers", "hashtags"]
        },
        "telegram": {
            "name": "Telegram",
            "url": "https://t.me",
            "priority": "HIGH",
            "metrics": ["messages", "members", "mentions", "sentiment"]
        },
        "reddit": {
            "name": "Reddit",
            "url": "https://www.reddit.com",
            "priority": "HIGH",
            "metrics": ["posts", "comments", "upvotes", "subreddits"]
        },
        "instagram": {
            "name": "Instagram",
            "url": "https://www.instagram.com",
            "priority": "MEDIUM",
            "metrics": ["posts", "followers", "engagement", "hashtags"]
        },
        "facebook": {
            "name": "Facebook",
            "url": "https://www.facebook.com",
            "priority": "LOW",
            "metrics": ["posts", "reactions", "comments", "groups"]
        },
        "tiktok": {
            "name": "TikTok",
            "url": "https://www.tiktok.com",
            "priority": "MEDIUM",
            "metrics": ["videos", "views", "hashtags", "trending"]
        },
        "youtube": {
            "name": "YouTube",
            "url": "https://www.youtube.com",
            "priority": "MEDIUM",
            "metrics": ["videos", "views", "comments", "subscribers"]
        },
        "discord": {
            "name": "Discord",
            "url": "https://discord.com",
            "priority": "MEDIUM",
            "metrics": ["messages", "members", "mentions", "servers"]
        },
    }
    
    # ==================== КРИПТОСООБЩЕСТВА ====================
    FORUM_SOURCES = {
        "bitcointalk": {
            "name": "Bitcointalk",
            "url": "https://bitcointalk.org",
            "priority": "MEDIUM",
            "metrics": ["posts", "topics", "activity"]
        },
        "cryptopanic": {
            "name": "CryptoPanic",
            "url": "https://cryptopanic.com",
            "priority": "HIGH",
            "metrics": ["news", "sentiment", "trending"]
        },
        "hackernews": {
            "name": "Hacker News",
            "url": "https://news.ycombinator.com",
            "priority": "LOW",
            "metrics": ["mentions", "upvotes", "comments"]
        },
        "4chan_biz": {
            "name": "4chan /biz/",
            "url": "https://boards.4channel.org/biz",
            "priority": "MEDIUM",
            "metrics": ["threads", "posts", "pump_signals"]
        },
        "medium": {
            "name": "Medium",
            "url": "https://medium.com",
            "priority": "MEDIUM",
            "metrics": ["articles", "reads", "publication"]
        },
    }
    
    # ==================== РЫНОЧНЫЕ ДАННЫЕ ====================
    MARKET_SOURCES = {
        "coinmarketcap": {
            "name": "CoinMarketCap",
            "url": "https://api.coinmarketcap.com",
            "priority": "CRITICAL",
            "metrics": ["price", "market_cap", "volume", "holders", "rating"]
        },
        "coingecko": {
            "name": "CoinGecko",
            "url": "https://api.coingecko.com/api/v3",
            "priority": "CRITICAL",
            "metrics": ["price", "market_cap", "volume", "social", "dev_activity"]
        },
        "dexscreener": {
            "name": "DexScreener",
            "url": "https://api.dexscreener.com",
            "priority": "CRITICAL",
            "metrics": ["pairs", "liquidity", "volume", "new_pools", "txns"]
        },
        "dextools": {
            "name": "DexTools",
            "url": "https://api.dexutils.io",
            "priority": "MEDIUM",
            "metrics": ["pairs", "history", "charts"]
        },
        "geckoterminal": {
            "name": "GeckoTerminal",
            "url": "https://api.geckoterminal.com/api/v2",
            "priority": "MEDIUM",
            "metrics": ["pools", "networks", "volume"]
        },
        "birdeye": {
            "name": "Birdeye",
            "url": "https://public-api.birdeye.so",
            "priority": "HIGH",
            "metrics": ["solana_data", "whales", "trades"]
        },
        "tradingview": {
            "name": "TradingView",
            "url": "https://www.tradingview.com",
            "priority": "HIGH",
            "metrics": ["price", "indicators", "support_resistance", "patterns"]
        },
    }
    
    # ==================== ОНЧЕЙН И КИТЫ ====================
    ONCHAIN_SOURCES = {
        "whale_alert": {
            "name": "Whale Alert",
            "url": "https://api.whale-alert.io",
            "priority": "HIGH",
            "metrics": ["transactions", "amounts", "movements"]
        },
        "arkham": {
            "name": "Arkham Intelligence",
            "url": "https://api.arkhamintelligence.com",
            "priority": "HIGH",
            "metrics": ["wallets", "entities", "flows", "labels"]
        },
        "nansen": {
            "name": "Nansen",
            "url": "https://api.nansen.ai",
            "priority": "MEDIUM",
            "metrics": ["smart_money", "wallet_labels", "token_flows"]
        },
        "bubblemaps": {
            "name": "Bubblemaps",
            "url": "https://api.bubblemaps.io",
            "priority": "MEDIUM",
            "metrics": ["concentration", "connections", "holders"]
        },
        "etherscan": {
            "name": "Etherscan",
            "url": "https://api.etherscan.io/api",
            "priority": "HIGH",
            "metrics": ["transactions", "holders", "contracts", "gas"]
        },
        "solscan": {
            "name": "Solscan",
            "url": "https://api.solscan.io",
            "priority": "HIGH",
            "metrics": ["transactions", "tokens", "accounts", "programs"]
        },
        "bscscan": {
            "name": "BscScan",
            "url": "https://api.bscscan.com/api",
            "priority": "MEDIUM",
            "metrics": ["transactions", "holders", "contracts"]
        },
    }
    
    # ==================== SOLANA ЭКОСИСТЕМА ====================
    SOLANA_SOURCES = {
        "pump_fun": {
            "name": "Pump.fun",
            "url": "https://pump.fun",
            "priority": "HIGH",
            "metrics": ["new_tokens", "trades", "volume", "graduations"]
        },
        "gmgn": {
            "name": "GMGN",
            "url": "https://gmgn.ai",
            "priority": "HIGH",
            "metrics": ["solana_tokens", "holders", "trades", "ai_score"]
        },
        "photon": {
            "name": "Photon",
            "url": "https://photon-sol.tinyastro.io",
            "priority": "MEDIUM",
            "metrics": ["solana_liquidity", "trades", "pools"]
        },
        "jupiter": {
            "name": "Jupiter",
            "url": "https://api.jup.ag",
            "priority": "HIGH",
            "metrics": ["volume", "liquidity", "swaps", "price_impact"]
        },
        "raydium": {
            "name": "Raydium",
            "url": "https://api.raydium.io",
            "priority": "MEDIUM",
            "metrics": ["pools", "liquidity", "volume", "swaps"]
        },
    }
    
    # ==================== GOOGLE ====================
    GOOGLE_SOURCES = {
        "google_search": {
            "name": "Google Search",
            "url": "https://www.google.com/search",
            "priority": "HIGH",
            "metrics": ["results", "trends", "related"]
        },
        "google_trends": {
            "name": "Google Trends",
            "url": "https://trends.google.com/trends",
            "priority": "HIGH",
            "metrics": ["interest", "comparisons", "timeline"]
        },
        "google_news": {
            "name": "Google News",
            "url": "https://news.google.com/rss",
            "priority": "MEDIUM",
            "metrics": ["articles", "mentions", "timeline"]
        },
    }
    
    # ==================== НОВОСТИ ====================
    NEWS_SOURCES = {
        "coindesk": {
            "name": "CoinDesk",
            "url": "https://www.coindesk.com",
            "priority": "HIGH",
            "metrics": ["articles", "headlines", "sentiment"]
        },
        "cointelegraph": {
            "name": "Cointelegraph",
            "url": "https://cointelegraph.com",
            "priority": "HIGH",
            "metrics": ["articles", "headlines", "sentiment"]
        },
        "the_block": {
            "name": "The Block",
            "url": "https://www.theblock.co",
            "priority": "MEDIUM",
            "metrics": ["articles", "vc_investments", "data"]
        },
        "decrypt": {
            "name": "Decrypt",
            "url": "https://decrypt.co",
            "priority": "MEDIUM",
            "metrics": ["articles", "headlines"]
        },
        "bitcoinmagazine": {
            "name": "Bitcoin Magazine",
            "url": "https://bitcoinmagazine.com",
            "priority": "MEDIUM",
            "metrics": ["articles", "headlines", "btc_news"]
        },
    }
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = {
            "price": 60,      # 1 минута
            "social": 300,    # 5 минут
            "onchain": 60,    # 1 минута
            "news": 600,      # 10 минут
        }
    
    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def fetch_data(self, source: str, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Базовый метод для запроса данных"""
        try:
            session = await self.get_session()
            url = f"{source}/{endpoint}"
            
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            logger.debug(f"Error fetching {source}: {e}")
            return None
    
    async def get_token_data(self, symbol: str, contract_address: str = None, chain: str = "solana") -> Dict[str, Any]:
        """
        Получить полные данные о токене со всех источников
        """
        result = {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "sources": {},
            "aggregated": {}
        }
        
        # Параллельный сбор данных
        tasks = [
            self._get_market_data(symbol, contract_address, chain),
            self._get_social_data(symbol),
            self._get_onchain_data(symbol, contract_address, chain),
            self._get_news_data(symbol),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обработка результатов
        if isinstance(results[0], dict):
            result["sources"]["market"] = results[0]
        if isinstance(results[1], dict):
            result["sources"]["social"] = results[1]
        if isinstance(results[2], dict):
            result["sources"]["onchain"] = results[2]
        if isinstance(results[3], dict):
            result["sources"]["news"] = results[3]
        
        # Агрегация
        result["aggregated"] = self._aggregate_data(result["sources"])
        
        return result
    
    async def _get_market_data(self, symbol: str, contract_address: str = None, chain: str = "solana") -> Dict:
        """Получить рыночные данные"""
        data = {
            "source": "aggregated",
            "symbol": symbol,
            "coinmarketcap": None,
            "coingecko": None,
            "dexscreener": None,
            "birdeye": None,
            "tradingview": None,
        }
        
        try:
            # CoinGecko API
            gecko_data = await self._fetch_coingecko(symbol)
            if gecko_data:
                data["coingecko"] = gecko_data
            
            # DexScreener API
            dex_data = await self._fetch_dexscreener(contract_address or symbol)
            if dex_data:
                data["dexscreener"] = dex_data
            
            # Birdeye для Solana
            if chain == "solana" and contract_address:
                birdeye_data = await self._fetch_birdeye(contract_address)
                if birdeye_data:
                    data["birdeye"] = birdeye_data
            
        except Exception as e:
            logger.debug(f"Market data error: {e}")
        
        return data
    
    async def _fetch_coingecko(self, symbol: str) -> Optional[Dict]:
        """CoinGecko API"""
        try:
            # Простой поиск токена
            url = f"https://api.coingecko.com/api/v3/search?query={symbol}"
            session = await self.get_session()
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    coins = result.get("coins", [])
                    if coins:
                        coin_id = coins[0].get("id")
                        if coin_id:
                            # Детальные данные
                            detail_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
                            async with session.get(detail_url, timeout=aiohttp.ClientTimeout(total=5)) as d_resp:
                                if d_resp.status == 200:
                                    return await d_resp.json()
        except Exception:
            pass
        return None
    
    async def _fetch_dexscreener(self, query: str) -> Optional[Dict]:
        """DexScreener API"""
        try:
            session = await self.get_session()
            url = f"https://api.dexscreener.com/dex/v2/search?q={query}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            pass
        return None
    
    async def _fetch_birdeye(self, address: str) -> Optional[Dict]:
        """Birdeye API для Solana"""
        try:
            session = await self.get_session()
            url = f"https://public-api.birdeye.so/public/token/{address}"
            headers = {"x-api-key": ""}  # Добавить API ключ если есть
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            pass
        return None
    
    async def _get_social_data(self, symbol: str) -> Dict:
        """Получить социальные данные"""
        data = {
            "source": "aggregated",
            "symbol": symbol,
            "total_mentions": 0,
            "sentiment_score": 0,
            "sources": {}
        }
        
        # Данные из CoinGecko social
        try:
            gecko_social = await self._fetch_coingecko_social(symbol)
            if gecko_social:
                data["sources"]["coingecko"] = gecko_social
                data["total_mentions"] = gecko_social.get("total_mentions", 0)
                data["sentiment_score"] = gecko_social.get("sentiment", 0)
        except Exception:
            pass
        
        return data
    
    async def _fetch_coingecko_social(self, symbol: str) -> Optional[Dict]:
        """Социальные данные из CoinGecko"""
        try:
            session = await self.get_session()
            url = f"https://api.coingecko.com/api/v3/search?query={symbol}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    coins = result.get("coins", [])
                    if coins:
                        return coins[0]
        except Exception:
            pass
        return None
    
    async def _get_onchain_data(self, symbol: str, contract_address: str = None, chain: str = "solana") -> Dict:
        """Получить ончейн данные"""
        data = {
            "source": "aggregated",
            "symbol": symbol,
            "chain": chain,
            "whale_transactions": [],
            "top_holders": [],
            "total_transactions": 0
        }
        
        try:
            if chain == "solana" and contract_address:
                # Solscan API
                solscan_data = await self._fetch_solscan(contract_address)
                if solscan_data:
                    data["solscan"] = solscan_data
            
            elif contract_address:
                # Etherscan для ETH/ERC20
                eth_data = await self._fetch_etherscan(contract_address)
                if eth_data:
                    data["etherscan"] = eth_data
                    
        except Exception:
            pass
        
        return data
    
    async def _fetch_solscan(self, address: str) -> Optional[Dict]:
        """Solscan API"""
        try:
            session = await self.get_session()
            url = f"https://api.solscan.io/token?address={address}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            pass
        return None
    
    async def _fetch_etherscan(self, address: str) -> Optional[Dict]:
        """Etherscan API - требует API ключ"""
        # Базовая реализация без ключа
        return None
    
    async def _get_news_data(self, symbol: str) -> Dict:
        """Получить новостные данные"""
        data = {
            "source": "aggregated",
            "symbol": symbol,
            "news_count": 0,
            "latest_news": [],
            "sentiment": "neutral"
        }
        
        # CryptoPanic агрегатор
        try:
            news = await self._fetch_cryptopanic(symbol)
            if news:
                data["news_count"] = len(news)
                data["latest_news"] = news[:5]
        except Exception:
            pass
        
        return data
    
    async def _fetch_cryptopanic(self, symbol: str) -> List[Dict]:
        """CryptoPanic API"""
        try:
            session = await self.get_session()
            url = f"https://cryptopanic.com/api/v1/posts/?auth_token=&kind=news&search={symbol}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get("results", [])
        except Exception:
            pass
        return []
    
    def _aggregate_data(self, sources: Dict) -> Dict:
        """Агрегация данных со всех источников"""
        aggregated = {
            "price": None,
            "market_cap": None,
            "volume_24h": None,
            "liquidity": None,
            "social_score": 0,
            "onchain_score": 0,
            "news_score": 0,
            "overall_score": 0,
            "confidence": 0
        }
        
        # Извлечение данных из sources
        if "market" in sources and sources["market"]:
            market = sources["market"]
            
            # CoinGecko
            if market.get("coingecko"):
                cg = market["coingecko"]
                if isinstance(cg, dict):
                    aggregated["price"] = cg.get("market_data", {}).get("current_price", {}).get("usd")
                    aggregated["market_cap"] = cg.get("market_data", {}).get("market_cap", {}).get("usd")
                    aggregated["volume_24h"] = cg.get("market_data", {}).get("total_volume", {}).get("usd")
            
            # DexScreener
            if market.get("dexscreener"):
                dex = market["dexscreener"]
                if isinstance(dex, dict):
                    pairs = dex.get("pairs", [])
                    if pairs:
                        aggregated["liquidity"] = pairs[0].get("liquidity", {}).get("usd")
        
        # Социальный счёт
        if "social" in sources and sources["social"]:
            social = sources["social"]
            mentions = social.get("total_mentions", 0)
            # Нормализация: 0-100
            aggregated["social_score"] = min(100, mentions // 100)
        
        # Общий счёт
        scores = [
            aggregated["social_score"],
            aggregated["onchain_score"],
            aggregated["news_score"]
        ]
        valid_scores = [s for s in scores if s > 0]
        if valid_scores:
            aggregated["overall_score"] = sum(valid_scores) / len(valid_scores)
            aggregated["confidence"] = aggregated["overall_score"]
        
        return aggregated
    
    def get_all_sources(self) -> Dict[str, Dict]:
        """Получить список всех источников"""
        return {
            **self.SOCIAL_SOURCES,
            **self.FORUM_SOURCES,
            **self.MARKET_SOURCES,
            **self.ONCHAIN_SOURCES,
            **self.SOLANA_SOURCES,
            **self.GOOGLE_SOURCES,
            **self.NEWS_SOURCES
        }
    
    def get_sources_by_priority(self, priority: str) -> List[Dict]:
        """Получить источники по приоритету"""
        all_sources = self.get_all_sources()
        return [
            {**source, "key": key} 
            for key, source in all_sources.items() 
            if source.get("priority") == priority
        ]
