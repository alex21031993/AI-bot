"""
Market Data Sources
Рыночные данные: CoinMarketCap, CoinGecko, DexScreener, TradingView и др.
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class MarketDataSource:
    """
    Источники рыночных данных
    """
    
    SOURCES = {
        "coinmarketcap": {
            "name": "CoinMarketCap",
            "url": "https://coinmarketcap.com",
            "api_url": "https://api.coinmarketcap.com",
            "description": "Цены, капитализация, объёмы"
        },
        "coingecko": {
            "name": "CoinGecko", 
            "url": "https://www.coingecko.com",
            "api_url": "https://api.coingecko.com/api/v3",
            "description": "Цены, соц.данные, разработка"
        },
        "dexscreener": {
            "name": "DexScreener",
            "url": "https://dexscreener.com",
            "api_url": "https://api.dexscreener.com",
            "description": "DEX пары, ликвидность, объёмы"
        },
        "dextools": {
            "name": "DexTools",
            "url": "https://www.dextools.io",
            "api_url": "https://api.dextools.io",
            "description": "Аналитика DEX"
        },
        "geckoterminal": {
            "name": "GeckoTerminal",
            "url": "https://www.geckoterminal.com",
            "api_url": "https://api.geckoterminal.com/api/v2",
            "description": "DEX данные всех сетей"
        },
        "birdeye": {
            "name": "Birdeye",
            "url": "https://birdeye.so",
            "api_url": "https://public-api.birdeye.so",
            "description": "Solana ончейн данные"
        },
        "tradingview": {
            "name": "TradingView",
            "url": "https://www.tradingview.com",
            "description": "Технический анализ"
        },
    }
    
    @staticmethod
    def get_source_info() -> List[Dict]:
        """Информация о источниках"""
        return [
            {
                "name": data["name"],
                "url": data["url"],
                "description": data["description"],
                "category": "Рыночные данные"
            }
            for data in MarketDataSource.SOURCES.values()
        ]
