"""
Advanced System Handlers - Telegram обработчики для Advanced System
"""
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger


class AdvancedHandlers:
    """Обработчики для Advanced System функций"""
    
    def __init__(self, button_bot):
        self.bot = button_bot
    
    async def show_meme_coins(self, query):
        """Показать результаты Meme Coin Scanner"""
        user_id = query.from_user.id
        
        await query.edit_message_text(
            "🌀 *MEME COIN SCANNER*\n\n"
            "🔍 Ищу мем-коины с потенциалом...\n"
            "⏳ Подождите..."
        )
        
        try:
            from crypto_intelligence_agent.scanner.meme_coin_scanner import MemeCoinScanner
            
            scanner = MemeCoinScanner()
            results = await asyncio.wait_for(
                scanner.scan_meme_coins(limit=10),
                timeout=60
            )
            await scanner.close()
            
            if results:
                report = scanner.format_report(results)
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Обновить", callback_data="scan_meme_refresh")],
                    [InlineKeyboardButton("🔙 Назад", callback_data="advanced_system")]
                ])
            else:
                report = "❌ Не удалось найти мем-коины. Попробуйте позже."
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="advanced_system")]
                ])
            
            await query.edit_message_text(report, parse_mode="Markdown", reply_markup=keyboard)
            
        except asyncio.TimeoutError:
            await query.edit_message_text(
                "❌ Таймаут. CoinGecko API перегружен.\n\n"
                "Попробуйте через несколько минут.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="advanced_system")]
                ])
            )
        except Exception as e:
            logger.error(f"Meme coins error: {e}")
            await query.edit_message_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="advanced_system")]
                ])
            )
    
    async def show_rug_check(self, query):
        """Показать Rug Pull Detector форму"""
        user_id = query.from_user.id
        
        text = """🛡️ *RUG PULL DETECTOR*
━━━━━━━━━━━━━━━━━━━━━━━━

Введите символ монеты для проверки
или выберите из популярных:

"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 BTC", callback_data="rugcheck_btc"),
             InlineKeyboardButton("🔍 ETH", callback_data="rugcheck_eth"),
             InlineKeyboardButton("🔍 SOL", callback_data="rugcheck_sol")],
            [InlineKeyboardButton("🔍 DOGE", callback_data="rugcheck_doge"),
             InlineKeyboardButton("🔍 SHIB", callback_data="rugcheck_shib"),
             InlineKeyboardButton("🔍 PEPE", callback_data="rugcheck_pepe")],
            [InlineKeyboardButton("🔙 Назад", callback_data="advanced_system")]
        ])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    
    async def perform_rug_check(self, query, token_id: str):
        """Выполнить проверку токена на rug pull"""
        await query.edit_message_text(
            f"🛡️ *Проверяю {token_id.upper()}...*\n\n"
            "🔍 Анализирую риски...\n"
            "⏳ Подождите..."
        )
        
        try:
            from crypto_intelligence_agent.scanner.rug_pull_detector import RugPullDetector
            
            detector = RugPullDetector()
            result = await asyncio.wait_for(
                detector.check_token(token_id),
                timeout=30
            )
            await detector.close()
            
            report = detector.format_report(result)
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Проверить другую", callback_data="show_rug_form")],
                [InlineKeyboardButton("🔙 Назад", callback_data="advanced_system")]
            ])
            
            await query.edit_message_text(report, parse_mode="Markdown", reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Rug check error: {e}")
            await query.edit_message_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="advanced_system")]
                ])
            )
    
    async def show_early_pumps(self, query):
        """Показать Early Pump Detector"""
        user_id = query.from_user.id
        
        await query.edit_message_text(
            "📈 *EARLY PUMP DETECTOR*\n\n"
            "🔍 Ищу ранние сигналы пампа...\n"
            "⏳ Подождите..."
        )
        
        try:
            from crypto_intelligence_agent.scanner.early_pump_detector import EarlyPumpDetector
            
            detector = EarlyPumpDetector()
            results = await asyncio.wait_for(
                detector.detect_pumps(limit=10),
                timeout=60
            )
            await detector.close()
            
            report = detector.format_report(results)
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data="scan_pumps_refresh")],
                [InlineKeyboardButton("🔙 Назад", callback_data="advanced_system")]
            ])
            
            await query.edit_message_text(report, parse_mode="Markdown", reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Early pumps error: {e}")
            await query.edit_message_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="advanced_system")]
                ])
            )
    
    async def show_smart_money(self, query, token_id: str = "bitcoin"):
        """Показать Smart Money Tracker"""
        await query.edit_message_text(
            f"🐋 *SMART MONEY TRACKER*\n\n"
            f"🔍 Анализирую {token_id.upper()}...\n"
            "⏳ Подождите..."
        )
        
        try:
            from crypto_intelligence_agent.scanner.smart_money_tracker import SmartMoneyTracker
            
            tracker = SmartMoneyTracker()
            result = await asyncio.wait_for(
                tracker.track_token(token_id),
                timeout=30
            )
            await tracker.close()
            
            report = tracker.format_report(result)
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🐋 BTC", callback_data="smartmoney_btc"),
                 InlineKeyboardButton("🐋 ETH", callback_data="smartmoney_eth"),
                 InlineKeyboardButton("🐋 SOL", callback_data="smartmoney_sol")],
                [InlineKeyboardButton("🔄 Другая монета", callback_data="smartmoney_other")],
                [InlineKeyboardButton("🔙 Назад", callback_data="advanced_system")]
            ])
            
            await query.edit_message_text(report, parse_mode="Markdown", reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Smart money error: {e}")
            await query.edit_message_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="advanced_system")]
                ])
            )
    
    async def show_entry_exit(self, query, token_id: str = "bitcoin"):
        """Показать AI Entry & Exit"""
        await query.edit_message_text(
            f"🧠 *AI ENTRY & EXIT*\n\n"
            f"🔍 Анализирую {token_id.upper()}...\n"
            "⏳ Подождите..."
        )
        
        try:
            from crypto_intelligence_agent.scanner.ai_entry_exit import AIEntryExitScanner
            
            scanner = AIEntryExitScanner()
            result = await asyncio.wait_for(
                scanner.analyze(token_id),
                timeout=30
            )
            await scanner.close()
            
            report = scanner.format_report(result)
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🧠 BTC", callback_data="entryexit_btc"),
                 InlineKeyboardButton("🧠 ETH", callback_data="entryexit_eth"),
                 InlineKeyboardButton("🧠 SOL", callback_data="entryexit_sol")],
                [InlineKeyboardButton("🔄 Другая монета", callback_data="entryexit_other")],
                [InlineKeyboardButton("🔙 Назад", callback_data="advanced_system")]
            ])
            
            await query.edit_message_text(report, parse_mode="Markdown", reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Entry/Exit error: {e}")
            await query.edit_message_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="advanced_system")]
                ])
            )