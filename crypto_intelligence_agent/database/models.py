"""
Database models for Crypto Intelligence Bot
"""
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum


class UserRole(Enum):
    """User roles"""
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"


class AlertType(Enum):
    """Alert types"""
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    RSI_OVERSOLD = "rsi_oversold"
    RSI_OVERBOUGHT = "rsi_overbought"
    WHALE_ACTIVITY = "whale_activity"
    SOCIAL_SPIKE = "social_spike"
    BUY_SIGNAL = "buy_signal"
    SELL_SIGNAL = "sell_signal"
    PRICE_CHANGE = "price_change"


class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Recommendation(Enum):
    """Trading recommendations"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    WAIT = "wait"


@dataclass
class User:
    """User model"""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_premium: bool = False
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    
    # Subscription
    subscription_expires: Optional[datetime] = None
    
    # Settings
    notify_on_signal: bool = True
    notify_on_whale: bool = True
    notify_on_price_alert: bool = True
    default_alert_tolerance: float = 5.0  # %


@dataclass
class WatchedToken:
    """Token being watched by user"""
    id: int = 0
    user_id: int = 0
    token_symbol: str = ""
    token_name: str = ""
    
    added_at: datetime = field(default_factory=datetime.utcnow)
    
    # Track price changes
    entry_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    
    # Current state
    current_price: Optional[float] = None
    price_change_24h: float = 0.0
    
    # Analysis
    last_analysis: Optional[datetime] = None
    last_recommendation: Optional[Recommendation] = None
    last_confidence: float = 0.0
    
    # Auto-monitor settings
    auto_monitor: bool = True
    alert_on_signal: bool = True


@dataclass
class PriceAlert:
    """Price alert configuration"""
    id: int = 0
    user_id: int = 0
    token_symbol: str = ""
    
    alert_type: AlertType = AlertType.PRICE_ABOVE
    target_value: float = 0.0  # Price or percentage
    
    status: AlertStatus = AlertStatus.ACTIVE
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    triggered_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    message: Optional[str] = None


@dataclass
class TradingSignal:
    """Trading signal from analysis"""
    id: int = 0
    token_symbol: str = ""
    token_name: str = ""
    
    recommendation: Recommendation = Recommendation.HOLD
    confidence: float = 0.0
    
    # Prices
    entry_price: float = 0.0
    target_price: float = 0.0
    stop_loss: float = 0.0
    
    # Analysis breakdown
    ai_score: float = 0.0
    social_score: float = 0.0
    whale_score: float = 0.0
    technical_score: float = 0.0
    volume_score: float = 0.0
    
    # Additional info
    rationale: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    
    # Status
    status: str = "active"  # active, triggered, expired, cancelled
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    triggered_at: Optional[datetime] = None
    
    @property
    def risk_ratio(self) -> float:
        """Calculate risk/reward ratio"""
        if self.stop_loss == 0 or self.entry_price == 0:
            return 0.0
        
        potential_loss = abs(self.entry_price - self.stop_loss) / self.entry_price * 100
        potential_gain = abs(self.target_price - self.entry_price) / self.entry_price * 100
        
        if potential_loss == 0:
            return 0.0
        
        return potential_gain / potential_loss
    
    @property
    def emoji(self) -> str:
        """Get emoji for recommendation"""
        mapping = {
            Recommendation.BUY: "🟢",
            Recommendation.SELL: "🔴",
            Recommendation.HOLD: "🟡",
            Recommendation.WAIT: "⚪"
        }
        return mapping.get(self.recommendation, "❓")
    
    def to_message(self) -> str:
        """Format as Telegram message"""
        lines = [
            f"{self.emoji} *СИГНАЛ: {self.recommendation.value.upper()}*",
            f"📊 {self.token_symbol} ({self.token_name})\n",
            f"💰 Цена входа: ${self.entry_price:,.6f}",
            f"📈 Цель: ${self.target_price:,.6f} (+{abs((self.target_price/self.entry_price-1)*100):.1f}%)",
            f"🛑 Стоп-лосс: ${self.stop_loss:,.6f} ({abs((self.stop_loss/self.entry_price-1)*100):.1f}%)",
            f"⚖️ Риск/Награда: {self.risk_ratio:.2f}",
            f"\n📊 Уверенность: {self.confidence:.0f}%",
        ]
        
        if self.rationale:
            lines.append(f"\n💡 *Обоснование:*")
            for r in self.rationale[:3]:
                lines.append(f"• {r}")
        
        if self.risks:
            lines.append(f"\n⚠️ *Риски:*")
            for r in self.risks[:2]:
                lines.append(f"• {r}")
        
        lines.extend([
            f"\n🕐 Время: {self.created_at.strftime('%H:%M %d.%m.%Y')}",
            f"⚠️ Это не финансовая рекомендация!"
        ])
        
        return "\n".join(lines)
