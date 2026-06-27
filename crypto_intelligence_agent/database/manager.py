"""
Database Manager - SQLite database for storing users, alerts, and signals
"""
import asyncio
import aiosqlite
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from loguru import logger

from .models import User, WatchedToken, PriceAlert, TradingSignal, AlertStatus, AlertType, Recommendation, UserRole


class DatabaseManager:
    """Manages SQLite database for all bot data"""
    
    def __init__(self, db_path: str = "crypto_bot.db"):
        self.db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize database and create tables"""
        async with self._lock:
            if self._db is None:
                self._db = await aiosqlite.connect(self.db_path)
                self._db.row_factory = aiosqlite.Row
                await self._create_tables()
                logger.info(f"Database initialized: {self.db_path}")
    
    async def _create_tables(self):
        """Create all necessary tables"""
        await self._db.executescript("""
            -- Users table
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                role TEXT DEFAULT 'user',
                is_active INTEGER DEFAULT 1,
                is_premium INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_active TEXT DEFAULT CURRENT_TIMESTAMP,
                subscription_expires TEXT,
                notify_on_signal INTEGER DEFAULT 1,
                notify_on_whale INTEGER DEFAULT 1,
                notify_on_price_alert INTEGER DEFAULT 1,
                default_alert_tolerance REAL DEFAULT 5.0
            );
            
            -- Watched tokens table
            CREATE TABLE IF NOT EXISTS watched_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_symbol TEXT NOT NULL,
                token_name TEXT,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                entry_price REAL,
                target_price REAL,
                stop_loss REAL,
                current_price REAL,
                price_change_24h REAL DEFAULT 0,
                last_analysis TEXT,
                last_recommendation TEXT,
                last_confidence REAL DEFAULT 0,
                auto_monitor INTEGER DEFAULT 1,
                alert_on_signal INTEGER DEFAULT 1,
                UNIQUE(user_id, token_symbol)
            );
            
            -- Price alerts table
            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_symbol TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                target_value REAL NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                triggered_at TEXT,
                expires_at TEXT,
                message TEXT
            );
            
            -- Trading signals table
            CREATE TABLE IF NOT EXISTS trading_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_symbol TEXT NOT NULL,
                token_name TEXT,
                recommendation TEXT NOT NULL,
                confidence REAL NOT NULL,
                entry_price REAL NOT NULL,
                target_price REAL NOT NULL,
                stop_loss REAL NOT NULL,
                ai_score REAL DEFAULT 0,
                social_score REAL DEFAULT 0,
                whale_score REAL DEFAULT 0,
                technical_score REAL DEFAULT 0,
                volume_score REAL DEFAULT 0,
                rationale TEXT,
                risks TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                triggered_at TEXT
            );
            
            -- Create indexes
            CREATE INDEX IF NOT EXISTS idx_watched_user ON watched_tokens(user_id);
            CREATE INDEX IF NOT EXISTS idx_alerts_user ON price_alerts(user_id);
            CREATE INDEX IF NOT EXISTS idx_alerts_status ON price_alerts(status);
            CREATE INDEX IF NOT EXISTS idx_signals_token ON trading_signals(token_symbol);
            CREATE INDEX IF NOT EXISTS idx_signals_status ON trading_signals(status);
        """)
        await self._db.commit()
    
    # ============ USER METHODS ============
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        await self.initialize()
        cursor = await self._db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return self._row_to_user(row) if row else None
    
    async def create_user(self, user_id: int, username: str = None, 
                         first_name: str = None, last_name: str = None) -> User:
        """Create or update user"""
        await self.initialize()
        
        await self._db.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, created_at, last_active)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                last_active = excluded.last_active
        """, (user_id, username, first_name, last_name, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
        
        await self._db.commit()
        return await self.get_user(user_id)
    
    async def update_user(self, user_id: int, **kwargs):
        """Update user fields"""
        await self.initialize()
        
        allowed_fields = ['role', 'is_active', 'is_premium', 'subscription_expires',
                        'notify_on_signal', 'notify_on_whale', 'notify_on_price_alert',
                        'default_alert_tolerance', 'last_active']
        
        updates = []
        values = []
        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = ?")
                values.append(value.isoformat() if isinstance(value, datetime) else value)
        
        if updates:
            values.append(user_id)
            await self._db.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?",
                values
            )
            await self._db.commit()
    
    def _row_to_user(self, row) -> User:
        """Convert row to User object"""
        sub_expires = row['subscription_expires'] if row['subscription_expires'] else None
        if sub_expires:
            sub_expires = datetime.fromisoformat(sub_expires)
        
        return User(
            user_id=row['user_id'],
            username=row['username'],
            first_name=row['first_name'],
            last_name=row['last_name'],
            role=UserRole(row['role']),
            is_active=bool(row['is_active']),
            is_premium=bool(row['is_premium']),
            created_at=datetime.fromisoformat(row['created_at']),
            last_active=datetime.fromisoformat(row['last_active']),
            subscription_expires=sub_expires,
            notify_on_signal=bool(row['notify_on_signal']),
            notify_on_whale=bool(row['notify_on_whale']),
            notify_on_price_alert=bool(row['notify_on_price_alert']),
            default_alert_tolerance=row['default_alert_tolerance'] if row['default_alert_tolerance'] else 5.0
        )
    
    # ============ WATCHED TOKENS METHODS ============
    
    async def add_watched_token(self, user_id: int, symbol: str, 
                               name: str = None, entry_price: float = None,
                               target_price: float = None, stop_loss: float = None) -> WatchedToken:
        """Add token to user's watchlist"""
        await self.initialize()
        
        await self._db.execute("""
            INSERT INTO watched_tokens 
            (user_id, token_symbol, token_name, entry_price, target_price, stop_loss, added_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, token_symbol) DO UPDATE SET
                token_name = excluded.token_name,
                entry_price = COALESCE(excluded.entry_price, entry_price),
                target_price = COALESCE(excluded.target_price, target_price),
                stop_loss = COALESCE(excluded.stop_loss, stop_loss)
        """, (user_id, symbol.upper(), name, entry_price, target_price, stop_loss, datetime.utcnow().isoformat()))
        
        await self._db.commit()
        return await self.get_watched_token(user_id, symbol)
    
    async def get_watched_token(self, user_id: int, symbol: str) -> Optional[WatchedToken]:
        """Get watched token"""
        await self.initialize()
        cursor = await self._db.execute(
            "SELECT * FROM watched_tokens WHERE user_id = ? AND token_symbol = ?",
            (user_id, symbol.upper())
        )
        row = await cursor.fetchone()
        return self._row_to_watched_token(row) if row else None
    
    async def get_user_watched_tokens(self, user_id: int) -> List[WatchedToken]:
        """Get all tokens watched by user"""
        await self.initialize()
        cursor = await self._db.execute(
            "SELECT * FROM watched_tokens WHERE user_id = ? ORDER BY added_at DESC",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [self._row_to_watched_token(row) for row in rows]
    
    async def get_all_watched_tokens(self) -> List[WatchedToken]:
        """Get all watched tokens (for monitoring)"""
        await self.initialize()
        cursor = await self._db.execute(
            "SELECT * FROM watched_tokens WHERE auto_monitor = 1"
        )
        rows = await cursor.fetchall()
        return [self._row_to_watched_token(row) for row in rows]
    
    async def update_watched_token(self, token_id: int, **kwargs):
        """Update watched token fields"""
        await self.initialize()
        
        updates = []
        values = []
        for key, value in kwargs.items():
            if hasattr(WatchedToken, key):
                updates.append(f"{key} = ?")
                values.append(value.isoformat() if isinstance(value, datetime) else value)
        
        if updates:
            values.append(token_id)
            await self._db.execute(
                f"UPDATE watched_tokens SET {', '.join(updates)} WHERE id = ?",
                values
            )
            await self._db.commit()
    
    async def remove_watched_token(self, user_id: int, symbol: str):
        """Remove token from watchlist"""
        await self.initialize()
        await self._db.execute(
            "DELETE FROM watched_tokens WHERE user_id = ? AND token_symbol = ?",
            (user_id, symbol.upper())
        )
        await self._db.commit()
    
    def _row_to_watched_token(self, row) -> WatchedToken:
        """Convert row to WatchedToken object"""
        last_analysis = row['last_analysis'] if row['last_analysis'] else None
        if last_analysis:
            last_analysis = datetime.fromisoformat(last_analysis)
        
        last_rec = row['last_recommendation'] if row['last_recommendation'] else None
        if last_rec:
            last_rec = Recommendation(last_rec)
        
        return WatchedToken(
            id=row['id'],
            user_id=row['user_id'],
            token_symbol=row['token_symbol'],
            token_name=row['token_name'],
            added_at=datetime.fromisoformat(row['added_at']),
            entry_price=row['entry_price'],
            target_price=row['target_price'],
            stop_loss=row['stop_loss'],
            current_price=row['current_price'],
            price_change_24h=row['price_change_24h'] or 0,
            last_analysis=last_analysis,
            last_recommendation=last_rec,
            last_confidence=row['last_confidence'] or 0,
            auto_monitor=bool(row['auto_monitor']),
            alert_on_signal=bool(row['alert_on_signal'])
        )
    
    # ============ PRICE ALERTS METHODS ============
    
    async def create_price_alert(self, user_id: int, symbol: str, 
                                 alert_type: AlertType, target_value: float,
                                 message: str = None, expires_days: int = 7) -> PriceAlert:
        """Create a price alert"""
        await self.initialize()
        
        cursor = await self._db.execute("""
            INSERT INTO price_alerts 
            (user_id, token_symbol, alert_type, target_value, status, expires_at, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, symbol.upper(), alert_type.value, target_value, 
              AlertStatus.ACTIVE.value, 
              (datetime.utcnow() + timedelta(days=expires_days)).isoformat(),
              message, datetime.utcnow().isoformat()))
        
        await self._db.commit()
        
        cursor = await self._db.execute("SELECT * FROM price_alerts WHERE id = ?", (cursor.lastrowid,))
        row = await cursor.fetchone()
        return self._row_to_price_alert(row)
    
    async def get_user_alerts(self, user_id: int, status: AlertStatus = None) -> List[PriceAlert]:
        """Get user's alerts"""
        await self.initialize()
        
        if status:
            cursor = await self._db.execute(
                "SELECT * FROM price_alerts WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
                (user_id, status.value)
            )
        else:
            cursor = await self._db.execute(
                "SELECT * FROM price_alerts WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
        
        rows = await cursor.fetchall()
        return [self._row_to_price_alert(row) for row in rows]
    
    async def get_active_alerts(self) -> List[PriceAlert]:
        """Get all active alerts for monitoring"""
        await self.initialize()
        cursor = await self._db.execute(
            "SELECT * FROM price_alerts WHERE status = 'active' AND (expires_at IS NULL OR expires_at > ?)",
            (datetime.utcnow().isoformat(),)
        )
        rows = await cursor.fetchall()
        return [self._row_to_price_alert(row) for row in rows]
    
    async def trigger_alert(self, alert_id: int):
        """Mark alert as triggered"""
        await self.initialize()
        await self._db.execute(
            "UPDATE price_alerts SET status = ?, triggered_at = ? WHERE id = ?",
            (AlertStatus.TRIGGERED.value, datetime.utcnow().isoformat(), alert_id)
        )
        await self._db.commit()
    
    async def cancel_alert(self, alert_id: int):
        """Cancel an alert"""
        await self.initialize()
        await self._db.execute(
            "UPDATE price_alerts SET status = ? WHERE id = ?",
            (AlertStatus.CANCELLED.value, alert_id)
        )
        await self._db.commit()
    
    def _row_to_price_alert(self, row) -> PriceAlert:
        """Convert row to PriceAlert object"""
        triggered_at = row['triggered_at'] if row['triggered_at'] else None
        if triggered_at:
            triggered_at = datetime.fromisoformat(triggered_at)
        
        expires_at = row['expires_at'] if row['expires_at'] else None
        if expires_at:
            expires_at = datetime.fromisoformat(expires_at)
        
        return PriceAlert(
            id=row['id'],
            user_id=row['user_id'],
            token_symbol=row['token_symbol'],
            alert_type=AlertType(row['alert_type']),
            target_value=row['target_value'],
            status=AlertStatus(row['status']),
            created_at=datetime.fromisoformat(row['created_at']),
            triggered_at=triggered_at,
            expires_at=expires_at,
            message=row['message']
        )
    
    # ============ TRADING SIGNALS METHODS ============
    
    async def save_signal(self, signal: TradingSignal) -> int:
        """Save a trading signal"""
        await self.initialize()
        
        rationale_json = ",".join(signal.rationale) if signal.rationale else ""
        risks_json = ",".join(signal.risks) if signal.risks else ""
        
        cursor = await self._db.execute("""
            INSERT INTO trading_signals 
            (token_symbol, token_name, recommendation, confidence, entry_price, 
             target_price, stop_loss, ai_score, social_score, whale_score, 
             technical_score, volume_score, rationale, risks, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            signal.token_symbol, signal.token_name, 
            signal.recommendation.value, signal.confidence,
            signal.entry_price, signal.target_price, signal.stop_loss,
            signal.ai_score, signal.social_score, signal.whale_score,
            signal.technical_score, signal.volume_score,
            rationale_json, risks_json, signal.status,
            datetime.utcnow().isoformat()
        ))
        
        await self._db.commit()
        return cursor.lastrowid
    
    async def get_active_signals(self, token_symbol: str = None) -> List[TradingSignal]:
        """Get active trading signals"""
        await self.initialize()
        
        if token_symbol:
            cursor = await self._db.execute(
                "SELECT * FROM trading_signals WHERE token_symbol = ? AND status = 'active' ORDER BY created_at DESC",
                (token_symbol.upper(),)
            )
        else:
            cursor = await self._db.execute(
                "SELECT * FROM trading_signals WHERE status = 'active' ORDER BY created_at DESC LIMIT 100"
            )
        
        rows = await cursor.fetchall()
        return [self._row_to_signal(row) for row in rows]
    
    async def expire_old_signals(self, hours: int = 24):
        """Expire signals older than specified hours"""
        await self.initialize()
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        await self._db.execute(
            "UPDATE trading_signals SET status = 'expired' WHERE status = 'active' AND created_at < ?",
            (cutoff.isoformat(),)
        )
        await self._db.commit()
    
    def _row_to_signal(self, row) -> TradingSignal:
        """Convert row to TradingSignal object"""
        rationale_str = row['rationale'] if row['rationale'] else ""
        rationale = [r for r in rationale_str.split(",") if r]
        
        risks_str = row['risks'] if row['risks'] else ""
        risks = [r for r in risks_str.split(",") if r]
        
        triggered_at = row['triggered_at'] if row['triggered_at'] else None
        if triggered_at:
            triggered_at = datetime.fromisoformat(triggered_at)
        
        return TradingSignal(
            id=row['id'],
            token_symbol=row['token_symbol'],
            token_name=row['token_name'],
            recommendation=Recommendation(row['recommendation']),
            confidence=row['confidence'],
            entry_price=row['entry_price'],
            target_price=row['target_price'],
            stop_loss=row['stop_loss'],
            ai_score=row['ai_score'] or 0,
            social_score=row['social_score'] or 0,
            whale_score=row['whale_score'] or 0,
            technical_score=row['technical_score'] or 0,
            volume_score=row['volume_score'] or 0,
            rationale=rationale,
            risks=risks,
            status=row['status'],
            created_at=datetime.fromisoformat(row['created_at']),
            triggered_at=triggered_at
        )
    
    # ============ STATS METHODS ============
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        await self.initialize()
        
        cursor = await self._db.execute("SELECT COUNT(*) as count FROM users")
        users_count = (await cursor.fetchone())['count']
        
        cursor = await self._db.execute("SELECT COUNT(*) as count FROM watched_tokens")
        watched_count = (await cursor.fetchone())['count']
        
        cursor = await self._db.execute("SELECT COUNT(*) as count FROM price_alerts WHERE status = 'active'")
        active_alerts = (await cursor.fetchone())['count']
        
        cursor = await self._db.execute("SELECT COUNT(*) as count FROM trading_signals WHERE status = 'active'")
        active_signals = (await cursor.fetchone())['count']
        
        return {
            "users": users_count,
            "watched_tokens": watched_count,
            "active_alerts": active_alerts,
            "active_signals": active_signals
        }
    
    async def close(self):
        """Close database connection"""
        if self._db:
            await self._db.close()
            self._db = None
