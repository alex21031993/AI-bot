"""
Telegram Bot - User interface for Crypto Intelligence Agent
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from ..agents.crypto_agent import CryptoIntelligenceAgent, CryptoReport
from ..subscription.manager import SubscriptionManager
from ..config.settings import TELEGRAM_CONFIG


@dataclass
class BotConfig:
    """Bot configuration"""
    token: str
    admin_ids: List[int] = None
    demo_mode: bool = False
    
    def __post_init__(self):
        if self.admin_ids is None:
            self.admin_ids = []


class CryptoIntelligenceBot:
    """
    Telegram bot for Crypto Intelligence Agent
    
    Commands:
    /analyze - Full token analysis
    /social - Social media analysis
    /whales - Whale activity analysis
    /sentiment - Sentiment analysis
    /history - Token history
    /trend - Current trends
    /report - Full report
    
    Subscription:
    /subscribe - Subscribe to premium
    /status - Check subscription status
    """
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.agent = CryptoIntelligenceAgent()
        self.subscription_manager = SubscriptionManager()
        self.logger = logging.getLogger(__name__)
        
        # Track user requests
        self.user_requests: Dict[int, int] = {}  # user_id -> count
        
        # Message cache for reports
        self.report_cache: Dict[str, CryptoReport] = {}
    
    def create_keyboard(self, token: Optional[str] = None) -> InlineKeyboardMarkup:
        """Create main menu keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("📊 Полный анализ", callback_data=f"analyze_{token or ''}"),
                InlineKeyboardButton("📱 Соцсети", callback_data=f"social_{token or ''}")
            ],
            [
                InlineKeyboardButton("🐋 Киты", callback_data=f"whales_{token or ''}"),
                InlineKeyboardButton("💭 Настроения", callback_data=f"sentiment_{token or ''}")
            ],
            [
                InlineKeyboardButton("📜 История", callback_data=f"history_{token or ''}"),
                InlineKeyboardButton("📈 Тренды", callback_data=f"trend_{token or ''}")
            ],
            [
                InlineKeyboardButton("📋 Полный отчет", callback_data=f"report_{token or ''}")
            ],
            [
                InlineKeyboardButton("💎 Подписка", callback_data="subscribe"),
                InlineKeyboardButton("📋 Статус", callback_data="status")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        
        welcome_message = """
🐋 *Crypto Intelligence Agent*

Привет! Я анализирую криптовалюты и помогаю находить перспективные активы.

📊 *Что я умею:*
• Анализ социальных сетей
• Отслеживание китов
• Анализ настроений
• Технический анализ
• Оценка рисков

💎 *Подписки:*
• TRIAL - 5 дней за $2.99
• STANDARD - 7 дней за $4.99  
• PREMIUM - 30 дней за $14.99

⚠️ *Важно:*
Это аналитический инструмент, а не финансовая рекомендация!

Введите название токена для начала анализа.
        """
        
        await update.message.reply_text(
            welcome_message,
            parse_mode="Markdown",
            reply_markup=self.create_keyboard()
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📖 *Справка по командам:*

`/analyze <TOKEN>` - Полный анализ токена
`/social <TOKEN>` - Анализ социальных сетей
`/whales <TOKEN>` - Анализ активности китов
`/sentiment <TOKEN>` - Анализ настроений
`/history <TOKEN>` - История монеты
`/trend <TOKEN>` - Тренды
`/report <TOKEN>` - Полный отчет

`/subscribe` - Оформить подписку
`/status` - Проверить статус подписки

💡 *Примеры:*
`/analyze BTC`
`/analyze ETH`
`/analyze solana`

⚠️ Это не финансовая рекомендация!
        """
        
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analyze command"""
        user_id = update.effective_user.id
        
        # Get token from context
        if not context.args:
            await update.message.reply_text(
                "❌ Укажите токен для анализа.\n\n"
                "Пример: `/analyze BTC`",
                parse_mode="Markdown"
            )
            return
        
        token = context.args[0].upper()
        
        # Check subscription
        if not await self._check_subscription(update, user_id):
            return
        
        # Check request limit
        if not await self._check_request_limit(user_id):
            return
        
        # Show typing indicator
        await update.message.reply_text(f"🔍 Анализирую {token}...")
        
        try:
            # Run analysis
            response = await self.agent.execute(token=token)
            
            if response.success and response.data:
                report = self._create_report_from_data(response.data)
                message = report.to_telegram_message()
                
                await update.message.reply_text(
                    message,
                    parse_mode="Markdown",
                    reply_markup=self.create_keyboard(token)
                )
            else:
                await update.message.reply_text(
                    f"❌ Не удалось проанализировать {token}.\n"
                    f"Попробуйте позже."
                )
                
        except Exception as e:
            self.logger.error(f"Analysis error: {e}")
            await update.message.reply_text(
                f"❌ Произошла ошибка при анализе.\n"
                f"Попробуйте позже."
            )
    
    async def social_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /social command"""
        if not context.args:
            await update.message.reply_text(
                "❌ Укажите токен.\nПример: `/social BTC`",
                parse_mode="Markdown"
            )
            return
        
        token = context.args[0].upper()
        await update.message.reply_text(f"📱 Анализирую соцсети для {token}...")
        
        try:
            from ..analyzers.social_analyzer import SocialAnalyzer
            analyzer = SocialAnalyzer()
            result = await analyzer.analyze(token)
            
            if result.get("success"):
                metrics = result.get("metrics", {})
                
                message = f"""
📱 *Social Analysis: {token}*

🔢 *Упоминания:*
• Twitter: {metrics.get('twitter_mentions', 0)}
• Reddit: {metrics.get('reddit_mentions', 0)}
• Telegram: {metrics.get('telegram_members', 0):,}

📈 *Рост:*
• 24h: {metrics.get('mentions_growth_24h', 0):.1f}%
• 7d: {metrics.get('mentions_growth_7d', 0):.1f}%

💬 *Вовлеченность:*
• Engagement Rate: {metrics.get('engagement_rate', 0):.1f}%
• Influencers: {metrics.get('influencer_count', 0)}

🔥 *Viral Score: {result.get('score', 0):.0f}/100*
                """
                
                await update.message.reply_text(
                    message,
                    parse_mode="Markdown",
                    reply_markup=self.create_keyboard(token)
                )
            else:
                await update.message.reply_text("❌ Не удалось получить данные.")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    async def whales_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /whales command"""
        if not context.args:
            await update.message.reply_text(
                "❌ Укажите токен.\nПример: `/whales BTC`",
                parse_mode="Markdown"
            )
            return
        
        token = context.args[0].upper()
        await update.message.reply_text(f"🐋 Анализирую китов для {token}...")
        
        try:
            from ..analyzers.whale_analyzer import WhaleAnalyzer
            analyzer = WhaleAnalyzer()
            result = await analyzer.analyze(token)
            
            if result.get("success"):
                data = result.get("data", {})
                
                message = f"""
🐋 *Whale Analysis: {token}*

💰 *Активность:*
• Крупных транзакций: {data.get('large_transactions', 0)}
• Объем: ${data.get('total_whale_volume_usd', 0):,.0f}

📊 *Покупки/Продажи:*
• 🟢 Покупки: {data.get('large_buys', 0)}
• 🔴 Продажи: {data.get('large_sells', 0)}

📈 *Индикаторы:*
• Accumulation Score: {data.get('accumulation_score', 0):.0f}
• Distribution Score: {data.get('distribution_score', 0):.0f}
• Новые кошельки: {data.get('new_wallets', 0)}

🏆 *Whale Score: {result.get('score', 0):.0f}/100*
{result.get('whale_score_label', '')}
                """
                
                await update.message.reply_text(
                    message,
                    parse_mode="Markdown",
                    reply_markup=self.create_keyboard(token)
                )
            else:
                await update.message.reply_text("❌ Не удалось получить данные.")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    async def sentiment_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /sentiment command"""
        if not context.args:
            await update.message.reply_text(
                "❌ Укажите токен.\nПример: `/sentiment BTC`",
                parse_mode="Markdown"
            )
            return
        
        token = context.args[0].upper()
        await update.message.reply_text(f"💭 Анализирую настроения для {token}...")
        
        try:
            from ..analyzers.sentiment_analyzer import SentimentAnalyzer
            analyzer = SentimentAnalyzer()
            result = await analyzer.analyze(token)
            
            if result.get("success"):
                data = result.get("data", {})
                fg = data.get('fear_greed_index')
                
                message = f"""
💭 *Sentiment Analysis: {token}*

📊 *Настроение:* {result.get('label', 'N/A')}

📈 *Индикаторы:*
• 🟢 Бычий: {data.get('bullish_ratio', 0)*100:.1f}%
• 🔴 Медвежий: {data.get('bearish_ratio', 0)*100:.1f}%
• ⚪ Нейтральный: {data.get('neutral_ratio', 0)*100:.1f}%

😱 *Fear & Greed:*
{f'• Index: {fg}' if fg else '• Index: N/A'}

🎯 *Уровни:*
• FOMO: {data.get('fomo_level', 0):.0f}/100
• Hype: {data.get('hype_level', 0):.0f}/100

🏆 *Sentiment Score: {result.get('score', 0):.0f}/100*
                """
                
                await update.message.reply_text(
                    message,
                    parse_mode="Markdown",
                    reply_markup=self.create_keyboard(token)
                )
            else:
                await update.message.reply_text("❌ Не удалось получить данные.")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /history command"""
        if not context.args:
            await update.message.reply_text(
                "❌ Укажите токен.\nПример: `/history BTC`",
                parse_mode="Markdown"
            )
            return
        
        token = context.args[0].upper()
        
        message = f"""
📜 *История: {token}*

Этот модуль показывает:
• Дату запуска
• Историю цены
• Крупные события
• Разблокировки токенов
• Изменение держателей

⏳ *Скоро будет доступно в полной версии.*
        """
        
        await update.message.reply_text(message, parse_mode="Markdown")
    
    async def trend_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /trend command"""
        if context.args:
            token = context.args[0].upper()
            await update.message.reply_text(f"📈 Анализирую тренды для {token}...")
        else:
            await update.message.reply_text("📈 Анализирую общие тренды...")
        
        message = """
📈 *Тренды рынка*

🔍 *Анализ трендов включает:*
• Текущие тренды
• Новые монеты
• Пампы и дампы
• Социальные тренды

⏳ *Скоро будет доступно в полной версии.*
        """
        
        await update.message.reply_text(message, parse_mode="Markdown")
    
    async def report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /report command - same as analyze"""
        await self.analyze_command(update, context)
    
    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /subscribe command"""
        keyboard = [
            [
                InlineKeyboardButton("🎁 TRIAL - 5 дней ($2.99)", callback_data="sub_trial")
            ],
            [
                InlineKeyboardButton("⭐ STANDARD - 7 дней ($4.99)", callback_data="sub_standard")
            ],
            [
                InlineKeyboardButton("💎 PREMIUM - 30 дней ($14.99)", callback_data="sub_premium")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="back")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = """
💎 *Подписки Crypto Intelligence*

Выберите план:

🎁 **TRIAL** - $2.99
• 5 дней доступа
• До 10 запросов

⭐ **STANDARD** - $4.99
• 7 дней доступа
• До 50 запросов

💎 **PREMIUM** - $14.99
• 30 дней доступа
• Безлимитные запросы

⚠️ Оплата через криптокошелек
        """
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user_id = update.effective_user.id
        
        is_admin = user_id in self.config.admin_ids
        subscription = await self.subscription_manager.get_subscription(user_id)
        
        if is_admin:
            message = f"""
📋 *Ваш статус*

👑 **Администратор**
• Бесплатный доступ
• Безлимитные запросы
            """
        elif subscription:
            days_left = (subscription.expires_at - datetime.utcnow()).days
            
            message = f"""
📋 *Ваш статус*

💎 **Подписка:** {subscription.plan_name}
• Осталось дней: {days_left}
• Осталось запросов: {subscription.requests_remaining}
• Истекает: {subscription.expires_at.strftime('%Y-%m-%d')}
            """
        else:
            message = """
📋 *Ваш статус*

❌ Нет активной подписки

💡 Используйте `/subscribe` для оформления
            """
        
        await update.message.reply_text(message, parse_mode="Markdown")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        # Parse callback data
        if data.startswith("analyze_"):
            token = data.replace("analyze_", "").strip()
            if token:
                context.args = [token]
                await self.analyze_command(query, context)
            else:
                await query.edit_message_text("❌ Укажите токен")
        
        elif data.startswith("social_"):
            token = data.replace("social_", "").strip()
            if token:
                context.args = [token]
                await self.social_command(query, context)
        
        elif data.startswith("whales_"):
            token = data.replace("whales_", "").strip()
            if token:
                context.args = [token]
                await self.whales_command(query, context)
        
        elif data.startswith("sentiment_"):
            token = data.replace("sentiment_", "").strip()
            if token:
                context.args = [token]
                await self.sentiment_command(query, context)
        
        elif data.startswith("history_"):
            token = data.replace("history_", "").strip()
            if token:
                context.args = [token]
                await self.history_command(query, context)
        
        elif data.startswith("trend_"):
            token = data.replace("trend_", "").strip()
            if token:
                context.args = [token]
                await self.trend_command(query, context)
        
        elif data.startswith("report_"):
            token = data.replace("report_", "").strip()
            if token:
                context.args = [token]
                await self.report_command(query, context)
        
        elif data == "subscribe":
            context.args = []
            await self.subscribe_command(query, context)
        
        elif data == "status":
            context.args = []
            await self.status_command(query, context)
        
        elif data.startswith("sub_"):
            plan = data.replace("sub_", "")
            await self._handle_subscription(query, plan)
        
        elif data == "back":
            await query.edit_message_text(
                "🔙 Возвращаюсь в главное меню...",
                reply_markup=self.create_keyboard()
            )
    
    async def _handle_subscription(self, query, plan: str):
        """Handle subscription selection"""
        plan_messages = {
            "trial": "🎁 **TRIAL** - 5 дней за $2.99",
            "standard": "⭐ **STANDARD** - 7 дней за $4.99",
            "premium": "💎 **PREMIUM** - 30 дней за $14.99"
        }
        
        message = f"""
{plan_messages.get(plan, 'Неизвестный план')}

⚠️ Для оплаты используйте криптокошелек:

**Адрес для оплаты:**
`0x...` (требуется настройка)

После оплаты отправьте TX hash боту для верификации.
        """
        
        await query.edit_message_text(message, parse_mode="Markdown")
    
    async def _check_subscription(self, update: Update, user_id: int) -> bool:
        """Check if user has valid subscription"""
        # Admin bypass
        if user_id in self.config.admin_ids:
            return True
        
        subscription = await self.subscription_manager.get_subscription(user_id)
        
        if not subscription:
            await update.message.reply_text(
                "❌ У вас нет активной подписки.\n"
                "Используйте `/subscribe` для оформления."
            )
            return False
        
        if subscription.is_expired:
            await update.message.reply_text(
                "❌ Ваша подписка истекла.\n"
                "Используйте `/subscribe` для продления."
            )
            return False
        
        return True
    
    async def _check_request_limit(self, user_id: int) -> bool:
        """Check if user has remaining requests"""
        # Admin bypass
        if user_id in self.config.admin_ids:
            return True
        
        remaining = await self.subscription_manager.get_remaining_requests(user_id)
        
        if remaining <= 0:
            await self.subscription_manager.get_user_request_count(user_id)  # Just to update
            
            await update.message.reply_text(
                "❌ Достигнут лимит запросов.\n"
                "Обновите подписку или попробуйте завтра."
            )
            return False
        
        # Increment counter
        self.user_requests[user_id] = self.user_requests.get(user_id, 0) + 1
        await self.subscription_manager.increment_requests(user_id)
        
        return True
    
    def _create_report_from_data(self, data: Dict) -> CryptoReport:
        """Create CryptoReport from analysis data"""
        from ..agents.crypto_agent import CryptoScores, RiskAssessment
        
        scores = CryptoScores(
            social_score=data.get("scores", {}).get("social_score", 0),
            sentiment_score=data.get("scores", {}).get("sentiment_score", 0),
            whale_score=data.get("scores", {}).get("whale_score", 0),
            technical_score=data.get("scores", {}).get("technical_score", 0),
            volume_score=data.get("scores", {}).get("volume_score", 0)
        )
        
        risk_data = data.get("risk", {})
        risk = RiskAssessment(
            level=risk_data.get("level", "HIGH"),
            description=risk_data.get("description", ""),
            factors=risk_data.get("factors", [])
        )
        
        return CryptoReport(
            token=data.get("token", ""),
            price=data.get("price"),
            market_cap=data.get("market_cap"),
            liquidity=data.get("liquidity"),
            age_days=data.get("age_days"),
            scores=scores,
            risk=risk,
            bullish_signals=data.get("bullish_signals", []),
            risks=data.get("risks", [])
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages (token name)"""
        user_id = update.effective_user.id
        text = update.message.text.strip().upper()
        
        # Skip commands
        if text.startswith("/"):
            return
        
        # Treat as token name
        if len(text) >= 2 and len(text) <= 20:
            context.args = [text]
            await self.analyze_command(update, context)
        else:
            await update.message.reply_text(
                "❌ Неверный формат. Введите название токена (например: BTC, ETH)"
            )
    
    def run(self):
        """Start the bot"""
        application = Application.builder().token(self.config.token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("analyze", self.analyze_command))
        application.add_handler(CommandHandler("social", self.social_command))
        application.add_handler(CommandHandler("whales", self.whales_command))
        application.add_handler(CommandHandler("sentiment", self.sentiment_command))
        application.add_handler(CommandHandler("history", self.history_command))
        application.add_handler(CommandHandler("trend", self.trend_command))
        application.add_handler(CommandHandler("report", self.report_command))
        application.add_handler(CommandHandler("subscribe", self.subscribe_command))
        application.add_handler(CommandHandler("status", self.status_command))
        
        # Callback handler
        application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Message handler
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_message
        ))
        
        # Start polling
        print("🤖 Crypto Intelligence Bot starting...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
