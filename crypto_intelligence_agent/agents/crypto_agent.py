"""
Crypto Intelligence Agent - Main agent for cryptocurrency analysis
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger

from .base_agent import BaseAgent, AgentResponse
from ..config.settings import SCORING_WEIGHTS, RISK_THRESHOLDS


@dataclass
class CryptoScores:
    """Individual scores for crypto analysis"""
    social_score: float = 0.0
    sentiment_score: float = 0.0
    whale_score: float = 0.0
    technical_score: float = 0.0
    volume_score: float = 0.0
    
    @property
    def total_score(self) -> float:
        """Calculate weighted total score"""
        return (
            self.social_score * SCORING_WEIGHTS.SOCIAL +
            self.sentiment_score * SCORING_WEIGHTS.SENTIMENT +
            self.whale_score * SCORING_WEIGHTS.WHALE +
            self.technical_score * SCORING_WEIGHTS.TECHNICAL +
            self.volume_score * SCORING_WEIGHTS.VOLUME
        )


@dataclass
class RiskAssessment:
    """Risk assessment result"""
    level: str  # HIGH, SPECULATIVE, PROMISING, STRONG
    description: str
    factors: List[str] = field(default_factory=list)
    
    @property
    def probability(self) -> str:
        """Get growth probability text"""
        mapping = {
            "HIGH": "Низкая",
            "SPECULATIVE": "Средняя",
            "PROMISING": "Высокая",
            "STRONG": "Очень высокая"
        }
        return mapping.get(self.level, "Неизвестно")


@dataclass
class CryptoReport:
    """Complete crypto analysis report"""
    token: str
    price: Optional[float] = None
    market_cap: Optional[float] = None
    liquidity: Optional[float] = None
    age_days: Optional[int] = None
    
    scores: CryptoScores = field(default_factory=CryptoScores)
    risk: RiskAssessment = field(default_factory=lambda: RiskAssessment("HIGH", ""))
    
    bullish_signals: List[str] = field(default_factory=list)
    bearish_signals: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "token": self.token,
            "price": self.price,
            "market_cap": self.market_cap,
            "liquidity": self.liquidity,
            "age_days": self.age_days,
            "scores": {
                "social_score": self.scores.social_score,
                "sentiment_score": self.scores.sentiment_score,
                "whale_score": self.scores.whale_score,
                "technical_score": self.scores.technical_score,
                "volume_score": self.scores.volume_score,
                "total": self.scores.total_score
            },
            "risk": {
                "level": self.risk.level,
                "description": self.risk.description,
                "probability": self.risk.probability
            },
            "bullish_signals": self.bullish_signals,
            "bearish_signals": self.bearish_signals,
            "risks": self.risks,
            "timestamp": self.timestamp.isoformat()
        }
    
    def to_telegram_message(self) -> str:
        """Format report for Telegram message"""
        emoji_map = {
            "STRONG": "🟢",
            "PROMISING": "🟡",
            "SPECULATIVE": "🟠",
            "HIGH": "🔴"
        }
        emoji = emoji_map.get(self.risk.level, "⚪")
        
        lines = [
            f"📊 *Анализ токена: {self.token.upper()}*\n",
            f"{emoji} *AI Confidence Score: {self.scores.total_score:.1f}%*\n",
            f"📈 Риск: {self.risk.level} ({self.risk.probability} вероятность роста)\n",
            f"\n💰 *Рыночные данные:*",
            f"• Цена: ${self.price:,.6f}" if self.price else "• Цена: N/A",
            f"• Капитализация: ${self.market_cap:,.0f}" if self.market_cap else "",
            f"• Ликвидность: ${self.liquidity:,.0f}" if self.liquidity else "",
            f"• Возраст: {self.age_days} дней" if self.age_days else "",
            f"\n📊 *Оценки:*",
            f"• Social Score: {self.scores.social_score:.1f}/100",
            f"• Sentiment Score: {self.scores.sentiment_score:.1f}/100",
            f"• Whale Score: {self.scores.whale_score:.1f}/100",
            f"• Technical Score: {self.scores.technical_score:.1f}/100",
            f"• Volume Score: {self.scores.volume_score:.1f}/100",
        ]
        
        if self.bullish_signals:
            lines.extend([f"\n🟢 *Бычьи сигналы:*"])
            for signal in self.bullish_signals[:5]:
                lines.append(f"• {signal}")
        
        if self.risks:
            lines.extend([f"\n🔴 *Риски:*"])
            for risk in self.risks[:5]:
                lines.append(f"• {risk}")
        
        lines.extend([
            f"\n⚠️ *Дисклеймер:*",
            "• Это аналитический инструмент, а не финансовая рекомендация",
            "• Не гарантируем прибыль",
            f"• Анализ сделан: {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
        ])
        
        return "\n".join(filter(None, lines))


class CryptoIntelligenceAgent(BaseAgent):
    """
    Main agent for cryptocurrency intelligence analysis.
    Analyzes social media, whale activity, technical indicators,
    and market data to provide investment insights.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.analyzers = {}
        super().__init__("CryptoIntelligenceAgent", config)
    
    def setup(self) -> None:
        """Initialize all analyzers"""
        from ..analyzers.social_analyzer import SocialAnalyzer
        from ..analyzers.sentiment_analyzer import SentimentAnalyzer
        from ..analyzers.whale_analyzer import WhaleAnalyzer
        from ..analyzers.technical_analyzer import TechnicalAnalyzer
        from ..analyzers.volume_analyzer import VolumeAnalyzer
        
        self.analyzers = {
            "social": SocialAnalyzer(self.config.get("social")),
            "sentiment": SentimentAnalyzer(self.config.get("sentiment")),
            "whale": WhaleAnalyzer(self.config.get("whale")),
            "technical": TechnicalAnalyzer(self.config.get("technical")),
            "volume": VolumeAnalyzer(self.config.get("volume"))
        }
        
        self.logger.info(f"Loaded {len(self.analyzers)} analyzers")
    
    async def execute(self, token: str, **kwargs) -> AgentResponse:
        """Execute full crypto analysis"""
        try:
            self.logger.info(f"Analyzing token: {token}")
            
            # Collect all scores
            scores = CryptoScores()
            report = CryptoReport(token=token)
            
            # Run all analyzers in parallel
            import asyncio
            
            tasks = {
                "social": self.analyzers["social"].analyze(token),
                "sentiment": self.analyzers["sentiment"].analyze(token),
                "whale": self.analyzers["whale"].analyze(token),
                "technical": self.analyzers["technical"].analyze(token),
                "volume": self.analyzers["volume"].analyze(token)
            }
            
            results = {}
            for key, task in tasks.items():
                try:
                    results[key] = await task
                except Exception as e:
                    self.logger.error(f"Error in {key} analyzer: {e}")
                    results[key] = {"score": 0, "error": str(e)}
            
            # Update scores
            scores.social_score = results.get("social", {}).get("score", 0)
            scores.sentiment_score = results.get("sentiment", {}).get("score", 0)
            scores.whale_score = results.get("whale", {}).get("score", 0)
            scores.technical_score = results.get("technical", {}).get("score", 0)
            scores.volume_score = results.get("volume", {}).get("score", 0)
            
            # Build report
            report.scores = scores
            report.price = results.get("technical", {}).get("price")
            report.market_cap = results.get("technical", {}).get("market_cap")
            report.liquidity = results.get("volume", {}).get("liquidity")
            
            # Calculate risk
            report.risk = self._calculate_risk(scores, results)
            
            # Add signals
            report.bullish_signals = self._extract_bullish_signals(results)
            report.risks = self._extract_risks(results)
            
            return AgentResponse(
                success=True,
                data=report.to_dict()
            )
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return AgentResponse(
                success=False,
                error=str(e)
            )
    
    def _calculate_risk(self, scores: CryptoScores, results: Dict) -> RiskAssessment:
        """Calculate risk level based on scores"""
        total = scores.total_score
        
        if total <= RISK_THRESHOLDS.HIGH_RISK_MAX:
            level = "HIGH"
            desc = "Высокий риск - возможна потеря инвестиций"
        elif total <= RISK_THRESHOLDS.SPECULATIVE_MAX:
            level = "SPECULATIVE"
            desc = "Спекулятивный актив - высокая волатильность"
        elif total <= RISK_THRESHOLDS.PROMISING_MAX:
            level = "PROMISING"
            desc = "Перспективный актив - есть потенциал роста"
        else:
            level = "STRONG"
            desc = "Сильный сигнал - обнаружены значимые индикаторы"
        
        return RiskAssessment(
            level=level,
            description=desc,
            factors=[]
        )
    
    def _extract_bullish_signals(self, results: Dict) -> List[str]:
        """Extract bullish signals from results"""
        signals = []
        
        # Check social signals
        social = results.get("social", {})
        if social.get("mentions_growth", 0) > 50:
            signals.append(f"Рост упоминаний: +{social.get('mentions_growth')}%")
        if social.get("viral_score", 0) > 70:
            signals.append("Вирусное распространение в соцсетях")
            
        # Check whale signals
        whale = results.get("whale", {})
        if whale.get("accumulation_signals", 0) > 3:
            signals.append("Обнаружена аккумуляция китов")
        if whale.get("large_buys", 0) > whale.get("large_sells", 0):
            signals.append("Преобладание крупных покупок")
            
        # Check technical signals
        tech = results.get("technical", {})
        if tech.get("rsi") and tech["rsi"] < 35:
            signals.append("RSI указывает на перепроданность")
        if tech.get("macd_bullish", False):
            signals.append("MACD показал бычий сигнал")
            
        # Check volume signals
        volume = results.get("volume", {})
        if volume.get("volume_spike", False):
            signals.append("Аномальный рост объема торгов")
            
        return signals[:5]  # Limit to top 5
    
    def _extract_risks(self, results: Dict) -> List[str]:
        """Extract risk factors from results"""
        risks = []
        
        # Check social risks
        social = results.get("social", {})
        if social.get("negative_sentiment_ratio", 0) > 0.5:
            risks.append("Преобладание негативных настроений")
            
        # Check whale risks
        whale = results.get("whale", {})
        if whale.get("distribution_signals", 0) > 3:
            risks.append("Обнаружена дистрибуция китов")
        if whale.get("dumping_risk", False):
            risks.append("Риск дампа от крупных держателей")
            
        # Check technical risks
        tech = results.get("technical", {})
        if tech.get("rsi") and tech["rsi"] > 75:
            risks.append("RSI указывает на перекупленность")
        if tech.get("high_volatility", False):
            risks.append("Высокая волатильность")
            
        # Check volume risks
        volume = results.get("volume", {})
        if volume.get("low_liquidity", False):
            risks.append("Низкая ликвидность")
            
        return risks[:5]  # Limit to top 5
    
    def validate_input(self, **kwargs) -> bool:
        """Validate token input"""
        token = kwargs.get("token")
        if not token:
            return False
        if not isinstance(token, str):
            return False
        if len(token) < 2 or len(token) > 20:
            return False
        return True
