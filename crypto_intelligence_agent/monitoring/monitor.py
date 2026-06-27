"""
Background Monitor - Continuously monitors tokens and sends alerts
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from loguru import logger

from ..database.models import TradingSignal, Recommendation, WatchedToken
from ..database.manager import DatabaseManager
from ..agents.crypto_agent import CryptoIntelligenceAgent


class BackgroundMonitor:
    """
    Background monitor that continuously:
    - Checks watched tokens
    - Generates trading signals
    - Sends alerts to users
    """
    
    def __init__(
        self,
        db: DatabaseManager,
        alert_callback: Callable,
        check_interval: int = 300
    ):
        self.db = db
        self.alert_callback = alert_callback
        self.check_interval = check_interval
        
        self.agent = CryptoIntelligenceAgent()
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        
        self._last_signals: Dict[str, datetime] = {}
        self._signal_cooldown = timedelta(hours=1)
    
    async def start(self):
        """Start the background monitor"""
        if self.is_running:
            logger.warning("Monitor already running")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Background monitor started")
    
    async def stop(self):
        """Stop the background monitor"""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Background monitor stopped")
    
    async def _run(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                await self._check_all_tokens()
                await self._cleanup_old_signals()
            except Exception as e:
                logger.error(f"Monitor error: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    async def _check_all_tokens(self):
        """Check all watched tokens and send alerts if needed"""
        try:
            watched_tokens = await self.db.get_all_watched_tokens()
            
            if not watched_tokens:
                return
            
            logger.info(f"Checking {len(watched_tokens)} watched tokens...")
            
            for token in watched_tokens:
                try:
                    await self._check_token(token)
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.error(f"Error checking {token.token_symbol}: {e}")
            
            for key in self.agent.analyzers:
                analyzer = self.agent.analyzers[key]
                if hasattr(analyzer, 'close'):
                    await analyzer.close()
                    
        except Exception as e:
            logger.error(f"Error in _check_all_tokens: {e}")
    
    async def _check_token(self, token: WatchedToken):
        """Check a single token and send alert if signal changed"""
        try:
            result = await self.agent.execute(token=token.token_symbol)
            
            if not result.success:
                return
            
            rec_data = result.data.get("recommendation", {})
            recommendation = rec_data.get("action", "WAIT")
            confidence = rec_data.get("confidence", 0)
            current_price = result.data.get("price")
            
            await self.db.update_watched_token(
                token.id,
                current_price=current_price,
                last_analysis=datetime.utcnow(),
                last_recommendation=recommendation.upper(),
                last_confidence=confidence
            )
            
            if token.alert_on_signal and recommendation in ["BUY", "SELL"]:
                signal_key = f"{token.token_symbol}_{recommendation}"
                last_time = self._last_signals.get(signal_key)
                
                if last_time is None or datetime.utcnow() - last_time > self._signal_cooldown:
                    await self._send_signal_alert(token, result.data)
                    self._last_signals[signal_key] = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error checking token {token.token_symbol}: {e}")
    
    async def _send_signal_alert(self, token: WatchedToken, analysis_data: Dict):
        """Send signal alert to user"""
        try:
            rec_data = analysis_data.get("recommendation", {})
            recommendation = rec_data.get("action", "WAIT")
            confidence = rec_data.get("confidence", 0)
            rationale = rec_data.get("rationale", [])
            current_price = analysis_data.get("price", 0)
            
            emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡", "WAIT": "⚪"}
            e = emoji.get(recommendation, "⚪")
            
            stop_loss = current_price * 0.95
            take_profit = current_price * 1.20 if confidence > 50 else current_price * 1.15
            
            message = f"""{e} *СИГНАЛ: {recommendation}*

📊 *{token.token_symbol}*

💰 Цена: ${current_price:,.6f}
📈 Уверенность: {confidence:.0f}%

📐 *Уровни:*
• Вход: ${current_price:,.6f}
• TP: ${take_profit:,.6f} (+{((take_profit/current_price)-1)*100:.1f}%)
• SL: ${stop_loss:,.6f} ({((stop_loss/current_price)-1)*100:.1f}%)

💡 *Обоснование:*
"""
            for r in rationale[:3]:
                message += f"• {r}\n"
            
            message += """

⚠️ Это не финансовая рекомендация!"""
            
            if self.alert_callback:
                await self.alert_callback(token.user_id, message)
            
            logger.info(f"Sent {recommendation} alert for {token.token_symbol} to user {token.user_id}")
            
        except Exception as e:
            logger.error(f"Error sending signal alert: {e}")
    
    async def _cleanup_old_signals(self):
        """Expire old signals"""
        try:
            await self.db.expire_old_signals(hours=24)
        except Exception as e:
            logger.error(f"Error cleaning up signals: {e}")
    
    async def manual_check(self, user_id: int, symbol: str) -> str:
        """Manually check a token and return analysis"""
        try:
            result = await self.agent.execute(token=symbol)
            
            if result.success:
                token = await self.db.get_watched_token(user_id, symbol)
                if token:
                    await self.db.update_watched_token(
                        token.id,
                        current_price=result.data.get("price"),
                        last_analysis=datetime.utcnow(),
                        last_recommendation=result.data.get("recommendation", {}).get("action", "HOLD"),
                        last_confidence=result.data.get("recommendation", {}).get("confidence", 0)
                    )
                
                for key in self.agent.analyzers:
                    analyzer = self.agent.analyzers[key]
                    if hasattr(analyzer, 'close'):
                        await analyzer.close()
                
                return self._format_analysis_result(symbol, result.data)
            else:
                return f"❌ Ошибка анализа: {result.error}"
                
        except Exception as e:
            logger.error(f"Error in manual_check: {e}")
            return f"❌ Ошибка: {str(e)}"
    
    def _format_analysis_result(self, symbol: str, data: Dict) -> str:
        """Format analysis result as message"""
        scores = data.get("scores", {})
        rec_data = data.get("recommendation", {})
        recommendation = rec_data.get("action", "WAIT")
        confidence = rec_data.get("confidence", 0)
        
        emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡", "WAIT": "⚪"}
        e = emoji.get(recommendation, "⚪")
        
        current_price = data.get("price", 0)
        
        lines = [
            f"📊 *Анализ: {symbol}*\n",
            f"{e} *РЕКОМЕНДАЦИЯ: {recommendation}* ({confidence:.0f}%)\n",
            f"💰 Цена: ${current_price:,.6f}\n",
            f"\n📊 *Оценки:*",
            f"• AI Score: {scores.get('total', 0):.1f}%",
            f"• Whale Score: {scores.get('whale_score', 0):.1f}%",
            f"• Technical: {scores.get('technical_score', 0):.1f}%",
            f"• Volume: {scores.get('volume_score', 0):.1f}%\n",
        ]
        
        rationale = rec_data.get("rationale", [])
        if rationale:
            lines.append("💡 *Обоснование:*")
            for r in rationale[:3]:
                lines.append(f"• {r}")
        
        if recommendation in ["BUY", "HOLD"]:
            tp = current_price * 1.20 if confidence > 50 else current_price * 1.15
            sl = current_price * 0.95
            lines.extend([
                f"\n📐 *Уровни:*",
                f"• Entry: ${current_price:,.6f}",
                f"• TP: ${tp:,.6f} (+{((tp/current_price)-1)*100:.1f}%)",
                f"• SL: ${sl:,.6f} ({((sl/current_price)-1)*100:.1f}%)"
            ])
        
        lines.extend([
            f"\n⚠️ Это не финансовая рекомендация!",
            f"🕐 {datetime.utcnow().strftime('%H:%M %d.%m.%Y')}"
        ])
        
        return "\n".join(lines)
