"""
Background Monitor - Continuously monitors tokens and sends alerts 24/7
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
    Background monitor that runs 24/7:
    - Checks watched tokens every 15 minutes
    - Generates trading signals
    - Sends alerts to users when BUY/SELL detected
    """
    
    def __init__(
        self,
        db: DatabaseManager,
        alert_callback: Callable,
        check_interval: int = 900  # 15 minutes
    ):
        self.db = db
        self.alert_callback = alert_callback
        self.check_interval = check_interval
        
        self.agent = CryptoIntelligenceAgent()
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        
        # Track last signals to avoid duplicates
        self._last_signals: Dict[str, datetime] = {}
        self._signal_cooldown = timedelta(minutes=30)  # 30 min between same signals
        
        # Alert user IDs who want notifications
        self._subscribed_users: List[int] = []
    
    async def start(self):
        """Start the background monitor"""
        if self.is_running:
            logger.warning("Monitor already running")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Background monitor started - checking every 15 minutes")
    
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
        """Main monitoring loop - runs 24/7"""
        while self.is_running:
            try:
                logger.info("🔄 [MONITOR] Starting market scan...")
                
                # Load subscribed users
                await self._load_subscribed_users()
                
                # Check all watched tokens
                await self._check_all_tokens()
                
                # Send daily summary to subscribed users
                await self._send_daily_summary()
                
            except Exception as e:
                logger.error(f"Monitor error: {e}")
            
            # Sleep for 15 minutes
            logger.info(f"💤 [MONITOR] Next scan in {self.check_interval//60} minutes")
            await asyncio.sleep(self.check_interval)
    
    async def _load_subscribed_users(self):
        """Load users who want notifications"""
        try:
            # Get all users who have notifications enabled
            # For now, we'll track this in memory
            pass
        except Exception as e:
            logger.error(f"Error loading users: {e}")
    
    async def _check_all_tokens(self):
        """Check all watched tokens and send alerts if needed"""
        try:
            watched_tokens = await self.db.get_all_watched_tokens()
            
            if not watched_tokens:
                logger.info("[MONITOR] No watched tokens")
                return
            
            logger.info(f"[MONITOR] Checking {len(watched_tokens)} watched tokens...")
            
            buy_signals = []
            sell_signals = []
            
            for token in watched_tokens:
                try:
                    result = await self.agent.execute(token=token.token_symbol)
                    
                    if result.success:
                        rec_data = result.data.get("recommendation", {})
                        recommendation = rec_data.get("action", "WAIT")
                        confidence = rec_data.get("confidence", 0)
                        current_price = result.data.get("price")
                        
                        # Update token
                        await self.db.update_watched_token(
                            token.id,
                            current_price=current_price,
                            last_analysis=datetime.utcnow(),
                            last_recommendation=recommendation.upper(),
                            last_confidence=confidence
                        )
                        
                        # Check for BUY/SELL signals
                        if recommendation in ["BUY", "SELL"] and token.alert_on_signal:
                            signal_key = f"{token.token_symbol}_{recommendation}"
                            last_time = self._last_signals.get(signal_key)
                            
                            if last_time is None or datetime.utcnow() - last_time > self._signal_cooldown:
                                # Send alert to user
                                if self.alert_callback:
                                    await self._send_signal_alert(token, result.data)
                                
                                self._last_signals[signal_key] = datetime.utcnow()
                                
                                if recommendation == "BUY":
                                    buy_signals.append(token.token_symbol)
                                else:
                                    sell_signals.append(token.token_symbol)
                    
                    await asyncio.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"[MONITOR] Error checking {token.token_symbol}: {e}")
            
            # Clean up analyzers
            for key in self.agent.analyzers:
                analyzer = self.agent.analyzers[key]
                if hasattr(analyzer, 'close'):
                    await analyzer.close()
            
            # Log summary
            if buy_signals or sell_signals:
                logger.info(f"[MONITOR] Signals found - BUY: {buy_signals}, SELL: {sell_signals}")
            else:
                logger.info("[MONITOR] No new signals")
                    
        except Exception as e:
            logger.error(f"[MONITOR] Error in check_all_tokens: {e}")
    
    async def _send_signal_alert(self, token: WatchedToken, analysis_data: Dict):
        """Send signal alert to user via Telegram"""
        try:
            rec_data = analysis_data.get("recommendation", {})
            recommendation = rec_data.get("action", "WAIT")
            confidence = rec_data.get("confidence", 0)
            rationale = rec_data.get("rationale", [])
            current_price = analysis_data.get("price", 0)
            
            emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡", "WAIT": "⚪"}
            e = emoji.get(recommendation, "⚪")
            
            stop_loss = current_price * 0.95 if current_price else 0
            take_profit = current_price * 1.20 if confidence > 50 else current_price * 1.15
            
            message = f"""🔔 *СИГНАЛ ОТ БОТА!*

{e} *{recommendation}* — {token.token_symbol}

💰 Текущая цена: ${current_price:,.6f}
📈 Уверенность: {confidence:.0f}%

📐 *Торговые уровни:*
• Вход: ${current_price:,.6f}
• 📈 TP: ${take_profit:,.6f} (+{((take_profit/current_price)-1)*100:.1f}% если достижимо)
• 🛑 SL: ${stop_loss:,.6f}

💡 *Почему {recommendation}:*
"""
            for r in rationale[:3]:
                message += f"• {r}\n"
            
            message += """
━━━━━━━━━━━━━━━
⚠️ Это аналитический сигнал, не финансовая рекомендация!
🕐 """ + datetime.utcnow().strftime("%H:%M %d.%m.%Y")
            
            # Send via callback
            if self.alert_callback:
                await self.alert_callback(token.user_id, message)
            
            logger.info(f"[MONITOR] Sent {recommendation} alert to user {token.user_id} for {token.token_symbol}")
            
        except Exception as e:
            logger.error(f"[MONITOR] Error sending alert: {e}")
    
    async def _send_daily_summary(self):
        """Send daily summary to all active users"""
        try:
            # This would send a daily report
            # For now, just log
            logger.info("[MONITOR] Daily summary sent")
        except Exception as e:
            logger.error(f"[MONITOR] Error sending daily summary: {e}")
    
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
                # Update user's watched token if exists
                token = await self.db.get_watched_token(user_id, symbol)
                if token:
                    await self.db.update_watched_token(
                        token.id,
                        current_price=result.data.get("price"),
                        last_analysis=datetime.utcnow(),
                        last_recommendation=result.data.get("recommendation", {}).get("action", "HOLD"),
                        last_confidence=result.data.get("recommendation", {}).get("confidence", 0)
                    )
                
                # Clean up
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
        
        if recommendation in ["BUY", "HOLD"] and current_price:
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
