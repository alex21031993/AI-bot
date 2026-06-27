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
class Recommendation:
    """Trading recommendation based on analysis"""
    action: str  # BUY, SELL, HOLD, WAIT
    confidence: float  # 0-100%
    rationale: List[str] = field(default_factory=list)
    entry_target: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    @property
    def emoji(self) -> str:
        """Get emoji for action"""
        mapping = {
            "BUY": "🟢",
            "SELL": "🔴",
            "HOLD": "🟡",
            "WAIT": "⚪"
        }
        return mapping.get(self.action, "❓")
    
    @property
    def color_hex(self) -> str:
        """Get color for action"""
        mapping = {
            "BUY": "#00C853",
            "SELL": "#D50000",
            "HOLD": "#FFD600",
            "WAIT": "#9E9E9E"
        }
        return mapping.get(self.action, "#9E9E9E")


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
    recommendation: Recommendation = field(default_factory=lambda: Recommendation("WAIT", 0))
    
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
            "recommendation": {
                "action": self.recommendation.action,
                "confidence": self.recommendation.confidence,
                "rationale": self.recommendation.rationale,
                "entry_target": self.recommendation.entry_target,
                "stop_loss": self.recommendation.stop_loss,
                "take_profit": self.recommendation.take_profit
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
        
        # Recommendation block
        rec_emoji = self.recommendation.emoji
        rec_action = self.recommendation.action
        
        lines = [
            f"📊 *Анализ токена: {self.token.upper()}*\n",
            f"{rec_emoji} *РЕКОМЕНДАЦИЯ: {rec_action}* (Уверенность: {self.recommendation.confidence:.0f}%)\n",
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
        
        # Add trading levels if available
        if self.recommendation.stop_loss or self.recommendation.take_profit:
            lines.extend([f"\n📈 *Торговые уровни:*"])
            if self.recommendation.entry_target:
                lines.append(f"• Вход (Entry): ${self.recommendation.entry_target:,.6f}")
            if self.recommendation.take_profit:
                lines.append(f"• Тейк-профит (TP): ${self.recommendation.take_profit:,.6f}")
            if self.recommendation.stop_loss:
                lines.append(f"• Стоп-лосс (SL): ${self.recommendation.stop_loss:,.6f}")
        
        # Rationale
        if self.recommendation.rationale:
            lines.extend([f"\n💡 *Обоснование:*"])
            for r in self.recommendation.rationale[:3]:
                lines.append(f"• {r}")
        
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
            
            # Calculate recommendation
            report.recommendation = self._calculate_recommendation(scores, results, report)
            
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
    
    def _calculate_recommendation(
        self, 
        scores: CryptoScores, 
        results: Dict,
        report: CryptoReport
    ) -> Recommendation:
        """
        Calculate trading recommendation based on all indicators
        
        Logic:
        - BUY if strong indicators and favorable conditions
        - SELL if bearish signals dominate
        - HOLD if mixed signals
        - WAIT if insufficient data or extreme risk
        """
        rationale = []
        current_price = report.price or 0
        
        # Count positive and negative signals
        positive_signals = 0
        negative_signals = 0
        
        # Social analysis
        social = results.get("social", {})
        if social.get("mentions_growth_24h", 0) > 30:
            positive_signals += 1
            rationale.append("Рост упоминаний в соцсетях")
        elif social.get("mentions_growth_24h", 0) < -20:
            negative_signals += 1
            rationale.append("Падение интереса в соцсетях")
        
        # Whale analysis - weighted more heavily
        whale = results.get("whale", {})
        if whale.get("accumulation_score", 0) > 50:
            positive_signals += 2
            rationale.append("Аккумуляция китов")
        if whale.get("large_buys", 0) > whale.get("large_sells", 0):
            positive_signals += 1
            rationale.append("Преобладание крупных покупок")
        if whale.get("distribution_score", 0) > 50:
            negative_signals += 2
            rationale.append("Дистрибуция китов - продают крупные")
        
        # Technical analysis
        tech = results.get("technical", {})
        indicators = tech.get("indicators", {})
        
        rsi = indicators.get("rsi")
        if rsi:
            if rsi < 35:
                positive_signals += 2
                rationale.append(f"RSI={rsi:.0f} перепродан")
            elif rsi > 70:
                negative_signals += 1
                rationale.append(f"RSI={rsi:.0f} перекуплен")
        
        macd_bullish = indicators.get("macd_bullish", False)
        macd_hist = indicators.get("macd_histogram", 0)
        
        if macd_bullish:
            positive_signals += 1
            rationale.append("MACD бычий")
        elif macd_hist < 0:
            negative_signals += 1
            rationale.append("MACD медвежий")
        
        volatility = indicators.get("volatility", 0.05)
        
        # Volume analysis - weighted more
        volume = results.get("volume", {})
        if volume.get("volume_spike"):
            positive_signals += 1
            rationale.append("Аномальный рост объема")
        if volume.get("volume_trend") == "increasing":
            positive_signals += 1
            rationale.append("Растущий объем")
        elif volume.get("volume_trend") == "decreasing":
            negative_signals += 1
            rationale.append("Падающий объем")
        
        # Sentiment analysis
        sentiment = results.get("sentiment", {})
        if sentiment.get("bullish_ratio", 0) > 0.55:
            positive_signals += 1
            rationale.append("Бычьи настроения")
        elif sentiment.get("bearish_ratio", 0) > 0.55:
            negative_signals += 1
            rationale.append("Медвежьи настроения")
        
        # Calculate signal-based confidence
        total_signals = positive_signals + negative_signals
        if total_signals > 0:
            signal_confidence = (positive_signals / total_signals) * 100
        else:
            signal_confidence = 50
        
        # Use only signal confidence if social score is 0 (no Twitter API)
        # This gives better recommendations without Twitter data
        if scores.social_score < 1:
            final_confidence = signal_confidence
        else:
            final_confidence = (scores.total_score * 0.6 + signal_confidence * 0.4)
        
        # Determine action based on score and signals
        # Use available scores (excluding social if 0)
        available_score = scores.total_score
        if scores.social_score < 1:
            # Recalculate without social
            available_score = (
                scores.sentiment_score * 0.20 +
                scores.whale_score * 0.30 +
                scores.technical_score * 0.25 +
                scores.volume_score * 0.25
            )
        
        if available_score >= 60:
            if positive_signals > negative_signals:
                action = "BUY"
            elif negative_signals > positive_signals:
                action = "HOLD"
            else:
                action = "HOLD"
        elif available_score >= 45:
            if positive_signals > negative_signals + 1:
                action = "BUY"
            elif negative_signals > positive_signals + 1:
                action = "SELL"
            else:
                action = "HOLD"
        elif available_score >= 35:
            if positive_signals > negative_signals + 2:
                action = "BUY"
            elif negative_signals > positive_signals + 2:
                action = "SELL"
            else:
                action = "WAIT"
        else:  # < 35
            if negative_signals >= positive_signals:
                action = "SELL"
            else:
                action = "WAIT"
        
        # Calculate trading levels
        entry_target = None
        stop_loss = None
        take_profit = None
        
        if current_price > 0 and action in ["BUY", "HOLD"]:
            entry_target = current_price
            
            # Stop loss based on volatility
            stop_loss = current_price * (1 - max(0.05, volatility * 2))
            
            # Take profit based on confidence
            if final_confidence > 65:
                take_profit = current_price * 1.25
            elif final_confidence > 50:
                take_profit = current_price * 1.15
            else:
                take_profit = current_price * 1.10
        
        return Recommendation(
            action=action,
            confidence=final_confidence,
            rationale=rationale[:5],
            entry_target=entry_target,
            stop_loss=stop_loss,
            take_profit=take_profit
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
