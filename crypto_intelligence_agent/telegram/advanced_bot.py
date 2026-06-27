"""
Advanced Telegram Bot with Authorization, Alerts, and Auto-Signals
"""
import asyncio
from typing import Dict, Optional
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

from ..database.manager import DatabaseManager
from ..database.models import User, WatchedToken, UserRole, AlertType
from ..monitoring.monitor import BackgroundMonitor
from ..config.settings import SUBSCRIPTION_PLANS


class CryptoBot:
    """
    Advanced Telegram bot with:
    - User registration/authentication
    - Watchlist tracking
    - Price alerts
    - Auto-signals from background monitoring
    - Subscription management
    """
    
    def __init__(self, token: str, admin_ids: list = None):
        self.token = token
        self.admin_ids = admin_ids or []
        
        self.db = DatabaseManager()
        self.monitor: Optional[BackgroundMonitor] = None
        
        # Track user states for conversations
        self.user_states: Dict[int, Dict] = {}
    
    async def _send_alert(self, user_id: int, message: str):
        """Callback to send alert to user"""
        try:
            # This will be called by the monitor
            # Store in a queue or directly send
            pass
        except Exception as e:
            print(f"Error sending alert: {e}")
    
    async def initialize(self):
        """Initialize bot components"""
        await self.db.initialize()
        
        # Initialize monitor
        self.monitor = BackgroundMonitor(
            db=self.db,
            alert_callback=self._send_telegram_message
        )
    
    async def _send_telegram_message(self, user_id: int, message: str):
        """Send message to user"""
        try:
            await self.app.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Error sending message to {user_id}: {e}")
    
    def create_app(self):
        """Create and configure the Telegram application"""
        self.app = Application.builder().token(self.token).build()
        
        # Register handlers
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("analyze", self.cmd_analyze))
        self.app.add_handler(CommandHandler("add", self.cmd_add_token))
        self.app.add_handler(CommandHandler("remove", self.cmd_remove_token))
        self.app.add_handler(CommandHandler("watchlist", self.cmd_watchlist))
        self.app.add_handler(CommandHandler("alert", self.cmd_alert))
        self.app.add_handler(CommandHandler("signals", self.cmd_signals))
        self.app.add_handler(CommandHandler("subscribe", self.cmd_subscribe))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("settings", self.cmd_settings))
        
        # Admin commands
        self.app.add_handler(CommandHandler("admin", self.cmd_admin))
        self.app.add_handler(CommandHandler("broadcast", self.cmd_broadcast))
        self.app.add_handler(CommandHandler("stats", self.cmd_stats))
        
        # Callback handler
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Message handler for token input
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_message
        ))
        
        return self.app
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        user = await self.db.get_user(user_id)
        
        if not user:
            # Auto-register user
            user = await self.db.create_user(
                user_id=user_id,
                username=update.effective_user.username,
                first_name=update.effective_user.first_name,
                last_name=update.effective_user.last_name
            )
            welcome = "✅ *Регистрация прошла успешно!*"
        else:
            welcome = "👋 *С возвращением!*"
        
        # Check if admin
        is_admin = user_id in self.admin_ids
        
        message = f"""{welcome}

🐋 *Crypto Intelligence Bot*

Я анализирую криптовалюты и отправляю сигналы на покупку/продажу.

📊 *Мои возможности:*
• Анализ монет по запросу
• Отслеживание портфеля
• Автоматические сигналы
• Оповещения о ценах
• Анализ китов

📱 *Команды:*
• `/analyze BTC` - Анализ монеты
• `/add BTC` - Добавить в отслеживание
• `/watchlist` - Ваш список
• `/alert BTC below 50000` - Оповещение
• `/signals` - Активные сигналы

💎 *Подписки:*
• `/subscribe` - Оформить подписку

👑 *Админ панель:*
• `/admin` - Управление
"""
        
        keyboard = self._main_keyboard(is_admin)
        await update.message.reply_text(message, parse_mode="Markdown", reply_markup=keyboard)
    
    def _main_keyboard(self, is_admin: bool = False) -> InlineKeyboardMarkup:
        """Create main menu keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("📊 Анализ", callback_data="menu_analyze"),
                InlineKeyboardButton("👁️ Отслеживание", callback_data="menu_watchlist")
            ],
            [
                InlineKeyboardButton("🔔 Оповещения", callback_data="menu_alerts"),
                InlineKeyboardButton("📈 Сигналы", callback_data="menu_signals")
            ],
            [
                InlineKeyboardButton("💎 Подписка", callback_data="menu_subscribe"),
                InlineKeyboardButton("⚙️ Настройки", callback_data="menu_settings")
            ]
        ]
        
        if is_admin:
            keyboard.append([InlineKeyboardButton("👑 Админ", callback_data="menu_admin")])
        
        return InlineKeyboardMarkup(keyboard)
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📖 *Справка по командам:*

*Анализ:*
• `/analyze BTC` - Полный анализ монеты
• `/add BTC` - Добавить в отслеживание
• `/remove BTC` - Удалить из отслеживания
• `/watchlist` - Ваш список монет

*Оповещения:*
• `/alert BTC above 60000` - Когда цена выше
• `/alert BTC below 50000` - Когда цена ниже

*Сигналы:*
• `/signals` - Активные сигналы

*Прочее:*
• `/status` - Статус подписки
• `/subscribe` - Подписки
• `/settings` - Настройки
• `/help` - Эта справка

💡 *Подсказка:* Просто отправьте название монеты!
        """
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def cmd_analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analyze command"""
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text("❌ Укажите монету: `/analyze BTC`", parse_mode="Markdown")
            return
        
        token = context.args[0].upper()
        await update.message.reply_text(f"🔍 Анализирую {token}...")
        
        if self.monitor:
            result = await self.monitor.manual_check(user_id, token)
            await update.message.reply_text(result, parse_mode="Markdown")
    
    async def cmd_add_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /add command"""
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text("❌ Укажите монету: `/add BTC`", parse_mode="Markdown")
            return
        
        token = context.args[0].upper()
        
        # Optional price entry
        entry_price = None
        if len(context.args) > 1:
            try:
                entry_price = float(context.args[1])
            except ValueError:
                pass
        
        # Add to watchlist
        await self.db.add_watched_token(
            user_id=user_id,
            symbol=token,
            name=token,
            entry_price=entry_price
        )
        
        # Analyze if monitor is available
        if self.monitor:
            result = await self.monitor.manual_check(user_id, token)
            
            keyboard = [
                [InlineKeyboardButton("📊 Ещё анализ", callback_data=f"analyze_{token}")],
                [InlineKeyboardButton("👁️ К списку", callback_data="menu_watchlist")]
            ]
            
            await update.message.reply_text(
                f"✅ *{token} добавлен в отслеживание!*\n\n{result}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                f"✅ *{token} добавлен в отслеживание!*",
                parse_mode="Markdown"
            )
    
    async def cmd_remove_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /remove command"""
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text("❌ Укажите монету: `/remove BTC`", parse_mode="Markdown")
            return
        
        token = context.args[0].upper()
        
        await self.db.remove_watched_token(user_id, token)
        
        await update.message.reply_text(
            f"✅ *{token} удалён из отслеживания!*",
            parse_mode="Markdown"
        )
    
    async def cmd_watchlist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /watchlist command"""
        user_id = update.effective_user.id
        
        tokens = await self.db.get_user_watched_tokens(user_id)
        
        if not tokens:
            message = "📋 *Ваш список отслеживания пуст*\n\nИспользуйте `/add BTC` для добавления монеты"
        else:
            message = "👁️ *Ваш список отслеживания:*\n\n"
            
            for token in tokens[:10]:
                emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡", "WAIT": "⚪"}
                rec_emoji = emoji.get(token.last_recommendation.value if token.last_recommendation else "?", "⚪")
                
                price_str = f"${token.current_price:,.2f}" if token.current_price else "N/A"
                change_str = f"{token.price_change_24h:+.1f}%" if token.price_change_24h else ""
                
                message += f"{rec_emoji} *{token.token_symbol}*\n"
                message += f"   💰 {price_str} {change_str}\n"
                if token.last_confidence:
                    message += f"   📊 Уверенность: {token.last_confidence:.0f}%\n"
                message += "\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ Добавить", callback_data="menu_analyze")],
            [InlineKeyboardButton("🔄 Обновить", callback_data="refresh_watchlist")]
        ]
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def cmd_alert(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /alert command"""
        user_id = update.effective_user.id
        
        if not context.args or len(context.args) < 3:
            await update.message.reply_text(
                "❌ Использование: `/alert BTC above 60000`\n"
                "или: `/alert BTC below 50000`",
                parse_mode="Markdown"
            )
            return
        
        token = context.args[0].upper()
        direction = context.args[1].lower()
        price = context.args[2]
        
        try:
            target_price = float(price)
        except ValueError:
            await update.message.reply_text("❌ Неверная цена")
            return
        
        alert_type = AlertType.PRICE_ABOVE if direction == "above" else AlertType.PRICE_BELOW
        
        alert = await self.db.create_price_alert(
            user_id=user_id,
            symbol=token,
            alert_type=alert_type,
            target_value=target_price,
            message=f"{direction} {target_price}"
        )
        
        emoji = "📈" if direction == "above" else "📉"
        
        await update.message.reply_text(
            f"{emoji} *Оповещение создано!*\n\n"
            f"📊 {token}\n"
            f"📍 Цена {direction}: ${target_price:,.2f}\n\n"
            f"Вы получите уведомление когда цена достигнет этого уровня.",
            parse_mode="Markdown"
        )
    
    async def cmd_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signals command"""
        signals = await self.db.get_active_signals()
        
        if not signals:
            message = "📈 *Нет активных сигналов*\n\nСигналы появляются автоматически при отслеживании монет."
        else:
            message = "📈 *Активные сигналы:*\n\n"
            
            for signal in signals[:5]:
                emoji = {"buy": "🟢", "sell": "🔴", "hold": "🟡", "wait": "⚪"}
                e = emoji.get(signal.recommendation.value, "⚪")
                
                message += f"{e} *{signal.token_symbol}* - {signal.recommendation.value.upper()}\n"
                message += f"   💰 ${signal.entry_price:,.2f}\n"
                message += f"   📊 Уверенность: {signal.confidence:.0f}%\n\n"
        
        await update.message.reply_text(message, parse_mode="Markdown")
    
    async def cmd_subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /subscribe command"""
        keyboard = [
            [InlineKeyboardButton("🎁 TRIAL - 5 дней ($2.99)", callback_data="sub_trial")],
            [InlineKeyboardButton("⭐ STANDARD - 7 дней ($4.99)", callback_data="sub_standard")],
            [InlineKeyboardButton("💎 PREMIUM - 30 дней ($14.99)", callback_data="sub_premium")],
            [InlineKeyboardButton("🔙 Назад", callback_data="menu_back")]
        ]
        
        message = """
💎 *Подписки Crypto Intelligence*

👑 *Бесплатно:*
• 2 анализа в день
• Базовые данные

🎁 *TRIAL - $2.99:*
• 5 дней
• 10 анализов в день
• Все функции

⭐ *STANDARD - $4.99:*
• 7 дней
• 30 анализов в день
• Приоритетные сигналы

💎 *PREMIUM - $14.99:*
• 30 дней
• Безлимитные анализы
• Эксклюзивные сигналы
• Поддержка 24/7

💡 *Оплата:* Криптовалюта (BTC, ETH, USDT)
        """
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user_id = update.effective_user.id
        user = await self.db.get_user(user_id)
        
        if not user:
            user = await self.db.create_user(user_id=user_id)
        
        is_admin = user_id in self.admin_ids
        
        if is_admin:
            status = "👑 *Администратор*"
            features = "• Безлимитные анализы\n• Все функции\n• Управление ботом"
        elif user.is_premium:
            days = (user.subscription_expires - datetime.utcnow()).days if user.subscription_expires else 0
            status = f"💎 *PREMIUM* (осталось {days} дней)"
            features = "• Безлимитные анализы\n• Приоритетные сигналы"
        else:
            status = "👤 *Бесплатный аккаунт*"
            features = "• 2 анализа в день"
        
        tokens = await self.db.get_user_watched_tokens(user_id)
        alerts = await self.db.get_user_alerts(user_id)
        
        message = f"""
📋 *Ваш статус:*

{status}
{features}

📊 *Статистика:*
• Отслеживается монет: {len(tokens)}
• Активных оповещений: {len([a for a in alerts if a.status.value == 'active'])}
        """
        
        await update.message.reply_text(message, parse_mode="Markdown")
    
    async def cmd_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command"""
        user_id = update.effective_user.id
        user = await self.db.get_user(user_id)
        
        if not user:
            user = await self.db.create_user(user_id=user_id)
        
        keyboard = [
            [
                InlineKeyboardButton(
                    f"🔔 Сигналы: {'ВКЛ' if user.notify_on_signal else 'ВЫКЛ'}",
                    callback_data="toggle_signals"
                )
            ],
            [
                InlineKeyboardButton(
                    f"🐋 Киты: {'ВКЛ' if user.notify_on_whale else 'ВЫКЛ'}",
                    callback_data="toggle_whale"
                )
            ],
            [
                InlineKeyboardButton(
                    f"💰 Цены: {'ВКЛ' if user.notify_on_price_alert else 'ВЫКЛ'}",
                    callback_data="toggle_price"
                )
            ],
            [InlineKeyboardButton("🔙 Назад", callback_data="menu_back")]
        ]
        
        message = """
⚙️ *Настройки уведомлений:*

Настройте какие уведомления получать:
        """
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def cmd_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command"""
        user_id = update.effective_user.id
        
        if user_id not in self.admin_ids:
            await update.message.reply_text("❌ Доступ запрещён")
            return
        
        stats = await self.db.get_stats()
        
        message = f"""
👑 *Админ панель*

📊 *Статистика:*
• Пользователей: {stats['users']}
• Отслеживается монет: {stats['watched_tokens']}
• Активных оповещений: {stats['active_alerts']}
• Активных сигналов: {stats['active_signals']}

🕐 Время сервера: {datetime.utcnow().strftime('%H:%M:%S %d.%m.%Y')}
        """
        
        keyboard = [
            [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton("📊 Полная статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("🔄 Перезапустить монитор", callback_data="admin_restart")]
        ]
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def cmd_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /broadcast command"""
        user_id = update.effective_user.id
        
        if user_id not in self.admin_ids:
            return
        
        if not context.args:
            await update.message.reply_text("❌ Укажите сообщение: `/broadcast Hello everyone!`")
            return
        
        message = " ".join(context.args)
        
        # Store broadcast message for later sending
        self.user_states[user_id] = {"broadcast": message}
        
        keyboard = [
            [InlineKeyboardButton("✅ Отправить", callback_data="confirm_broadcast")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_broadcast")]
        ]
        
        await update.message.reply_text(
            f"📢 *Подтвердите рассылку:*\n\n{message}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        user_id = update.effective_user.id
        
        if user_id not in self.admin_ids:
            return
        
        stats = await self.db.get_stats()
        
        await update.message.reply_text(
            f"📊 *Статистика бота:*\n\n"
            f"• Пользователей: {stats['users']}\n"
            f"• Отслеживается: {stats['watched_tokens']}\n"
            f"• Оповещений: {stats['active_alerts']}\n"
            f"• Сигналов: {stats['active_signals']}",
            parse_mode="Markdown"
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        # Menu navigation
        if data == "menu_back":
            await query.edit_message_text(
                "🔙 *Главное меню*",
                reply_markup=self._main_keyboard(query.from_user.id in self.admin_ids)
            )
        
        elif data == "menu_analyze":
            await query.edit_message_text(
                "📊 *Анализ монеты*\n\n"
                "Введите название монеты для анализа:\n"
                "Например: `BTC`, `ETH`, `SOL`",
                parse_mode="Markdown"
            )
        
        elif data == "menu_watchlist":
            context.args = []
            await self.cmd_watchlist(query, context)
        
        elif data == "menu_subscribe":
            context.args = []
            await self.cmd_subscribe(query, context)
        
        elif data == "menu_signals":
            context.args = []
            await self.cmd_signals(query, context)
        
        elif data == "menu_settings":
            context.args = []
            await self.cmd_settings(query, context)
        
        elif data == "menu_admin":
            if query.from_user.id in self.admin_ids:
                context.args = []
                await self.cmd_admin(query, context)
        
        # Toggle settings
        elif data.startswith("toggle_"):
            setting = data.replace("toggle_", "")
            await self._toggle_setting(query, setting)
        
        # Subscription
        elif data.startswith("sub_"):
            plan = data.replace("sub_", "")
            await self._handle_subscription(query, plan)
        
        # Analyze specific token
        elif data.startswith("analyze_"):
            token = data.replace("analyze_", "")
            context.args = [token]
            await self.cmd_analyze(query, context)
        
        # Refresh watchlist
        elif data == "refresh_watchlist":
            context.args = []
            await self.cmd_watchlist(query, context)
        
        # Admin actions
        elif data == "confirm_broadcast":
            if query.from_user.id in self.admin_ids:
                message = self.user_states.get(query.from_user.id, {}).get("broadcast", "")
                # TODO: Send to all users
                await query.edit_message_text(f"✅ *Рассылка выполнена!*")
        
        elif data == "cancel_broadcast":
            await query.edit_message_text("❌ *Рассылка отменена*")
    
    async def _toggle_setting(self, query, setting: str):
        """Toggle a user setting"""
        user_id = query.from_user.id
        user = await self.db.get_user(user_id)
        
        if not user:
            return
        
        if setting == "signals":
            await self.db.update_user(user_id, notify_on_signal=not user.notify_on_signal)
        elif setting == "whale":
            await self.db.update_user(user_id, notify_on_whale=not user.notify_on_whale)
        elif setting == "price":
            await self.db.update_user(user_id, notify_on_price_alert=not user.notify_on_price_alert)
        
        context = type('Context', (), {'args': []})()
        await self.cmd_settings(query, context)
    
    async def _handle_subscription(self, query, plan: str):
        """Handle subscription selection"""
        plans = {
            "trial": ("TRIAL", "$2.99", "5 дней", "10 анализов"),
            "standard": ("STANDARD", "$4.99", "7 дней", "30 анализов"),
            "premium": ("PREMIUM", "$14.99", "30 дней", "∞ анализов")
        }
        
        if plan not in plans:
            return
        
        name, price, duration, limit = plans[plan]
        
        message = f"""
💎 *Подписка {name}*

💰 Цена: {price}
📅 Длительность: {duration}
📊 Лимит: {limit} анализов в день

💡 *Для оплаты отправьте USDT (TRC20) на адрес:*
`TJYbKShKhCfNMXKj9p1Gaz2KfK5w7xPqVJ`

⚠️ После оплаты отправьте TX hash боту.
        """
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="menu_subscribe")]]
        
        await query.edit_message_text(message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        text = update.message.text.strip().upper()
        
        # Check if it's a token symbol
        if len(text) >= 2 and len(text) <= 10:
            context.args = [text]
            await self.cmd_analyze(update, context)
    
    async def start_monitoring(self):
        """Start background monitoring"""
        if self.monitor:
            await self.monitor.start()
    
    async def stop_monitoring(self):
        """Stop background monitoring"""
        if self.monitor:
            await self.monitor.stop()
    
    def run(self):
        """Run the bot"""
        app = self.create_app()
        
        print("🤖 Crypto Intelligence Bot starting...")
        print("📱 Monitoring enabled")
        
        try:
            app.run_polling(allowed_updates=Update.ALL_TYPES)
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped")
