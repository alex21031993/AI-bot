"""
Crypto Intelligence Bot - 100% Button-Only Interface

All user interaction is through buttons ONLY.
Text input is only allowed for admin password.
"""
import asyncio
from crypto_intelligence_agent.data_sources import DataSourcesInfo
from datetime import datetime
from crypto_intelligence_agent.data_sources import DataSourcesInfo
from typing import Dict, Optional

from crypto_intelligence_agent.data_sources import DataSourcesInfo
from telegram.error import BadRequest
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from crypto_intelligence_agent.data_sources import DataSourcesInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

from crypto_intelligence_agent.data_sources import DataSourcesInfo
from ..database.manager import DatabaseManager
from crypto_intelligence_agent.data_sources import DataSourcesInfo
from ..monitoring.monitor import BackgroundMonitor
from crypto_intelligence_agent.data_sources import DataSourcesInfo
from ..scanner.market_scanner import MarketScanner
from crypto_intelligence_agent.data_sources import DataSourcesInfo
from ..scanner.premium_analyzer import PremiumScanner
from crypto_intelligence_agent.data_sources import DataSourcesInfo
from ..payment.tron_tracker import TronPaymentTracker, PaymentVerifier


# ============ CONSTANTS ============
# ADMIN_PASSWORD is now loaded from .env

# Trial period
TRIAL_DAYS = 3
FREE_LIMIT_COINS = 5  # Limit for free users per day

# Popular tokens for quick selection
POPULAR_TOKENS = [
    ["BTC", "ETH", "SOL", "BNB"],
    ["XRP", "ADA", "DOGE", "AVAX"],
    ["DOT", "LINK", "MATIC", "SHIB"]
]

# Menu action constants
class Actions:
    # Main menu
    MENU_MAIN = "menu_main"
    ADMIN_MAIN = "admin_main"
    MENU_BACK = "menu_back"
    
    # Analysis menu
    MENU_ANALYSIS = "menu_analysis"
    SELECT_TOKEN = "select_token"
    ANALYSIS_RESULT = "analysis_result"
    
    # Watchlist menu  
    MENU_WATCHLIST = "menu_watchlist"
    WATCHLIST_SHOW = "watchlist_show"
    WATCHLIST_ADD = "watchlist_add"
    WATCHLIST_REMOVE = "watchlist_remove"
    
    # Signals menu
    MENU_SIGNALS = "menu_signals"
    SIGNALS_ACTIVE = "signals_active"
    
    # Alerts menu
    MENU_ALERTS = "menu_alerts"
    ALERTS_SHOW = "alerts_show"
    ALERTS_ADD = "alerts_add"
    ALERTS_ABOVE = "alerts_above"
    ALERTS_BELOW = "alerts_below"
    
    # Subscribe menu
    MENU_SUBSCRIBE = "menu_subscribe"
    SUB_TRIAL = "sub_trial"
    SUB_STANDARD = "sub_standard"
    SUB_PREMIUM = "sub_premium"
    
    # Settings menu
    MENU_SETTINGS = "menu_settings"
    SETTINGS_NOTIFY_SIGNALS = "settings_sig"
    SETTINGS_NOTIFY_WHALE = "settings_whale"
    SETTINGS_NOTIFY_PRICE = "settings_price"
    
    # Admin menu
    ADMIN_ENTER = "admin_enter"
    ADMIN_PASSWORD = "admin_password"
    ADMIN_VERIFY = "admin_verify"
    ADMIN_MAIN = "admin_menu"
    ADMIN_STATS = "admin_stats"
    ADMIN_BROADCAST = "admin_broadcast"
    ADMIN_USERS = "admin_users"
    
    # Token selection prefixes
    TOKEN_SELECT = "tok_"
    TOKEN_REMOVE = "rem_"
    TOKEN_ALERT_ABOVE = "alab_"
    TOKEN_ALERT_BELOW = "albe_"
    
    # Scanner actions
    SCAN_BUY_SIGNALS = "scan_buy"
    SCAN_TOP_10 = "scan_top10"
    SCAN_TOP_20 = "scan_top20"
    SCAN_SIGNALS = "scan_signals"
    SCAN_REFRESH = "scan_refresh"
    SCAN_COIN_DETAIL = "scan_detail_"
    
    # Payment actions
    PAY_TRIAL = "pay_trial"
    PAY_STANDARD = "pay_standard"
    PAY_PREMIUM = "pay_premium"
    PAY_CHECK = "pay_check"
    
    # Premium actions
    PREMIUM_SIGNAL = "premium_signal"
    
    # Time period actions
    PERIOD_30MIN = "period_30min"
    PERIOD_1H = "period_1h"
    PERIOD_3H = "period_3h"
    PERIOD_24H = "period_24h"
    
    # Premium deep analysis
    PREMIUM_DEEP = "premium_deep"
    ADVANCED_SYSTEM = "advanced_system"
    PAY_ADVANCED_SYSTEM = "pay_advanced_system"
    SCAN_MEME = "scan_meme"
    SCAN_PUMPS = "scan_pumps"
    SMART_MONEY = "smart_money"
    ENTRY_EXIT = "entry_exit"
    RUG_CHECK = "rug_check"
    AI_AGENT = "ai_agent"
    AI_ANALYZE = "ai_analyze"
    PAY_PREMIUM_USES = "pay_premium_uses"
    
    # Admin panel (for when admin is already authenticated)
    ADMIN_PANEL = "admin_panel"
    DATA_SOURCES_INFO = "data_sources_info"
    DATA_SOURCES = "data_sources"


class ButtonBot:
    """
    100% Button-only Telegram bot
    No text input from users (except admin password)
    """
    
    def __init__(self, token: str, admin_ids: list = None, admin_password: str = "crypto_admin_2024"):
        self.token = token
        self.admin_ids = admin_ids or []
        self.admin_password = admin_password  # Password from .env
        
        self.db = DatabaseManager()
        self.monitor: Optional[BackgroundMonitor] = None
        self.scanner = MarketScanner()
        
        # Track user states
        self.user_states: Dict[int, str] = {}
        self.admin_attempts: Dict[int, int] = {}
        self.temp_data: Dict[int, dict] = {}
        
        # User daily limits (for free trial)
        self.user_requests: Dict[int, int] = {}  # user_id -> requests_today
        self.last_request_date: Dict[int, str] = {}  # user_id -> date string
        
        # Payment tracker
        self.payment_tracker: Optional[TronPaymentTracker] = None
        self.payment_verifier: Optional[PaymentVerifier] = None
        self.deposit_address: str = ""
        
        # Premium scanner
        self.premium_scanner = PremiumScanner()
    
    async def initialize(self):
        """Initialize bot components"""
        await self.db.initialize()
        
        # Initialize payment tracker
        from dotenv import load_dotenv
        import os
        load_dotenv()
        
        usdt_contract = os.getenv("USDT_CONTRACT_TRC20", "TR7NHqjeKQxGTCi8q8REbdNKR2AfZ7Tn7")
        self.deposit_address = os.getenv("TRON_DEPOSIT_ADDRESS", "")
        min_confirmations = int(os.getenv("MIN_CONFIRMATIONS", "6"))
        
        self.payment_tracker = TronPaymentTracker(
            usdt_contract=usdt_contract,
            min_confirmations=min_confirmations,
            check_interval=30
        )
        
        self.payment_verifier = PaymentVerifier(
            tracker=self.payment_tracker,
            db=self.db
        )
        
        await self.payment_tracker.start_monitoring()
        
        self.monitor = BackgroundMonitor(
            db=self.db,
            alert_callback=self._send_alert
        )
    
    async def _send_alert(self, user_id: int, message: str):
        """Send alert to user"""
        try:
            if hasattr(self, 'app') and self.app:
                await self.app.bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown")
        except Exception as e:
            print(f"Error sending alert: {e}")
    
    def create_app(self) -> Application:
        """Create and configure the Telegram application"""
        self.app = Application.builder().token(self.token).build()
        
        # Only allow callback queries and specific commands
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        
        # Only allow text for admin password
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_text_input
        ))
        
        return self.app
    
    # ============ COMMAND HANDLERS ============
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - show welcome and main menu"""
        user_id = update.effective_user.id
        first_name = update.effective_user.first_name or "Друг"
        
        # Auto-register user with trial period
        user = await self.db.create_user(
            user_id=user_id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name,
            last_name=update.effective_user.last_name
        )
        
        # Set trial period if new user
        if user and not user.subscription_expires and not user.is_premium:
            from datetime import timedelta
            trial_end = datetime.utcnow() + timedelta(days=TRIAL_DAYS)
            await self.db.update_user(user_id, subscription_expires=trial_end)
        
        self.user_states[user_id] = Actions.MENU_MAIN
        
        # Get user's subscription status
        user = await self.db.get_user(user_id)
        is_trial = user and user.subscription_expires and not user.is_premium
        
        if is_trial:
            days_left = (user.subscription_expires - datetime.utcnow()).days
            trial_text = f"""
🎁 *Бесплатный пробный период*

⏰ Осталось дней: *{max(0, days_left)}*
📊 Лимит запросов: {FREE_LIMIT_COINS} монет/день

💡 После окончания пробного периода:
• Подписка активируется автоматически
• Мы напомним вам о продлении
"""
        else:
            trial_text = """
🎁 *Ваша подписка активна!*

✅ Бесплатные функции доступны
💎 Полный доступ к аналитике
"""
        
        welcome_text = f"""👋 *Привет, {first_name}!*

🐋 Я — *Crypto Intelligence Bot*
Твой персональный AI-аналитик криптовалют

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎁 *Бесплатный пробный период активен!*

⏰ У Вас осталось: *{max(0, days_left)} дней*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 *ЧТО УМЕЕТ ЭТОТ БОТ:*

🔍 *ПОИСК МОНЕТ*
• Нахожу лучшие монеты для покупки
• Анализирую объёмы и тренды
• Автоматическое сканирование рынка

📊 *СИГНАЛЫ*
• 🟢 BUY — сигнал на покупку
• 🟡 HOLD — держать позицию
• 🔴 SELL — сигнал на продажу
• Анализ 50+ индикаторов

🐋 *ОТСЛЕЖИВАНИЕ КИТОВ*
• Нахожу крупных держателей
• Анализирую движение средств
• Smart Money Tracker

💎 *PREMIUM АНАЛИЗ*
• Глубокий AI-анализ монеты
• Прогноз пампа/дампа
• Входные точки (TP/SL)
• Уведомления 24/7

🧠 *ADVANCED SYSTEM*
• AI-анализ токенов
• Early Pump Detector
• Rug Pull Detector
• AI Confidence Engine
• Meme Coin Scanner

🔔 *УВЕДОМЛЕНИЯ*
• Сигналы в реальном времени
• Уведомления о пампах/дампах
• Настройка оповещений по цене

━━━━━━━━━━━━━━━━━━━━━━━━━━━

👇 *Выберите действие:*"""
        
        await update.message.reply_text(
            welcome_text,
            parse_mode="Markdown",
            reply_markup=self._get_main_menu_keyboard()
        )
    
    # ============ CALLBACK HANDLER ============
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all button presses"""
        query = update.callback_query
        try:
            await query.answer()
        except Exception:
            # Ignore old callback queries
            pass
        
        user_id = query.from_user.id
        data = query.data
        
        # Handle based on current state and action
        if data == Actions.MENU_MAIN:
            user_id = query.from_user.id
            if user_id in self.admin_ids:
                await self._show_admin_main_menu(query)
            else:
                await self._show_main_menu(query)
        elif data == Actions.MENU_BACK:
            # Всегда показывать главное меню (не админку)
            await self._show_main_menu(query)
        elif data == Actions.ADMIN_MAIN:
            await self._show_admin_main_menu(query)
        
        elif data == Actions.MENU_ANALYSIS:
            await self._show_analysis_menu(query)
        
        elif data == Actions.SCAN_BUY_SIGNALS:
            await self._show_buy_signals(query)
        
        elif data == Actions.SCAN_TOP_10:
            await self._show_top_coins(query, limit=10)
        elif data == Actions.SCAN_TOP_20:
            await self._show_top_coins(query, limit=20)
        
        elif data == Actions.SCAN_SIGNALS:
            await self._show_all_signals(query)
        
        elif data == Actions.SCAN_REFRESH:
            await self._refresh_scan(query)
        
        elif data.startswith(Actions.SCAN_COIN_DETAIL):
            coin_symbol = data.replace(Actions.SCAN_COIN_DETAIL, "")
            await self._show_coin_detail(query, coin_symbol)
        
        # Payment handlers
        elif data == Actions.PAY_TRIAL:
            await self._show_payment_form(query, "trial")
        
        elif data == Actions.PAY_STANDARD:
            await self._show_payment_form(query, "standard")
        
        elif data == Actions.PAY_PREMIUM:
            await self._show_payment_form(query, "premium")
        
        elif data == Actions.PAY_CHECK:
            await self._check_payment(query)
        
        elif data == Actions.PREMIUM_SIGNAL:
            await self._show_premium_signal(query)
        
        elif data == Actions.PERIOD_30MIN:
            await self._analyze_period(query, 30)
        
        elif data == Actions.PERIOD_1H:
            await self._analyze_period(query, 60)
        
        elif data == Actions.PERIOD_3H:
            await self._analyze_period(query, 180)
        
        elif data == Actions.PERIOD_24H:
            await self._analyze_period(query, 1440)
        
        elif data == Actions.ADMIN_PANEL:
            await self._show_admin_panel(query)
        
        
        elif data == Actions.PREMIUM_DEEP:
            await self._show_premium_deep(query)

        elif data == Actions.ADVANCED_SYSTEM:
            await self._show_advanced_system(query)
        
        elif data == Actions.PAY_ADVANCED_SYSTEM:
            await self._show_advanced_payment(query)

        # Advanced System sub-menus
        elif data == Actions.SCAN_MEME:
            await self._show_meme_coins(query)
        elif data == Actions.SCAN_PUMPS:
            await self._show_early_pumps(query)
        elif data == Actions.SMART_MONEY:
            await self._show_smart_money(query)
        elif data == Actions.ENTRY_EXIT:
            await self._show_entry_exit(query)
        elif data == Actions.RUG_CHECK:
            await self._show_rug_check(query)
        elif data.startswith("smartmoney_"):
            token = data.replace("smartmoney_", "")
            await self._show_smart_money(query, token)
        elif data.startswith("entryexit_"):
            token = data.replace("entryexit_", "")
            await self._show_entry_exit(query, token)
        elif data.startswith("rugcheck_"):
            token = data.replace("rugcheck_", "")
            await self._show_rug_check(query, token)
        elif data == Actions.AI_AGENT:
            await self._show_ai_agent(query)
        elif data.startswith("aianalyze_"):
            token = data.replace("aianalyze_", "")
            await self._analyze_with_ai(query, token)

        elif data == Actions.PAY_PREMIUM_USES:
            await self._show_premium_uses_payment(query)
        
        elif data == Actions.SELECT_TOKEN:
            await self._show_token_selection(query, "analysis")
        
        elif data.startswith(Actions.TOKEN_SELECT):
            token = data.replace(Actions.TOKEN_SELECT, "")
            await self._analyze_token(query, token)
        
        elif data == Actions.MENU_WATCHLIST:
            await self._show_watchlist_menu(query)
        
        elif data == Actions.WATCHLIST_ADD:
            await self._show_token_selection(query, "watchlist_add")
        
        elif data.startswith(Actions.TOKEN_SELECT + "watchlist_add_"):
            token = data.replace(Actions.TOKEN_SELECT + "watchlist_add_", "")
            await self._add_to_watchlist(query, token)
        
        elif data == Actions.WATCHLIST_REMOVE:
            await self._show_watchlist_remove(query)
        
        elif data.startswith(Actions.TOKEN_REMOVE):
            token = data.replace(Actions.TOKEN_REMOVE, "")
            await self._remove_from_watchlist(query, token)
        
        elif data == Actions.WATCHLIST_SHOW:
            await self._show_watchlist(query)
        
        elif data == Actions.MENU_SIGNALS:
            await self._show_signals_menu(query)
        
        elif data == Actions.SIGNALS_ACTIVE:
            await self._show_active_signals(query)
        
        elif data == Actions.MENU_ALERTS:
            await self._show_alerts_menu(query)
        
        elif data == Actions.ALERTS_ADD:
            await self._show_alerts_type_selection(query)
        
        elif data == Actions.ALERTS_ABOVE:
            await self._show_token_selection(query, "alert_above")
        
        elif data == Actions.ALERTS_BELOW:
            await self._show_token_selection(query, "alert_below")
        
        elif data.startswith(Actions.TOKEN_ALERT_ABOVE):
            token = data.replace(Actions.TOKEN_ALERT_ABOVE, "")
            await self._set_price_alert(query, token, "above")
        
        elif data.startswith(Actions.TOKEN_ALERT_BELOW):
            token = data.replace(Actions.TOKEN_ALERT_BELOW, "")
            await self._set_price_alert(query, token, "below")
        
        elif data == Actions.ALERTS_SHOW:
            await self._show_user_alerts(query)
        
        elif data == Actions.MENU_SUBSCRIBE:
            await self._show_subscribe_menu(query)
        
        elif data in [Actions.SUB_TRIAL, Actions.SUB_STANDARD, Actions.SUB_PREMIUM]:
            await self._show_subscription_details(query, data)
        
        elif data == Actions.MENU_SETTINGS:
            await self._show_settings_menu(query)
        
        elif data.startswith(Actions.SETTINGS_NOTIFY_SIGNALS):
            await self._toggle_setting(query, "signal")
        
        elif data.startswith(Actions.SETTINGS_NOTIFY_WHALE):
            await self._toggle_setting(query, "whale")
        
        elif data.startswith(Actions.SETTINGS_NOTIFY_PRICE):
            await self._toggle_setting(query, "price")
        
        elif data == Actions.ADMIN_ENTER:
            await self._request_admin_password(query)
        
        elif data == Actions.ADMIN_MAIN:
            await self._show_admin_menu(query)
        
        elif data == Actions.ADMIN_STATS:
            await self._show_admin_stats(query)
        
        elif data == Actions.ADMIN_BROADCAST:
            await self._request_broadcast_message(query)
        
        elif data == Actions.ADMIN_USERS:
            await self._show_admin_users(query)

        elif data == Actions.DATA_SOURCES_INFO:
            await self._show_data_sources_info(query)
    
    # ============ TEXT INPUT HANDLER ============
    
    async def handle_text_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text input - only admin password allowed"""
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        # Check if user is entering admin password
        if self.user_states.get(user_id) == Actions.ADMIN_ENTER:
            if user_id in self.admin_ids:
                if text == self.admin_password:
                    user = await self.db.get_user(user_id)
                    first_name = update.effective_user.first_name or "Администратор"
                    
                    admin_welcome = f"""👑 *Вы вошли как администратор!*

👋 Привет, {first_name}!

🐋 *Crypto Intelligence Bot*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎁 *Бесплатный неограниченный доступ!*

💎 Вам доступны все функции без ограничений:
• Все анализы и сканирования
• Premium функции
• Advanced System
• Управление пользователями

━━━━━━━━━━━━━━━━━━━━━━━━━━━

👇 *Выберите действие:*"""
                    
                    await update.message.reply_text(
                        admin_welcome,
                        parse_mode="Markdown",
                        reply_markup=self._get_full_admin_menu_keyboard()
                    )
                    self.user_states[user_id] = Actions.ADMIN_MAIN
                else:
                    attempts = self.admin_attempts.get(user_id, 0) + 1
                    self.admin_attempts[user_id] = attempts
                    
                    if attempts >= 3:
                        await update.message.reply_text("❌ Слишком много попыток. Попробуйте позже.")
                        self.user_states[user_id] = Actions.MENU_MAIN
                    else:
                        await update.message.reply_text(
                            f"❌ Неверный пароль. Осталось попыток: {3 - attempts}",
                            reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("🔙 Отмена", callback_data=Actions.MENU_BACK)
                            ]])
                        )
            return
        
        # Check if user is entering broadcast message
        if self.user_states.get(user_id) == "broadcast_input" and user_id in self.admin_ids:
            self.temp_data[user_id] = {"broadcast_msg": text}
            await update.message.reply_text(
                f"📢 *Подтвердите рассылку:*\n\n{text}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Отправить", callback_data="confirm_broadcast")],
                    [InlineKeyboardButton("❌ Отмена", callback_data=Actions.ADMIN_MAIN)]
                ])
            )
            self.user_states[user_id] = Actions.ADMIN_MAIN
            return
        
        # Check if user is entering alert price
        if self.user_states.get(user_id, "").startswith("alert_price_"):
            parts = self.user_states[user_id].split("_")
            token = parts[2]
            direction = parts[3]
            
            try:
                price = float(text.replace(",", "").replace("$", ""))
                await self._create_price_alert(update.message, token, direction, price)
            except ValueError:
                await update.message.reply_text(
                    "❌ Неверный формат цены. Введите число.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Отмена", callback_data=Actions.MENU_ALERTS)
                    ]])
                )
            self.user_states[user_id] = Actions.MENU_ALERTS
            return
        
        # Everything else - use buttons only!
        await update.message.reply_text(
            "⚠️ *Используйте кнопки для управления ботом.*\n\nНажмите /start для главного меню.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📱 Главное меню", callback_data=Actions.MENU_BACK)
            ]])
        )
    
    # ============ MENU METHODS ============
    
    def _get_main_menu_text(self) -> str:
        return """🐋 *Crypto Intelligence Bot*

🤖 Бот АВТОМАТИЧЕСКИ находит лучшие монеты
📊 Сканирует рынок каждые 15 минут
🟢 Находит монеты с высоким потенциалом роста

━━━━━━━━━━━━━━━
👇 Выберите действие:"""

    def _get_main_menu_keyboard(self, user_trial_active: bool = True, is_admin: bool = False, days_remaining: int = 3) -> InlineKeyboardMarkup:
        """
        Get main menu keyboard
        - Admin: full access (no days counter)
        - Trial active: all buttons + days remaining
        - Trial expired: subscription only
        """
        # Admin has full access (no trial needed)
        if is_admin:
            return InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 НАЙТИ МОНЕТЫ", callback_data=Actions.SCAN_BUY_SIGNALS)],
                [InlineKeyboardButton("📊 ТОП-20 🏆", callback_data=Actions.SCAN_TOP_20)],
                [InlineKeyboardButton("📈 СИГНАЛЫ", callback_data=Actions.SCAN_SIGNALS)],
                [InlineKeyboardButton("🔄 ОБНОВИТЬ", callback_data=Actions.SCAN_REFRESH)],
                [InlineKeyboardButton("💎 PREMIUM АНАЛИЗ", callback_data=Actions.PREMIUM_DEEP)],
                [InlineKeyboardButton("⏱️ АНАЛИЗ ПЕРИОДА", callback_data=Actions.PREMIUM_SIGNAL)],
                [InlineKeyboardButton("🔔 Оповещения", callback_data=Actions.MENU_ALERTS)],
                [InlineKeyboardButton("🧠 ADVANCED SYSTEM", callback_data=Actions.ADVANCED_SYSTEM)],
                [InlineKeyboardButton("👑 Админ", callback_data=Actions.ADMIN_ENTER)]
            ])
        
        # If trial expired - show only subscription
        if not user_trial_active:
            return InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 КУПИТЬ ПОДПИСКУ", callback_data=Actions.MENU_SUBSCRIBE)]
            ])
        
        # Trial active - show all buttons + days remaining
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 НАЙТИ МОНЕТЫ", callback_data=Actions.SCAN_BUY_SIGNALS)],
            [InlineKeyboardButton("📊 ТОП-20 🏆", callback_data=Actions.SCAN_TOP_20)],
            [InlineKeyboardButton("📈 СИГНАЛЫ", callback_data=Actions.SCAN_SIGNALS)],
            [InlineKeyboardButton("🔄 ОБНОВИТЬ", callback_data=Actions.SCAN_REFRESH)],
            [InlineKeyboardButton("💎 PREMIUM АНАЛИЗ", callback_data=Actions.PREMIUM_DEEP)],
            [InlineKeyboardButton("⏱️ АНАЛИЗ ПЕРИОДА", callback_data=Actions.PREMIUM_SIGNAL)],
            [InlineKeyboardButton("🔔 Оповещения", callback_data=Actions.MENU_ALERTS)],
                [InlineKeyboardButton("🧠 ADVANCED SYSTEM", callback_data=Actions.ADVANCED_SYSTEM)],
            [InlineKeyboardButton("👑 Админ", callback_data=Actions.ADMIN_ENTER)]
        ])
    
    async def _show_admin_main_menu(self, query):
        """Показать админ-панель"""
        await self._safe_edit_message(
            query,
            "👑 *Админ-панель*\n\nВыберите действие:",
            parse_mode="Markdown",
            reply_markup=self._get_full_admin_menu_keyboard()
        )

    async def _show_main_menu(self, query):
        """Show main menu with trial check"""
        user_id = query.from_user.id
        
        # Check if trial is active for non-admin users
        user_trial_active = True
        is_admin = user_id in self.admin_ids
        days_remaining = 3
        
        if not is_admin:
            user = await self.db.get_user(user_id)
            if user and user.created_at:
                from datetime import timedelta
                trial_end = user.created_at + timedelta(days=3)
                user_trial_active = datetime.utcnow() < trial_end
                
                # Calculate days remaining
                if user_trial_active:
                    time_left = trial_end - datetime.utcnow()
                    days_remaining = max(0, time_left.days)
                    if time_left.seconds > 0 and days_remaining == 0:
                        days_remaining = 1  # At least 1 day if still active
        
        # If trial expired - show subscription only
        if not is_admin and not user_trial_active:
            text = """🐋 *Crypto Intelligence Bot*

━━━━━━━━━━━━━━━━━━━━━━━━

⏰ *Ваш бесплатный период истёк!*

📅 Пробный период: 3 дня (закончился)

💎 *Подписка открывает:*
• Все функции без ограничений
• Premium анализ монеты дня
• Сигналы 24/7
• Уведомления о пампах/дампах

👇 *Выберите план подписки:*
"""
            await self._safe_edit_message(query, text, parse_mode="Markdown", reply_markup=self._get_main_menu_keyboard(user_trial_active=False, is_admin=False))
            return
        
        # Show full menu with days remaining
        await self._safe_edit_message(query, self._get_main_menu_text(), parse_mode="Markdown", reply_markup=self._get_main_menu_keyboard(user_trial_active=True, is_admin=is_admin, days_remaining=days_remaining))
    
    # ============ SCANNER METHODS ============
    
    async def _show_buy_signals(self, query):
        """Показать монеты с сигналом BUY"""
        await query.edit_message_text("🔍 *Сканирую рынок...*\n\nНахожу монеты с сигналом 🟢 BUY")
        
        try:
            coins = await self.scanner.scan_market(100)
            buy_coins = [c for c in coins if c.recommendation == "BUY"][:10]
            
            if not buy_coins:
                text = """🟡 *Нет сигналов BUY*

Система не нашла монет с явным сигналом на покупку.

Нажмите "Обновить" для повторного сканирования."""
            else:
                text = f"""🟢 *Монеты с сигналом BUY*

Найдено: {len(buy_coins)} монет
Время сканирования: {datetime.utcnow().strftime('%H:%M:%S')}

"""
                for coin in buy_coins:
                    text += f"{coin.emoji} *{coin.symbol}*\n"
                    text += f"   💰 ${coin.price:,.4f}\n"
                    text += f"   📈 {coin.price_change_24h:+.1f}% | 📊 {coin.total_score:.0f}%\n\n"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data=Actions.SCAN_REFRESH)],
                [InlineKeyboardButton("📊 ТОП-20 🏆", callback_data=Actions.SCAN_TOP_20)],
                [InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)]
            ])
            
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Ошибка сканирования: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)
                ]])
            )
    
    async def _show_top_coins(self, query, limit=10):
        """Показать топ-10 монет по баллам"""
        await query.edit_message_text("📊 *Сканирую рынок...*\n\nАнализирую топ-100 монет")
        
        try:
            coins = await self.scanner.scan_market(100)
            top_coins = coins[:limit]
            
            text = f"""📊 *ТОП-{limit} монет по потенциалу*

Рейтинг составлен на основе:
• Объем торгов
• Динамика цены
• Настроения рынка
• Активность китов

🕐 Обновлено: {datetime.utcnow().strftime('%H:%M:%S')}

"""
            
            for i, coin in enumerate(top_coins, 1):
                emoji = coin.emoji
                text += f"{i}. {emoji} *{coin.symbol}*\n"
                text += f"   💰 ${coin.price:,.4f}\n"
                text += f"   📊 Балл: {coin.total_score:.0f}/100 | 📈 {coin.price_change_24h:+.1f}%\n"
                text += f"   💡 {coin.rationale[0] if coin.rationale else 'Хороший выбор'}\n\n"
            
            # Add coins as buttons for details
            keyboard_buttons = []
            row = []
            for coin in top_coins:
                row.append(InlineKeyboardButton(f"{coin.emoji} {coin.symbol}", callback_data=f"{Actions.SCAN_COIN_DETAIL}{coin.symbol}"))
                if len(row) == 2:
                    keyboard_buttons.append(row)
                    row = []
            if row:
                keyboard_buttons.append(row)
            
            keyboard_buttons.append([InlineKeyboardButton("🔄 Обновить", callback_data=Actions.SCAN_REFRESH)])
            keyboard_buttons.append([InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)])
            
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard_buttons))
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)
                ]])
            )
    
    async def _show_all_signals(self, query):
        """Показать все сигналы"""
        await query.edit_message_text("📈 *Анализирую сигналы...*")
        
        try:
            coins = await self.scanner.scan_market(50)
            
            buy = [c for c in coins if c.recommendation == "BUY"]
            hold = [c for c in coins if c.recommendation == "HOLD"]
            sell = [c for c in coins if c.recommendation == "SELL"]
            
            text = f"""📈 *Сводка по сигналам*

🟢 BUY: {len(buy)} монет
🟡 HOLD: {len(hold)} монет
🔴 SELL: {len(sell)} монет

━━━━━━━━━━━━━━━

🟢 *Сигналы на ПОКУПКУ:*
"""
            for coin in buy[:3]:
                text += f"• {coin.symbol}: {coin.total_score:.0f}%\n"
            
            if not buy:
                text += "Нет\n"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🟢 BUY", callback_data=Actions.SCAN_BUY_SIGNALS)],
                [InlineKeyboardButton("🔴 SELL", callback_data="show_sell")],
                [InlineKeyboardButton("🔄 Обновить", callback_data=Actions.SCAN_REFRESH)],
                [InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)]
            ])
            
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)
                ]])
            )
    
    async def _refresh_scan(self, query):
        """Обновить сканирование"""
        await query.edit_message_text("🔄 *Обновляю данные...*\n\nСканирую рынок заново")
        
        try:
            coins = await self.scanner.scan_market(100)
            
            buy = len([c for c in coins if c.recommendation == "BUY"])
            
            text = f"""✅ *Данные обновлены!*

📊 Просканировано: {len(coins)} монет
🟢 Сигналов BUY: {buy}

🕐 Время: {datetime.utcnow().strftime('%H:%M:%S')}
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 НАЙТИ МОНЕТЫ", callback_data=Actions.SCAN_BUY_SIGNALS)],
                [InlineKeyboardButton("📊 ТОП-20 🏆", callback_data=Actions.SCAN_TOP_20)],
                [InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)]
            ])
            
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)
                ]])
            )
    
    async def _show_coin_detail(self, query, symbol: str):
        """Показать детали монеты"""
        await query.edit_message_text(f"📊 *Загружаю {symbol}...*")
        
        try:
            coins = self.scanner.get_top_coins(100)
            coin = next((c for c in coins if c.symbol == symbol), None)
            
            if not coin:
                await query.edit_message_text(
                    "❌ Монета не найдена. Обновите данные.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔄 Обновить", callback_data=Actions.SCAN_REFRESH),
                        InlineKeyboardButton("🔙 Назад", callback_data=Actions.SCAN_TOP_10)
                    ]])
                )
                return
            
            # Подробный анализ монеты
            text = f"""🪙 *{coin.name} ({coin.symbol})*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 *Цена:* ${coin.price:,.6f}
📊 *Капитализация:* ${coin.market_cap/1e9:.2f}B
📈 *Изменение 24ч:* {coin.price_change_24h:+.1f}%
📉 *Изменение 7д:* {coin.price_change_7d:+.1f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 *Рекомендация:* {coin.emoji} {coin.recommendation}
📊 *Общий балл:* {coin.total_score:.0f}/100
📈 *Потенциал роста:* {coin.growth_potential:.0f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 *Детальный анализ:*

🔹 Social Score: {coin.social_score:.0f}/100
🔹 Sentiment: {coin.sentiment_score:.0f}/100
🔹 Whale Activity: {coin.whale_score:.0f}/100
🔹 Technical: {coin.technical_score:.0f}/100
🔹 Volume: {coin.volume_score:.0f}/100"""

            # Обоснование рекомендации
            if coin.rationale:
                text += f"\n━━━━━━━━━━━━━━━\n💡 *Почему {coin.recommendation}:*"
                for r in coin.rationale[:3]:
                    text += f"\n• {r}"

            # Риски
            if coin.risks:
                text += f"\n━━━━━━━━━━━━━━━\n⚠️ *Риски:*"
                for r in coin.risks[:2]:
                    text += f"\n• {r}"

            # Торговые уровни
            entry = coin.price
            stop_loss = coin.price * 0.95
            take_profit = coin.price * 1.25 if coin.total_score > 70 else coin.price * 1.15

            text += f"\n━━━━━━━━━━━━━━━\n📐 *Торговые уровни:*\n"
            text += f"• Вход: ${entry:,.6f}\n"
            text += f"• TP: ${take_profit:,.6f} (+{((take_profit/entry)-1)*100:.1f}%)\n"
            text += f"• SL: ${stop_loss:,.6f} ({((stop_loss/entry)-1)*100:.1f}%)\n"

            text += f"\n⚠️ Не является финансовой рекомендацией!"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👁️ Добавить в отслеживание", callback_data=f"track_{symbol}")],
                [InlineKeyboardButton("🔄 Другие монеты", callback_data=Actions.SCAN_TOP_10)],
                [InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)]
            ])
            
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)
                ]])
            )
    
    # ============ PAYMENT METHODS ============
    
    async def _show_admin_panel(self, query):
        """Показать админ-панель"""
        user_id = query.from_user.id
        
        if user_id not in self.admin_ids:
            await query.edit_message_text(
                "❌ Доступ запрещён!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)
                ]])
            )
            return
        
        await query.edit_message_text(
            "👑 *АДМИН-ПАНЕЛЬ*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👋 Добро пожаловать, администратор!\n\n"
            "💎 У вас полный доступ ко всем функциям!",
            parse_mode="Markdown",
            reply_markup=self._get_admin_keyboard()
        )
    
    async def _show_premium_deep(self, query):
        """Показать Premium глубокий анализ"""
        user_id = query.from_user.id
        
        # Check user access
        user = await self.db.get_user(user_id)
        user_trial_active = True
        if user and user.created_at:
            from datetime import timedelta
            trial_end = user.created_at + timedelta(days=3)
            user_trial_active = datetime.utcnow() < trial_end
        
        # Check premium uses
        uses_remaining = getattr(user, 'premium_uses_remaining', 0) if user else 0
        
        # Check subscription
        is_subscribed = user and user.subscription_expires and user.subscription_expires > datetime.utcnow()
        
        # Check trial - give 5 free uses during trial
        if user_trial_active and uses_remaining <= 0:
            uses_remaining = 5  # Trial: 5 free, Purchase: 10
        
        # Admin has unlimited access
        is_admin = user_id in self.admin_ids
        
        # If no access - show payment
        if uses_remaining <= 0 and not is_subscribed and not is_admin:
            text = """💎 *PREMIUM ГЛУБОКИЙ АНАЛИЗ*

━━━━━━━━━━━━━━━━━━━━━━━━

🔒 Для доступа к глубокому анализу:

📦 *10 использований - $1.99*
• Полный анализ монеты
• Китовый анализ
• Прогноз пампа/дампа
• Входные точки
• Уведомления 24/7

💡 Анализ включает:
• Данные с 10+ источников
• Социальные метрики
• Он-чейн данные
• Объёмы торгов
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 КУПИТЬ 10 АНАЛИЗОВ - $1.99", callback_data=Actions.PAY_PREMIUM_USES)],
                [InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)]
            ])
            
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
            return
        
        # Show counter and start analysis
        counter_text = "∞" if is_admin else str(uses_remaining)
        
        await query.edit_message_text(
            "💎 *PREMIUM ГЛУБОКИЙ АНАЛИЗ*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 Осталось использований: *{counter_text}*\n\n"
            "⏳ Запускаю глубокий анализ монеты..."
        )
        
        try:
            # Decrement uses (not for admin)
            if not is_admin and user:
                await self.db.db.execute(
                    "UPDATE users SET premium_uses_remaining = premium_uses_remaining - 1 WHERE user_id = ?",
                    (user_id,)
                )
                await self.db.db.commit()
            
            analysis = await self.premium_scanner.get_today_coin()
            if analysis:
                text = analysis.to_detailed_report()
                text += f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━"
                
                if is_admin:
                    text += f"\n👑 *Администратор: ∞ использований*"
                else:
                    text += f"\n📊 Осталось использований: *{uses_remaining - 1}*"
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 ОБНОВИТЬ", callback_data=Actions.PREMIUM_DEEP)],
                    [InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)]
                ])
                
                await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
            else:
                await query.edit_message_text(
                    "❌ Ошибка анализа. Попробуйте позже.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)
                    ]])
                )
        except Exception as e:
            await query.edit_message_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)
                ]])
            )
    
    async def _show_premium_uses_payment(self, query):
        """Показать форму оплаты Premium использований"""
        user_id = query.from_user.id
        
        text = """💳 *ПОКУПКА PREMIUM АНАЛИЗОВ*

━━━━━━━━━━━━━━━━━━━━━━━━

📦 *10 глубоких анализов*

💰 Цена: *$1.99*

✅ *Что входит:*
• Полный анализ монеты
• Китовый анализ
• Прогноз пампа/дампа
• Входные точки (TP/SL)
• Уведомления 24/7

━━━━━━━━━━━━━━━

💵 *Оплата USDT (TRC20):*

📬 Адрес:
`TCSYEiTBp67GvUk3f2f1foL1jdRKu6upD8`

━━━━━━━━━━━━━━━

⚠️ Минимальная сумма: 1 USDT
⏱️ Оплата проверяется автоматически

📝 После оплаты напишите свой Telegram ID: `{user_id}`

💡 Или отправьте скриншот оплаты администратору
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 ПРОВЕРИТЬ ОПЛАТУ", callback_data=Actions.PAY_CHECK)],
            [InlineKeyboardButton("🔙 Отмена", callback_data=Actions.MENU_BACK)]
        ])
        
        await query.edit_message_text(
            text.format(user_id=user_id),
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    
    async def _show_advanced_system(self, query):
        """Показать Advanced System (премиум)"""
        user_id = query.from_user.id

        # Admin has unlimited access
        is_admin = user_id in self.admin_ids

        # Check subscription
        try:
            user = await self.db.get_user(user_id)
            is_subscribed = user and user.subscription_expires and user.subscription_expires > datetime.utcnow()
        except:
            is_subscribed = False

        # Force access for testing
        has_access = is_admin or is_subscribed or True

        if has_access:
            text = "🧠 *ADVANCED SYSTEM*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n👋 Выберите функцию:"

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🤖 AI Agent", callback_data=Actions.AI_AGENT)],
                [InlineKeyboardButton("🐋 Smart Money", callback_data=Actions.SMART_MONEY)],
                [InlineKeyboardButton("🌀 Meme Scanner", callback_data=Actions.SCAN_MEME)],
                [InlineKeyboardButton("📈 Early Pump", callback_data=Actions.SCAN_PUMPS)],
                [InlineKeyboardButton("🛡️ Rug Check", callback_data=Actions.RUG_CHECK)],
                [InlineKeyboardButton("🧠 Entry/Exit", callback_data=Actions.ENTRY_EXIT)],
                [InlineKeyboardButton("🔙 Назад", callback_data=Actions.MENU_BACK)]
            ])

            await query.answer("OK")
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            text = "🔒 *PREMIUM REQUIRED*\n\nНажмите ОПЛАТИТЬ для доступа"

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 ОПЛАТИТЬ", callback_data=Actions.PAY_ADVANCED_SYSTEM)],
                [InlineKeyboardButton("🔙 Назад", callback_data=Actions.MENU_BACK)]
            ])

            await query.answer("Нужен Premium", show_alert=True)
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)

    async def _show_data_sources_info(self, query):
        """Показать информацию об источниках данных"""
        counts = DataSourcesInfo.get_all_sources_count()
        
        text = f"""📡 *ИСТОЧНИКИ ДАННЫХ*
━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔢 Всего источников: *{counts['Всего']}*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 *РЫНОЧНЫЕ ДАННЫЕ ({counts['Рыночные данные']}):*
• CoinMarketCap
• CoinGecko
• DexScreener
• DexTools
• GeckoTerminal
• Birdeye
• TradingView

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🐋 *ОНЧЕЙН И КИТЫ ({counts['Ончейн и киты']}):*
• Whale Alert
• Arkham Intelligence
• Nansen
• Bubblemaps
• Etherscan
• Solscan
• BscScan
• Pump.fun
• GMGN
• Jupiter
• Raydium

━━━━━━━━━━━━━━━━━━━━━━━━━━━

💬 *СОЦИАЛЬНЫЕ СЕТИ ({counts['Социальные сети']}):*
• X (Twitter)
• Telegram
• Reddit
• Instagram
• Facebook
• TikTok
• YouTube
• Discord
• Bitcointalk
• CryptoPanic
• 4chan /biz/
• Medium

━━━━━━━━━━━━━━━━━━━━━━━━━━━

📰 *НОВОСТИ ({counts['Новости']}):*
• Google Search
• Google Trends
• Google News
• CoinDesk
• Cointelegraph
• The Block
• Decrypt
• Bitcoin Magazine

━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)]
        ])
        
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    async def _show_premium_signal(self, query):
        """Показать выбор периода анализа или результат анализа"""
        user_id = query.from_user.id
        
        try:
            # Проверяем подписку или админ
            user = await self.db.get_user(user_id)
            is_premium = (
                user_id in self.admin_ids or  # Admin has full access
                (user and user.is_premium) or
                (user and user.subscription_expires and user.subscription_expires > datetime.utcnow())
            )
            
            # Проверяем trial период (3 дня)
            user_trial_active = True
            if user and user.created_at:
                from datetime import timedelta
                trial_end = user.created_at + timedelta(days=3)
                user_trial_active = datetime.utcnow() < trial_end
            
            has_access = is_premium or user_trial_active or user_id in self.admin_ids
            
            if not has_access:
                # Показываем превью обычного анализа
                coins = await self.scanner.scan_market(50)
                if coins:
                    top_coin = coins[0]
                    
                    text = f"""🔒 *PREMIUM ДОСТУП*

⏰ Ваш пробный период истёк!

━━━━━━━━━━━━━━━

📊 *Превью монеты дня:*
{top_coin.emoji} *{top_coin.symbol}*
💰 ${top_coin.price:,.4f}
📊 Балл: {top_coin.total_score:.0f}%

━━━━━━━━━━━━━━━

💎 *Подписка открывает:*
• Анализ на 30 мин, 1ч, 3ч, 24ч
• Прогноз пампа/дампа
• Китовый анализ
• Уведомления за 15 минут

💰 Стоимость: от $2.99
"""
                    
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("💳 КУПИТЬ ПОДПИСКУ", callback_data=Actions.MENU_SUBSCRIBE)],
                        [InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)]
                    ])
                    
                    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
                return
            
            # Показываем выбор периода анализа
            text = """⏱️ *ВЫБЕРИТЕ ПЕРИОД АНАЛИЗА*

━━━━━━━━━━━━━━━━━━━━━━━━

🐋 Выберите временной период для анализа монеты:

📊 *Доступные периоды:*
• 🕐 30 минут - краткосрочный
• 🕐 1 час - среднесрочный
• 🕐 3 часа - долгосрочный
• 🕐 24 часа - суточный

💎 Будет проанализирована 1 монета с:
• Прогнозом пампа/дампа
• Китовым анализом
• Входными точками
• Уведомлением за 15 минут
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🕐 30 МИНУТ", callback_data=Actions.PERIOD_30MIN)],
                [InlineKeyboardButton("🕐 1 ЧАС", callback_data=Actions.PERIOD_1H)],
                [InlineKeyboardButton("🕐 3 ЧАСА", callback_data=Actions.PERIOD_3H)],
                [InlineKeyboardButton("🕐 24 ЧАСА", callback_data=Actions.PERIOD_24H)],
                [InlineKeyboardButton("🔙 Назад", callback_data=Actions.MENU_BACK)]
            ])
            
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)
                ]])
            )
    
    async def _analyze_period(self, query, period_minutes: int):
        """Анализ монеты за выбранный период"""
        user_id = query.from_user.id
        
        period_names = {
            30: "30 минут",
            60: "1 час",
            180: "3 часа",
            1440: "24 часа"
        }
        
        await query.edit_message_text(
            f"⏱️ *АНАЛИЗ НА {period_names.get(period_minutes, str(period_minutes))}*\n\n"
            f"🔍 Ищу монету с наибольшим потенциалом...\n"
            f"📊 Провожу глубокий анализ..."
        )
        
        try:
            # Получаем анализ
            analysis = await self.premium_scanner.get_today_coin()
            
            if not analysis:
                await query.edit_message_text(
                    "❌ Ошибка анализа. Попробуйте позже.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data=Actions.MENU_BACK)
                    ]])
                )
                return
            
            # Добавляем информацию о периоде
            text = analysis.to_detailed_report()
            
            # Добавляем информацию о периоде и уведомлении
            notification_time = analysis.next_alert_at.strftime("%H:%M")
            
            text += f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━"
            text += f"\n⏱️ *Период анализа:* {period_names.get(period_minutes, str(period_minutes))}"
            text += f"\n🔔 *Уведомление в:* {notification_time}"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 ДРУГАЯ МОНЕТА", callback_data=Actions.PREMIUM_SIGNAL)],
                [InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)]
            ])
            
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)
                ]])
            )
    
    async def _show_payment_form(self, query, plan: str):
        """Show payment form for subscription"""
        user_id = query.from_user.id
        
        plan_info = {
            "trial": ("🎁 TRIAL", "5 дней", "$2.99"),
            "standard": ("⭐ STANDARD", "7 дней", "$4.99"),
            "premium": ("💎 PREMIUM", "30 дней", "$14.99")
        }
        
        name, days, price = plan_info.get(plan, ("❓", "?", "?"))
        
        # Create payment
        address = self.deposit_address
        
        if not address:
            await query.edit_message_text(
                "❌ *Ошибка оплаты*\n\nАдрес для оплаты не настроен. Обратитесь к администратору.",
                parse_mode="Markdown"
            )
            return
        
        text = f"""💳 *Оплата подписки*

{name}
━━━━━━━━━━━━━━━
📅 Срок: {days}
💰 Цена: {price} USDT

━━━━━━━━━━━━━━━

📋 *Инструкция:*

1️⃣ Скопируйте адрес ниже
2️⃣ Отправьте {price} USDT (TRC20)
3️⃣ Нажмите "Проверить оплату"

━━━━━━━━━━━━━━━

🏦 *Адрес для оплаты:*
`{address}`

⚠️ *Внимание:*
• Только сеть TRON (TRC20)
• Только USDT токен
• Минимум 6 подтверждений (~30 сек)

━━━━━━━━━━━━━━━

💡 После оплаты нажмите кнопку "Проверить оплату"
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Проверить оплату", callback_data=Actions.PAY_CHECK)],
            [InlineKeyboardButton("💎 Другие планы", callback_data=Actions.MENU_SUBSCRIBE)],
            [InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)]
        ])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    
    async def _check_payment(self, query):
        """Check if payment was received"""
        user_id = query.from_user.id
        
        await query.edit_message_text("🔍 *Проверяю оплату...*\n\nПодключение к блокчейну TRON...")
        
        try:
            # Get user's pending payment
            # For simplicity, we'll use the shared deposit address
            # In production, you'd generate unique addresses per user
            address = self.deposit_address
            
            if not address:
                await query.edit_message_text(
                    "❌ Адрес не настроен",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data=Actions.MENU_BACK)
                    ]])
                )
                return
            
            # Check for payments
            txs = await self.payment_tracker.check_address_transactions(address)
            
            if not txs:
                text = """🔍 *Оплата не найдена*

⏳ Платеж обычно поступает в течение 1-2 минут

💡 *Проверьте:*
• Отправили ли вы USDT (не другую монету)
• Использовали ли сеть TRON (TRC20)
• Хватило ли подтверждений (обычно ~30 сек)

━━━━━━━━━━━━━━━
Попробуйте проверить через минуту.
"""
            else:
                # Payment found!
                tx = txs[0]
                amount = tx.get("amount", 0)
                
                # Activate subscription based on amount
                from datetime import timedelta
                
                if amount >= 14.99:
                    plan = "premium"
                    days = 30
                elif amount >= 4.99:
                    plan = "standard"
                    days = 7
                elif amount >= 2.99:
                    plan = "trial"
                    days = 5
                else:
                    plan = "unknown"
                    days = 0
                
                if days > 0:
                    expires = datetime.utcnow() + timedelta(days=days)
                    await self.db.update_user(user_id, is_premium=True, subscription_expires=expires)
                    
                    # Add 10 premium uses for deep analysis
                    await self.db.db.execute(
                        "UPDATE users SET premium_uses_remaining = 10 WHERE user_id = ?",
                        (user_id,)
                    )
                    await self.db.db.commit()
                    
                    text = f"""✅ *ОПЛАТА ПОДТВЕРЖДЕНА!*

💰 Получено: {amount} USDT
📋 План: {plan.upper()}
📅 Период: {days} дней
📅 Истекает: {expires.strftime('%d.%m.%Y')}

━━━━━━━━━━━━━━━
🎁 *БОНУС:*
📊 +10 глубоких анализов PREMIUM

━━━━━━━━━━━━━━━
TxID: `{tx.get('tx_id', '')[:20]}...`

🎉 *Ваша подписка активирована!*
"""
                else:
                    text = f"""⚠️ *Сумма не соответствует*

💰 Получено: {amount} USDT
💵 Ожидалось: 2.99 / 4.99 / 14.99 USDT

Свяжитесь с администратором.
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)]
            ])
            
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Ошибка проверки: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data=Actions.MENU_BACK)
                ]])
            )
    
    # ============ ANALYSIS METHODS ============
    
    async def _show_analysis_menu(self, query):
        """Show analysis selection menu"""
        user_id = query.from_user.id
        self.user_states[user_id] = Actions.MENU_ANALYSIS
        
        text = """📊 *Анализ монеты*

Выберите способ анализа:"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Популярные монеты", callback_data=Actions.SELECT_TOKEN)],
            [InlineKeyboardButton("➕ Ввести свою монету", callback_data="custom_token_input")],
            [InlineKeyboardButton("🔙 Назад", callback_data=Actions.MENU_BACK)]
        ])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    
    async def _show_token_selection(self, query, purpose: str):
        """Show popular tokens for selection"""
        user_id = query.from_user.id
        self.user_states[user_id] = f"select_token_{purpose}"
        
        text = """💎 *Выберите монету*

Нажмите на монету для анализа:"""
        
        keyboard_buttons = []
        for row in POPULAR_TOKENS:
            button_row = [InlineKeyboardButton(token, callback_data=f"{Actions.TOKEN_SELECT}{purpose}_{token}") for token in row]
            keyboard_buttons.append(button_row)
        
        keyboard_buttons.append([InlineKeyboardButton("🔙 Назад", callback_data=Actions.MENU_ANALYSIS)])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard_buttons))
    
    async def _analyze_token(self, query, token: str):
        """Analyze a token and show results"""
        user_id = query.from_user.id
        await query.edit_message_text(f"🔍 *Анализирую {token}...*")
        
        try:
            if self.monitor:
                result = await self.monitor.manual_check(user_id, token)
            else:
                result = "❌ Сервис анализа временно недоступен."
            
            # Format result as message
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Другой анализ", callback_data=Actions.MENU_ANALYSIS)],
                [InlineKeyboardButton("👁️ Добавить в портфель", callback_data=f"{Actions.TOKEN_SELECT}watchlist_add_{token}")],
                [InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)]
            ])
            
            await query.edit_message_text(result, parse_mode="Markdown", reply_markup=keyboard)
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Ошибка анализа: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data=Actions.MENU_ANALYSIS)
                ]])
            )
    
    # ============ WATCHLIST METHODS ============
    
    async def _show_watchlist_menu(self, query):
        """Show watchlist menu"""
        user_id = query.from_user.id
        self.user_states[user_id] = Actions.MENU_WATCHLIST
        
        text = """👁️ *Мой портфель*

Управление отслеживаемыми монетами:"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👁️ Показать портфель", callback_data=Actions.WATCHLIST_SHOW)],
            [InlineKeyboardButton("➕ Добавить монету", callback_data=Actions.WATCHLIST_ADD)],
            [InlineKeyboardButton("➖ Удалить монету", callback_data=Actions.WATCHLIST_REMOVE)],
            [InlineKeyboardButton("🔙 Назад", callback_data=Actions.MENU_BACK)]
        ])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    
    async def _show_watchlist(self, query):
        """Show user's watchlist"""
        user_id = query.from_user.id
        tokens = await self.db.get_user_watched_tokens(user_id)
        
        if not tokens:
            text = "📋 *Ваш портфель пуст*\n\nДобавьте монеты для отслеживания."
        else:
            text = "👁️ *Ваш портфель:*\n\n"
            
            for token in tokens[:10]:
                emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡", "WAIT": "⚪"}
                rec = emoji.get(token.last_recommendation.value if token.last_recommendation else "?", "⚪")
                
                price = f"${token.current_price:,.2f}" if token.current_price else "N/A"
                conf = f"{token.last_confidence:.0f}%" if token.last_confidence else ""
                
                text += f"{rec} *{token.token_symbol}*\n"
                text += f"   💰 {price} | 📊 {conf}\n\n"
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад", callback_data=Actions.MENU_WATCHLIST)
        ]])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    
    async def _add_to_watchlist(self, query, token: str):
        """Add token to watchlist"""
        user_id = query.from_user.id
        
        await self.db.add_watched_token(user_id, token, token)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Анализировать", callback_data=f"{Actions.TOKEN_SELECT}analysis_{token}")],
            [InlineKeyboardButton("👁️ К портфелю", callback_data=Actions.MENU_WATCHLIST)],
            [InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)]
        ])
        
        await query.edit_message_text(
            f"✅ *{token} добавлен в портфель!*\n\nТеперь будете получать сигналы по этой монете.",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    
    async def _show_watchlist_remove(self, query):
        """Show tokens to remove"""
        user_id = query.from_user.id
        tokens = await self.db.get_user_watched_tokens(user_id)
        
        if not tokens:
            text = "📋 *Ваш портфель пуст*\n\nНечего удалять."
        else:
            text = "➖ *Выберите монету для удаления:*"
            
            keyboard_buttons = []
            for token in tokens:
                keyboard_buttons.append([
                    InlineKeyboardButton(f"❌ {token.token_symbol}", callback_data=f"{Actions.TOKEN_REMOVE}{token.token_symbol}")
                ])
            
            keyboard_buttons.append([InlineKeyboardButton("🔙 Назад", callback_data=Actions.MENU_WATCHLIST)])
            
            await query.edit_message_text(text, parse_mode="Markdown", 
                reply_markup=InlineKeyboardMarkup(keyboard_buttons))
            return
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад", callback_data=Actions.MENU_WATCHLIST)
        ]]))
    
    async def _remove_from_watchlist(self, query, token: str):
        """Remove token from watchlist"""
        user_id = query.from_user.id
        
        await self.db.remove_watched_token(user_id, token)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👁️ К портфелю", callback_data=Actions.MENU_WATCHLIST)],
            [InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)]
        ])
        
        await query.edit_message_text(
            f"✅ *{token} удалён из портфеля*",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    
    # ============ SIGNALS METHODS ============
    
    async def _show_signals_menu(self, query):
        """Show signals menu"""
        user_id = query.from_user.id
        self.user_states[user_id] = Actions.MENU_SIGNALS
        
        text = """📈 *Торговые сигналы*

Актуальные сигналы от бота:"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Активные сигналы", callback_data=Actions.SIGNALS_ACTIVE)],
            [InlineKeyboardButton("📋 Мои сигналы", callback_data="my_signals")],
            [InlineKeyboardButton("🔙 Назад", callback_data=Actions.MENU_BACK)]
        ])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    
    async def _show_active_signals(self, query):
        """Show active trading signals"""
        signals = await self.db.get_active_signals()
        
        if not signals:
            text = "📈 *Нет активных сигналов*\n\nСигналы появятся автоматически."
        else:
            text = "📈 *Активные сигналы:*\n\n"
            
            for signal in signals[:5]:
                emoji = {"buy": "🟢", "sell": "🔴", "hold": "🟡", "wait": "⚪"}
                e = emoji.get(signal.recommendation.value, "⚪")
                
                text += f"{e} *{signal.token_symbol}* — {signal.recommendation.value.upper()}\n"
                text += f"   💰 ${signal.entry_price:,.2f} | 📊 {signal.confidence:.0f}%\n\n"
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад", callback_data=Actions.MENU_SIGNALS)
        ]])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    
    # ============ ALERTS METHODS ============
    
    async def _show_alerts_menu(self, query):
        """Show alerts menu"""
        user_id = query.from_user.id
        self.user_states[user_id] = Actions.MENU_ALERTS
        
        text = """🔔 *Оповещения*

Настройте уведомления о ценах:"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔔 Мои оповещения", callback_data=Actions.ALERTS_SHOW)],
            [InlineKeyboardButton("📈 Когда цена вырастет", callback_data=Actions.ALERTS_ABOVE)],
            [InlineKeyboardButton("📉 Когда цена упадёт", callback_data=Actions.ALERTS_BELOW)],
            [InlineKeyboardButton("🔙 Назад", callback_data=Actions.MENU_BACK)]
        ])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    
    async def _show_alerts_type_selection(self, query):
        """Show alert type selection"""
        text = """🔔 *Новое оповещение*

Выберите тип оповещения:"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📈 Цена ВЫШЕ", callback_data=Actions.ALERTS_ABOVE)],
            [InlineKeyboardButton("📉 Цена НИЖЕ", callback_data=Actions.ALERTS_BELOW)],
            [InlineKeyboardButton("🔙 Назад", callback_data=Actions.MENU_ALERTS)]
        ])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    
    async def _set_price_alert(self, query, token: str, direction: str):
        """Start price alert setup"""
        user_id = query.from_user.id
        self.user_states[user_id] = f"alert_price_{token}_{direction}"
        
        direction_text = "выше" if direction == "above" else "ниже"
        emoji = "📈" if direction == "above" else "📉"
        
        text = f"""{emoji} *Оповещение: {token}*

Когда цена будет {direction_text}?

Введите целевую цену (число):"""
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Отмена", callback_data=Actions.MENU_ALERTS)
        ]])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    
    async def _create_price_alert(self, message, token: str, direction: str, price: float):
        """Create a price alert"""
        user_id = message.from_user.id
        
        from ..database.models import AlertType
        alert_type = AlertType.PRICE_ABOVE if direction == "above" else AlertType.PRICE_BELOW
        
        await self.db.create_price_alert(user_id, token, alert_type, price)
        
        emoji = "📈" if direction == "above" else "📉"
        direction_text = "выше" if direction == "above" else "ниже"
        
        await message.reply_text(
            f"{emoji} *Оповещение создано!*\n\n"
            f"📊 {token}\n"
            f"Когда цена будет {direction_text}: ${price:,.2f}\n\n"
            f"Вы получите уведомление!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔔 К оповещениям", callback_data=Actions.MENU_ALERTS)
            ]])
        )
    
    async def _show_user_alerts(self, query):
        """Show user's alerts"""
        user_id = query.from_user.id
        alerts = await self.db.get_user_alerts(user_id)
        
        if not alerts:
            text = "🔔 *Нет активных оповещений*\n\nСоздайте новое оповещение."
        else:
            text = "🔔 *Ваши оповещения:*\n\n"
            
            for alert in alerts[:10]:
                emoji = "📈" if alert.alert_type.value == "price_above" else "📉"
                status = "✅" if alert.status.value == "active" else "⏸️"
                
                text += f"{emoji} {status} *{alert.token_symbol}*\n"
                text += f"   ${alert.target_value:,.2f}\n\n"
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад", callback_data=Actions.MENU_ALERTS)
        ]])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    
    # ============ SUBSCRIBE METHODS ============
    
    async def _show_subscribe_menu(self, query):
        """Show subscription menu"""
        user_id = query.from_user.id
        self.user_states[user_id] = Actions.MENU_SUBSCRIBE
        
        text = """💎 *Тарифы подписки*

Выберите план для оплаты USDT (TRC20):

━━━━━━━━━━━━━━━

🎁 *TRIAL* — $2.99
   • 5 дней доступа
   • Все функции

⭐ *STANDARD* — $4.99
   • 7 дней доступа
   • Все функции
   • Приоритетная поддержка

💎 *PREMIUM* — $14.99
   • 30 дней доступа
   • Все функции
   • VIP поддержка
   • Ранний доступ к сигналам

━━━━━━━━━━━━━━━

💳 Оплата через USDT TRC20"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 TRIAL — $2.99", callback_data=Actions.PAY_TRIAL)],
            [InlineKeyboardButton("⭐ STANDARD — $4.99", callback_data=Actions.PAY_STANDARD)],
            [InlineKeyboardButton("💎 PREMIUM — $14.99", callback_data=Actions.PAY_PREMIUM)],
            [InlineKeyboardButton("🔙 Назад", callback_data=Actions.MENU_BACK)]
        ])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    
    async def _show_subscription_details(self, query, plan: str):
        """Show subscription details"""
        plans = {
            Actions.SUB_TRIAL: ("TRIAL", "5 дней", "$2.99", "10 анализов/день"),
            Actions.SUB_STANDARD: ("STANDARD", "7 дней", "$4.99", "30 анализов/день"),
            Actions.SUB_PREMIUM: ("PREMIUM", "30 дней", "$14.99", "∞ анализов")
        }
        
        name, duration, price, limit = plans.get(plan, ("Unknown", "?", "?", "?"))
        
        text = f"""💎 *Подписка {name}*

💰 Цена: {price}
📅 Длительность: {duration}
📊 Лимит: {limit} анализов/день

━━━━━━━━━━━━━━━

💡 *Оплата криптовалютой:*

*USDT (TRC20):*
`TJYbKShKhCfNMXKj9p1Gaz2KfK5w7xPqVJ`

*После оплаты отправьте TX hash боту*
(через кнопку "Оплата" ниже)"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Отправить TX hash", callback_data="input_tx_hash")],
            [InlineKeyboardButton("🔙 К подпискам", callback_data=Actions.MENU_SUBSCRIBE)],
            [InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)]
        ])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    
    # ============ SETTINGS METHODS ============
    
    async def _show_settings_menu(self, query):
        """Show settings menu"""
        user_id = query.from_user.id
        user = await self.db.get_user(user_id)
        
        self.user_states[user_id] = Actions.MENU_SETTINGS
        
        sig_status = "✅ ВКЛ" if user.notify_on_signal else "❌ ВЫКЛ"
        whale_status = "✅ ВКЛ" if user.notify_on_whale else "❌ ВЫКЛ"
        price_status = "✅ ВКЛ" if user.notify_on_price_alert else "❌ ВЫКЛ"
        
        text = """⚙️ *Настройки уведомлений*

Включите/выключите уведомления:"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"🔔 Сигналы: {sig_status}", callback_data=Actions.SETTINGS_NOTIFY_SIGNALS)],
            [InlineKeyboardButton(f"🐋 Киты: {whale_status}", callback_data=Actions.SETTINGS_NOTIFY_WHALE)],
            [InlineKeyboardButton(f"💰 Цены: {price_status}", callback_data=Actions.SETTINGS_NOTIFY_PRICE)],
            [InlineKeyboardButton("🔙 Назад", callback_data=Actions.MENU_BACK)]
        ])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    
    async def _toggle_setting(self, query, setting: str):
        """Toggle a setting"""
        user_id = query.from_user.id
        user = await self.db.get_user(user_id)
        
        if setting == "signal":
            await self.db.update_user(user_id, notify_on_signal=not user.notify_on_signal)
        elif setting == "whale":
            await self.db.update_user(user_id, notify_on_whale=not user.notify_on_whale)
        elif setting == "price":
            await self.db.update_user(user_id, notify_on_price_alert=not user.notify_on_price_alert)
        
        await self._show_settings_menu(query)
    
    # ============ ADMIN METHODS ============
    

    def _get_full_admin_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Полное меню для администратора - все кнопки + админ-функции"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 НАЙТИ МОНЕТЫ", callback_data=Actions.SCAN_BUY_SIGNALS)],
            [InlineKeyboardButton("📊 ТОП-20 🏆", callback_data=Actions.SCAN_TOP_20)],
            [InlineKeyboardButton("📈 СИГНАЛЫ", callback_data=Actions.SCAN_SIGNALS)],
            [InlineKeyboardButton("🔄 ОБНОВИТЬ", callback_data=Actions.SCAN_REFRESH)],
            [InlineKeyboardButton("💎 PREMIUM АНАЛИЗ", callback_data=Actions.PREMIUM_DEEP)],
            [InlineKeyboardButton("⏱️ АНАЛИЗ ПЕРИОДА", callback_data=Actions.PREMIUM_SIGNAL)],
            [InlineKeyboardButton("🔔 Оповещения", callback_data=Actions.MENU_ALERTS)],
            [InlineKeyboardButton("🧠 ADVANCED SYSTEM", callback_data=Actions.ADVANCED_SYSTEM)],
            [InlineKeyboardButton("━━━━━━━━━━━━━━━", callback_data="noop")],
            [InlineKeyboardButton("📊 Статистика", callback_data=Actions.ADMIN_STATS)],
            [InlineKeyboardButton("📡 ИСТОЧНИКИ", callback_data=Actions.DATA_SOURCES_INFO)],
            [InlineKeyboardButton("👥 Пользователи", callback_data=Actions.ADMIN_USERS)],
            [InlineKeyboardButton("📢 Рассылка", callback_data=Actions.ADMIN_BROADCAST)],
            [InlineKeyboardButton("🔙 Админ-панель", callback_data=Actions.ADMIN_MAIN)]
        ])


    async def _safe_edit_message(self, query, text, parse_mode=None, reply_markup=None):
        """Безопасно редактирует сообщение, игнорируя BadRequest"""
        try:
            await query.edit_message_text(
                text,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
        except BadRequest:
            pass  # Message not modified - ignore
        except Exception:
            pass

    def _get_admin_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Статистика", callback_data=Actions.ADMIN_STATS)],
                [InlineKeyboardButton("📡 ИСТОЧНИКИ", callback_data=Actions.DATA_SOURCES_INFO)],
            [InlineKeyboardButton("👥 Пользователи", callback_data=Actions.ADMIN_USERS)],
            [InlineKeyboardButton("📢 Рассылка", callback_data=Actions.ADMIN_BROADCAST)],
            [InlineKeyboardButton("🔙 Выход", callback_data=Actions.MENU_BACK)]
        ])
    
    async def _request_admin_password(self, query):
        """Request admin password"""
        user_id = query.from_user.id
        
        # Check if user is in admin list
        if user_id not in self.admin_ids:
            await query.edit_message_text(
                "❌ *Доступ запрещён*\n\nУ вас нет прав администратора.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Главное меню", callback_data=Actions.MENU_BACK)
                ]])
            )
            return
        
        self.user_states[user_id] = Actions.ADMIN_ENTER
        self.admin_attempts[user_id] = 0
        
        await query.edit_message_text(
            "🔐 *Введите пароль администратора:*\n\nЭто ЕДИНСТВЕННЫЙ случай когда можно ввести текст.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Отмена", callback_data=Actions.MENU_BACK)
            ]])
        )
    
    async def _show_admin_menu(self, query):
        """Show admin menu"""
        await self._safe_edit_message(
            query,
            "👑 *Админ-панель*\n\nВыберите действие:",
            parse_mode="Markdown",
            reply_markup=self._get_full_admin_menu_keyboard()
        )
    
    async def _show_admin_stats(self, query):
        """Show admin statistics"""
        stats = await self.db.get_stats()
        
        text = f"""📊 *Статистика бота*

👥 Пользователей: {stats['users']}
👁️ Отслеживают монеты: {stats['watched_tokens']}
🔔 Активных оповещений: {stats['active_alerts']}
📈 Активных сигналов: {stats['active_signals']}

🕐 {datetime.utcnow().strftime('%H:%M:%S %d.%m.%Y')}"""
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 К админ-панели", callback_data=Actions.ADMIN_MAIN)
        ]])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    
    async def _show_admin_users(self, query):
        """Show user statistics"""
        stats = await self.db.get_stats()
        
        text = f"""👥 *Пользователи*

Всего пользователей: {stats['users']}

📋 Действия с пользователями будут доступны в следующих версиях."""
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 К админ-панели", callback_data=Actions.ADMIN_MAIN)
        ]])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    
    async def _request_broadcast_message(self, query):
        """Request broadcast message"""
        user_id = query.from_user.id
        self.user_states[user_id] = "broadcast_input"
        
        await query.edit_message_text(
            "📢 *Рассылка*\n\nВведите сообщение для рассылки всем пользователям:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Отмена", callback_data=Actions.ADMIN_MAIN)
            ]])
        )
    


    # ============ ADVANCED SYSTEM ============

    async def _show_meme_coins(self, query):
        """Показать Meme Coin Scanner"""
        await query.edit_message_text("🌀 *MEME COIN SCANNER*\n\n🔍 Ищу мем-коины...\n⏳ Подождите...")
        
        try:
            from crypto_intelligence_agent.scanner.meme_coin_scanner import MemeCoinScanner
            scanner = MemeCoinScanner()
            results = await asyncio.wait_for(scanner.scan_meme_coins(limit=10), timeout=45)
            await scanner.close()
            
            report = scanner.format_report(results) if results else "❌ Не удалось найти мем-коины"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data=Actions.SCAN_MEME)],
                [InlineKeyboardButton("🔙 Назад", callback_data=Actions.ADVANCED_SYSTEM)]
            ])
            await query.edit_message_text(report, parse_mode="Markdown", reply_markup=keyboard)
        except asyncio.TimeoutError:
            await query.edit_message_text("❌ Таймаут. Попробуйте через несколько минут.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=Actions.ADVANCED_SYSTEM)]]))
        except Exception as e:
            await query.edit_message_text(f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=Actions.ADVANCED_SYSTEM)]]))
    async def _show_ai_agent(self, query):
        """Показать Crypto Intelligence Agent"""
        text = """🤖 *CRYPTO INTELLIGENCE AGENT*
━━━━━━━━━━━━━━━━━━━━━━━━

Выберите монету для AI-анализа:

━━━━━━━━━━━━━━━━━━━━━━━━
📊 *ЧТО АНАЛИЗИРУЕТ АГЕНТ:*
🔍 Социальные сети и настроения
🐋 Активность китов
📈 Технические индикаторы
📊 Объемы торгов
🎯 Вероятность роста/падения
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🤖 BTC", callback_data="aianalyze_btc"),
             InlineKeyboardButton("🤖 ETH", callback_data="aianalyze_eth"),
             InlineKeyboardButton("🤖 SOL", callback_data="aianalyze_sol")],
            [InlineKeyboardButton("🤖 DOGE", callback_data="aianalyze_doge"),
             InlineKeyboardButton("🤖 SHIB", callback_data="aianalyze_shib"),
             InlineKeyboardButton("🤖 PEPE", callback_data="aianalyze_pepe")],
            [InlineKeyboardButton("🔙 Назад", callback_data=Actions.ADVANCED_SYSTEM)]
        ])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)

    async def _analyze_with_ai(self, query, token: str):
        """Анализ монеты с помощью AI Agent"""
        await query.edit_message_text(
            f"🤖 *CRYPTO INTELLIGENCE AGENT*\n\n"
            f"🔍 Анализирую {token.upper()}...\n\n"
            "⏳ Подождите, это может занять 10-30 секунд..."
        )
        
        try:
            from crypto_intelligence_agent.agents.crypto_intelligence_agent import CryptoIntelligenceAgent
            
            agent = CryptoIntelligenceAgent()
            metrics = await asyncio.wait_for(agent.analyze_coin(token), timeout=60)
            await agent.close()
            
            report = agent.format_report(metrics)
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Другой токен", callback_data=Actions.AI_AGENT)],
                [InlineKeyboardButton("🔙 Назад", callback_data=Actions.ADVANCED_SYSTEM)]
            ])
            
            await query.edit_message_text(report, parse_mode="Markdown", reply_markup=keyboard)
            
        except asyncio.TimeoutError:
            await query.edit_message_text(
                "❌ Таймаут. AI анализ занял слишком долго.\n\n"
                "Попробуйте снова или выберите другую монету.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=Actions.AI_AGENT)]])
            )
        except Exception as e:
            await query.edit_message_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=Actions.AI_AGENT)]])
            )



    async def _show_early_pumps(self, query):
        """Показать Early Pump Detector"""
        await query.edit_message_text("📈 *EARLY PUMP DETECTOR*\n\n🔍 Ищу сигналы...\n⏳ Подождите...")
        
        try:
            from crypto_intelligence_agent.scanner.early_pump_detector import EarlyPumpDetector
            detector = EarlyPumpDetector()
            results = await asyncio.wait_for(detector.detect_pumps(limit=10), timeout=45)
            await detector.close()
            
            report = detector.format_report(results) if results else "❌ Не обнаружено"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data=Actions.SCAN_PUMPS)],
                [InlineKeyboardButton("🔙 Назад", callback_data=Actions.ADVANCED_SYSTEM)]
            ])
            await query.edit_message_text(report, parse_mode="Markdown", reply_markup=keyboard)
        except Exception as e:
            await query.edit_message_text(f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=Actions.ADVANCED_SYSTEM)]]))

    async def _show_smart_money(self, query, token: str = "bitcoin"):
        """Показать Smart Money Tracker"""
        await query.edit_message_text(f"🐋 *SMART MONEY TRACKER*\n\n🔍 Анализирую {token.upper()}...\n⏳ Подождите...")
        
        try:
            from crypto_intelligence_agent.scanner.smart_money_tracker import SmartMoneyTracker
            tracker = SmartMoneyTracker()
            result = await asyncio.wait_for(tracker.track_token(token), timeout=30)
            await tracker.close()
            
            report = tracker.format_report(result)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🐋 BTC", callback_data="smartmoney_btc"),
                 InlineKeyboardButton("🐋 ETH", callback_data="smartmoney_eth"),
                 InlineKeyboardButton("🐋 SOL", callback_data="smartmoney_sol")],
                [InlineKeyboardButton("🔙 Назад", callback_data=Actions.ADVANCED_SYSTEM)]
            ])
            await query.edit_message_text(report, parse_mode="Markdown", reply_markup=keyboard)
        except Exception as e:
            await query.edit_message_text(f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=Actions.ADVANCED_SYSTEM)]]))

    async def _show_entry_exit(self, query, token: str = "bitcoin"):
        """Показать AI Entry & Exit"""
        await query.edit_message_text(f"🧠 *AI ENTRY & EXIT*\n\n🔍 Анализирую {token.upper()}...\n⏳ Подождите...")
        
        try:
            from crypto_intelligence_agent.scanner.ai_entry_exit import AIEntryExitScanner
            scanner = AIEntryExitScanner()
            result = await asyncio.wait_for(scanner.analyze(token), timeout=30)
            await scanner.close()
            
            report = scanner.format_report(result)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🧠 BTC", callback_data="entryexit_btc"),
                 InlineKeyboardButton("🧠 ETH", callback_data="entryexit_eth"),
                 InlineKeyboardButton("🧠 SOL", callback_data="entryexit_sol")],
                [InlineKeyboardButton("🔙 Назад", callback_data=Actions.ADVANCED_SYSTEM)]
            ])
            await query.edit_message_text(report, parse_mode="Markdown", reply_markup=keyboard)
        except Exception as e:
            await query.edit_message_text(f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=Actions.ADVANCED_SYSTEM)]]))

    async def _show_rug_check(self, query, token: str = None):
        """Показать Rug Pull Detector"""
        if not token:
            text = "🛡️ *RUG PULL DETECTOR*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\nВыберите монету:"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 BTC", callback_data="rugcheck_btc"),
                 InlineKeyboardButton("🔍 ETH", callback_data="rugcheck_eth"),
                 InlineKeyboardButton("🔍 SOL", callback_data="rugcheck_sol")],
                [InlineKeyboardButton("🔍 DOGE", callback_data="rugcheck_doge"),
                 InlineKeyboardButton("🔍 SHIB", callback_data="rugcheck_shib"),
                 InlineKeyboardButton("🔍 PEPE", callback_data="rugcheck_pepe")],
                [InlineKeyboardButton("🔙 Назад", callback_data=Actions.ADVANCED_SYSTEM)]
            ])
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
            return
        
        await query.edit_message_text(f"🛡️ *Проверяю {token.upper()}...*\n\n⏳ Подождите...")
        
        try:
            from crypto_intelligence_agent.scanner.rug_pull_detector import RugPullDetector
            detector = RugPullDetector()
            result = await asyncio.wait_for(detector.check_token(token), timeout=30)
            await detector.close()
            
            report = detector.format_report(result)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Другая", callback_data=Actions.RUG_CHECK)],
                [InlineKeyboardButton("🔙 Назад", callback_data=Actions.ADVANCED_SYSTEM)]
            ])
            await query.edit_message_text(report, parse_mode="Markdown", reply_markup=keyboard)
        except Exception as e:
            await query.edit_message_text(f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=Actions.ADVANCED_SYSTEM)]]))


    # ============ MONITORING ============
    
    async def start_monitoring(self):
        """Start background monitoring"""
        if self.monitor:
            await self.monitor.start()
    
    async def stop_monitoring(self):
        """Stop background monitoring"""
        if self.monitor:
            await self.monitor.stop()
        if self.payment_tracker:
            await self.payment_tracker.stop_monitoring()
        await self.scanner.close()
        await self.premium_scanner.close()
    
    def run(self):
        """Run the bot"""
        app = self.create_app()
        
        print("🤖 Crypto Intelligence Bot (Button-Only)")
        print("📱 All interaction through buttons only!")
        print("🔐 Admin password required for admin panel")
        
        try:
            app.run_polling(allowed_updates=["callback_query"])
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped")
