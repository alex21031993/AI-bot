"""
Crypto Intelligence Agent
=========================

A comprehensive cryptocurrency analysis system that analyzes:
- Social media presence and trends
- Market sentiment
- Whale activity
- Technical indicators
- Trading volume and liquidity
"""

from .agents import CryptoIntelligenceAgent, CryptoReport
from .telegram import CryptoIntelligenceBot
from .subscription import SubscriptionManager

__version__ = "1.0.0"
__author__ = "Crypto Intelligence Team"

__all__ = [
    "CryptoIntelligenceAgent",
    "CryptoReport",
    "CryptoIntelligenceBot",
    "SubscriptionManager"
]
