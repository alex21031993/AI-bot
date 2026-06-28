"""
Social Data Sources
Социальные сети: Twitter, Telegram, Reddit, Instagram, TikTok и др.
"""

from typing import Dict, List


class SocialDataSource:
    """
    Источники социальных данных
    """
    
    SOURCES = {
        # ОСНОВНЫЕ
        "twitter": {
            "name": "X (Twitter)",
            "url": "https://x.com",
            "priority": "HIGH",
            "metrics": ["mentions", "sentiment", "retweets", "likes", "influencers"]
        },
        "telegram": {
            "name": "Telegram",
            "url": "https://telegram.org",
            "priority": "HIGH",
            "metrics": ["messages", "members", "mentions", "sentiment"]
        },
        "reddit": {
            "name": "Reddit",
            "url": "https://www.reddit.com",
            "priority": "HIGH",
            "metrics": ["posts", "upvotes", "comments", "subreddits"]
        },
        
        # ДОПОЛНИТЕЛЬНЫЕ
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
            "metrics": ["posts", "reactions", "groups"]
        },
        "tiktok": {
            "name": "TikTok",
            "url": "https://www.tiktok.com",
            "priority": "MEDIUM",
            "metrics": ["videos", "views", "trending", "hashtags"]
        },
        "youtube": {
            "name": "YouTube",
            "url": "https://www.youtube.com",
            "priority": "MEDIUM",
            "metrics": ["videos", "views", "subscribers", "comments"]
        },
        "discord": {
            "name": "Discord",
            "url": "https://discord.com",
            "priority": "MEDIUM",
            "metrics": ["messages", "members", "servers"]
        },
        
        # ФОРУМЫ
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
            "metrics": ["mentions", "upvotes"]
        },
        "4chan_biz": {
            "name": "4chan /biz/",
            "url": "https://boards.4channel.org/biz",
            "priority": "MEDIUM",
            "metrics": ["threads", "pump_signals"]
        },
        "medium": {
            "name": "Medium",
            "url": "https://medium.com",
            "priority": "MEDIUM",
            "metrics": ["articles", "reads"]
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
                "metrics": data["metrics"],
                "category": "Социальные сети"
            }
            for data in SocialDataSource.SOURCES.values()
        ]
    
    @staticmethod
    def get_high_priority() -> List[Dict]:
        """Высокоприоритетные источники"""
        return [
            {"name": data["name"], "url": data["url"]}
            for key, data in SocialDataSource.SOURCES.items()
            if data["priority"] == "HIGH"
        ]
