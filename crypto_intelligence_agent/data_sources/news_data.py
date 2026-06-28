"""
News Data Sources
Новостные ресурсы: CoinDesk, Cointelegraph, Google и др.
"""

from typing import Dict, List


class NewsDataSource:
    """
    Источники новостных данных
    """
    
    SOURCES = {
        # GOOGLE СЕРВИСЫ
        "google_search": {
            "name": "Google Search",
            "url": "https://www.google.com",
            "priority": "HIGH",
            "description": "Поисковые запросы, тренды"
        },
        "google_trends": {
            "name": "Google Trends",
            "url": "https://trends.google.com",
            "priority": "HIGH",
            "description": "Динамика поисковых запросов"
        },
        "google_news": {
            "name": "Google News",
            "url": "https://news.google.com",
            "priority": "MEDIUM",
            "description": "Новости о криптовалютах"
        },
        
        # НОВОСТНЫЕ КРИПТОРЕСУРСЫ
        "coindesk": {
            "name": "CoinDesk",
            "url": "https://www.coindesk.com",
            "priority": "HIGH",
            "description": "Новости, аналитика рынка"
        },
        "cointelegraph": {
            "name": "Cointelegraph",
            "url": "https://cointelegraph.com",
            "priority": "HIGH",
            "description": "Новости, интервью, аналитика"
        },
        "the_block": {
            "name": "The Block",
            "url": "https://www.theblock.co",
            "priority": "MEDIUM",
            "description": "Глубокий анализ, VC инвестиции"
        },
        "decrypt": {
            "name": "Decrypt",
            "url": "https://decrypt.co",
            "priority": "MEDIUM",
            "description": "Новости, образовательный контент"
        },
        "bitcoinmagazine": {
            "name": "Bitcoin Magazine",
            "url": "https://bitcoinmagazine.com",
            "priority": "MEDIUM",
            "description": "Bitcoin новости, аналитика"
        },
    }
    
    @staticmethod
    def get_source_info() -> List[Dict]:
        """Информация о источниках"""
        return [
            {
                "name": data["name"],
                "url": data["url"],
                "priority": data["priority"],
                "description": data["description"],
                "category": "Новости"
            }
            for data in NewsDataSource.SOURCES.values()
        ]
    
    @staticmethod
    def get_high_priority() -> List[Dict]:
        """Высокоприоритетные источники"""
        return [
            {"name": data["name"], "url": data["url"]}
            for key, data in NewsDataSource.SOURCES.items()
            if data["priority"] == "HIGH"
        ]


class DataSourcesInfo:
    """
    Информация о всех источниках данных
    """
    
    @staticmethod
    def get_all_sources_count() -> Dict[str, int]:
        """Количество источников по категориям"""
        from .social_data import SocialDataSource
        from .market_data import MarketDataSource
        from .onchain_data import OnChainDataSource
        from .news_data import NewsDataSource
        
        return {
            "Социальные сети": len(SocialDataSource.SOURCES),
            "Рыночные данные": len(MarketDataSource.SOURCES),
            "Ончейн и киты": len(OnChainDataSource.SOURCES),
            "Новости": len(NewsDataSource.SOURCES),
            "Всего": (
                len(SocialDataSource.SOURCES) + 
                len(MarketDataSource.SOURCES) + 
                len(OnChainDataSource.SOURCES) + 
                len(NewsDataSource.SOURCES)
            )
        }
    
    @staticmethod
    def get_sources_text() -> str:
        """Текстовое описание всех источников"""
        from .social_data import SocialDataSource
        from .market_data import MarketDataSource
        from .onchain_data import OnChainDataSource
        from .news_data import NewsDataSource
        
        text = """📡 *ИСТОЧНИКИ ДАННЫХ (41+)*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 *РЫНОЧНЫЕ ДАННЫЕ:*
"""
        for key, data in MarketDataSource.SOURCES.items():
            text += f"• {data['name']}\n"
        
        text += """
🐋 *ОНЧЕЙН И КИТЫ:*
"""
        for key, data in OnChainDataSource.SOURCES.items():
            text += f"• {data['name']}\n"
        
        text += """
💬 *СОЦИАЛЬНЫЕ СЕТИ:*
"""
        for key, data in SocialDataSource.SOURCES.items():
            text += f"• {data['name']}\n"
        
        text += """
📰 *НОВОСТИ:*
"""
        for key, data in NewsDataSource.SOURCES.items():
            text += f"• {data['name']}\n"
        
        return text