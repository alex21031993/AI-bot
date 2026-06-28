"""
Data Sources Module
Интеграция 41+ источников данных для крипто-анализа
"""

from .manager import DataSourceManager, data_manager
from .aggregator import DataAggregator


class DataSourcesInfo:
    """
    Информация о всех источниках данных
    """
    
    SOCIAL_SOURCES = [
        {"name": "X (Twitter)", "priority": "HIGH", "metrics": ["mentions", "sentiment", "retweets"]},
        {"name": "Telegram", "priority": "HIGH", "metrics": ["messages", "members", "mentions"]},
        {"name": "Reddit", "priority": "HIGH", "metrics": ["posts", "upvotes", "comments"]},
        {"name": "Instagram", "priority": "MEDIUM", "metrics": ["posts", "followers", "engagement"]},
        {"name": "Facebook", "priority": "LOW", "metrics": ["posts", "reactions"]},
        {"name": "TikTok", "priority": "MEDIUM", "metrics": ["videos", "views", "trending"]},
        {"name": "YouTube", "priority": "MEDIUM", "metrics": ["videos", "views", "subscribers"]},
        {"name": "Discord", "priority": "MEDIUM", "metrics": ["messages", "members"]},
        {"name": "Bitcointalk", "priority": "MEDIUM", "metrics": ["posts", "topics"]},
        {"name": "CryptoPanic", "priority": "HIGH", "metrics": ["news", "sentiment"]},
        {"name": "Hacker News", "priority": "LOW", "metrics": ["mentions", "upvotes"]},
        {"name": "4chan /biz/", "priority": "MEDIUM", "metrics": ["threads", "pump_signals"]},
        {"name": "Medium", "priority": "MEDIUM", "metrics": ["articles", "reads"]},
    ]
    
    MARKET_SOURCES = [
        {"name": "CoinMarketCap", "priority": "CRITICAL", "description": "Цены, капитализация, объёмы"},
        {"name": "CoinGecko", "priority": "CRITICAL", "description": "Цены, соц.данные, разработка"},
        {"name": "DexScreener", "priority": "CRITICAL", "description": "DEX пары, ликвидность"},
        {"name": "DexTools", "priority": "MEDIUM", "description": "Аналитика DEX"},
        {"name": "GeckoTerminal", "priority": "MEDIUM", "description": "DEX данные всех сетей"},
        {"name": "Birdeye", "priority": "HIGH", "description": "Solana ончейн"},
        {"name": "TradingView", "priority": "HIGH", "description": "Технический анализ"},
    ]
    
    ONCHAIN_SOURCES = [
        {"name": "Whale Alert", "priority": "HIGH", "description": "Крупные транзакции"},
        {"name": "Arkham Intelligence", "priority": "HIGH", "description": "Smart Money"},
        {"name": "Nansen", "priority": "MEDIUM", "description": "Smart Money анализ"},
        {"name": "Bubblemaps", "priority": "MEDIUM", "description": "Связи кошельков"},
        {"name": "Etherscan", "priority": "HIGH", "description": "Ethereum транзакции"},
        {"name": "Solscan", "priority": "HIGH", "description": "Solana транзакции"},
        {"name": "BscScan", "priority": "MEDIUM", "description": "BSC транзакции"},
        {"name": "Pump.fun", "priority": "HIGH", "description": "Мем-токены"},
        {"name": "GMGN", "priority": "HIGH", "description": "Solana аналитика"},
        {"name": "Photon", "priority": "MEDIUM", "description": "Solana ликвидность"},
        {"name": "Jupiter", "priority": "HIGH", "description": "DEX агрегатор"},
        {"name": "Raydium", "priority": "MEDIUM", "description": "Solana DEX"},
    ]
    
    NEWS_SOURCES = [
        {"name": "Google Search", "priority": "HIGH", "description": "Поисковые запросы"},
        {"name": "Google Trends", "priority": "HIGH", "description": "Динамика трендов"},
        {"name": "Google News", "priority": "MEDIUM", "description": "Новости"},
        {"name": "CoinDesk", "priority": "HIGH", "description": "Новости, аналитика"},
        {"name": "Cointelegraph", "priority": "HIGH", "description": "Новости, аналитика"},
        {"name": "The Block", "priority": "MEDIUM", "description": "Глубокий анализ"},
        {"name": "Decrypt", "priority": "MEDIUM", "description": "Новости"},
        {"name": "Bitcoin Magazine", "priority": "MEDIUM", "description": "Bitcoin новости"},
    ]
    
    @staticmethod
    def get_all_sources_count() -> dict:
        return {
            "Социальные сети": len(DataSourcesInfo.SOCIAL_SOURCES),
            "Рыночные данные": len(DataSourcesInfo.MARKET_SOURCES),
            "Ончейн и киты": len(DataSourcesInfo.ONCHAIN_SOURCES),
            "Новости": len(DataSourcesInfo.NEWS_SOURCES),
            "Всего": (
                len(DataSourcesInfo.SOCIAL_SOURCES) + 
                len(DataSourcesInfo.MARKET_SOURCES) + 
                len(DataSourcesInfo.ONCHAIN_SOURCES) + 
                len(DataSourcesInfo.NEWS_SOURCES)
            )
        }


__all__ = [
    "DataSourcesInfo",
    "DataSourceManager",
    "data_manager",
    "DataAggregator"
]
