"""
Data Sources Module
Интеграция 41+ источников данных для крипто-анализа
"""

from .market_data import MarketDataSource
from .social_data import SocialDataSource
from .onchain_data import OnChainDataSource
from .news_data import NewsDataSource

__all__ = [
    "MarketDataSource",
    "SocialDataSource", 
    "OnChainDataSource",
    "NewsDataSource"
]
