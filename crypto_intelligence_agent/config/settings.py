"""
Configuration settings for Crypto Intelligence Agent
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class ScoringWeights:
    """Weights for final score calculation"""
    SOCIAL: float = 0.25
    SENTIMENT: float = 0.20
    WHALE: float = 0.20
    TECHNICAL: float = 0.20
    VOLUME: float = 0.15


@dataclass
class SubscriptionPlans:
    """Subscription plan definitions"""
    TRIAL: Dict[str, any] = None
    STANDARD: Dict[str, any] = None
    PREMIUM: Dict[str, any] = None
    
    def __post_init__(self):
        self.TRIAL = {
            "name": "TRIAL",
            "duration_days": 5,
            "price_usd": 2.99,
            "max_requests": 10
        }
        self.STANDARD = {
            "name": "STANDARD", 
            "duration_days": 7,
            "price_usd": 4.99,
            "max_requests": 50
        }
        self.PREMIUM = {
            "name": "PREMIUM",
            "duration_days": 30,
            "price_usd": 14.99,
            "max_requests": float('inf')  # Unlimited
        }


@dataclass
class RiskThresholds:
    """Risk level thresholds based on AI Confidence Score"""
    HIGH_RISK_MAX: int = 40
    SPECULATIVE_MAX: int = 60
    PROMISING_MAX: int = 80
    # Above 80 = Strong Signal


@dataclass
class WhaleThresholds:
    """Thresholds for whale transaction detection"""
    MIN_TRANSACTION_USD: float = 10000  # $10k minimum for alert
    LARGE_TRANSACTION_USD: float = 100000  # $100k for major alert
    WHALE_BALANCE_MIN: float = 1000000  # $1M minimum balance


@dataclass
class APIEndpoints:
    """External API endpoints"""
    COINGECKO_BASE: str = "https://api.coingecko.com/api/v3"
    COINMARKETCAP_BASE: str = "https://pro-api.coinmarketcap.com/v1"
    DEX_SCREENER: str = "https://api.dexscreener.com"
    WHALE_ALERT: str = "https://api.whale-alert.io/v1"


@dataclass 
class TelegramConfig:
    """Telegram bot configuration"""
    COMMANDS: list = None
    
    def __post_init__(self):
        self.COMMANDS = [
            ("analyze", "Полный анализ токена"),
            ("social", "Анализ социальных сетей"),
            ("whales", "Анализ китов"),
            ("sentiment", "Анализ настроений"),
            ("history", "История монеты"),
            ("trend", "Тренды"),
            ("report", "Полный отчет"),
        ]


# Global config instances
SCORING_WEIGHTS = ScoringWeights()
SUBSCRIPTION_PLANS = SubscriptionPlans()
RISK_THRESHOLDS = RiskThresholds()
WHALE_THRESHOLDS = WhaleThresholds()
API_ENDPOINTS = APIEndpoints()
TELEGRAM_CONFIG = TelegramConfig()
