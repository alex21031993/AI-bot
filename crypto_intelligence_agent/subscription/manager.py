"""
Subscription Manager - Handles user subscriptions and payments
"""
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import aiosqlite
from loguru import logger

from ..config.settings import SUBSCRIPTION_PLANS


@dataclass
class Subscription:
    """User subscription data"""
    user_id: int
    plan_name: str
    plan_type: str  # TRIAL, STANDARD, PREMIUM
    started_at: datetime
    expires_at: datetime
    requests_used: int
    requests_limit: int
    tx_hash: Optional[str] = None
    is_active: bool = True
    
    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
    
    @property
    def requests_remaining(self) -> int:
        if self.requests_limit == float('inf'):
            return float('inf')
        return max(0, self.requests_limit - self.requests_used)
    
    @property
    def days_remaining(self) -> int:
        if self.is_expired:
            return 0
        return (self.expires_at - datetime.utcnow()).days


class SubscriptionManager:
    """
    Manages user subscriptions and access control
    
    Features:
    - Subscription creation and validation
    - Request counting
    - Wallet payment verification
    - Admin access
    """
    
    def __init__(self, db_path: str = "subscriptions.db"):
        self.db_path = db_path
        self._db = None
        self._init_lock = asyncio.Lock()
    
    async def _ensure_init(self):
        """Ensure database is initialized"""
        async with self._init_lock:
            if self._db is None:
                self._db = await aiosqlite.connect(self.db_path)
                await self._create_tables()
    
    async def _create_tables(self):
        """Create database tables"""
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER PRIMARY KEY,
                plan_name TEXT NOT NULL,
                plan_type TEXT NOT NULL,
                started_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                requests_used INTEGER DEFAULT 0,
                requests_limit INTEGER NOT NULL,
                tx_hash TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS payment_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tx_hash TEXT NOT NULL,
                amount TEXT NOT NULL,
                currency TEXT NOT NULL,
                status TEXT NOT NULL,
                plan_type TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                user_id INTEGER PRIMARY KEY,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self._db.commit()
    
    async def get_subscription(self, user_id: int) -> Optional[Subscription]:
        """Get user's active subscription"""
        await self._ensure_init()
        
        cursor = await self._db.execute(
            """
            SELECT user_id, plan_name, plan_type, started_at, expires_at, 
                   requests_used, requests_limit, tx_hash, is_active
            FROM subscriptions
            WHERE user_id = ? AND is_active = 1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id,)
        )
        
        row = await cursor.fetchone()
        
        if row:
            return Subscription(
                user_id=row[0],
                plan_name=row[1],
                plan_type=row[2],
                started_at=datetime.fromisoformat(row[3]),
                expires_at=datetime.fromisoformat(row[4]),
                requests_used=row[5],
                requests_limit=row[6],
                tx_hash=row[7],
                is_active=bool(row[8])
            )
        
        return None
    
    async def create_subscription(
        self,
        user_id: int,
        plan_type: str,
        tx_hash: Optional[str] = None
    ) -> Optional[Subscription]:
        """Create a new subscription"""
        await self._ensure_init()
        
        # Get plan details
        plan = getattr(SUBSCRIPTION_PLANS, plan_type, None)
        if not plan:
            logger.error(f"Invalid plan type: {plan_type}")
            return None
        
        now = datetime.utcnow()
        expires_at = now + timedelta(days=plan["duration_days"])
        
        # Deactivate any existing subscription
        await self._db.execute(
            "UPDATE subscriptions SET is_active = 0 WHERE user_id = ?",
            (user_id,)
        )
        
        # Create new subscription
        await self._db.execute(
            """
            INSERT INTO subscriptions 
            (user_id, plan_name, plan_type, started_at, expires_at, 
             requests_used, requests_limit, tx_hash, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                user_id,
                plan["name"],
                plan_type,
                now.isoformat(),
                expires_at.isoformat(),
                0,
                plan["max_requests"],
                tx_hash
            )
        )
        
        # Log payment if tx_hash provided
        if tx_hash:
            await self._log_payment(
                user_id=user_id,
                tx_hash=tx_hash,
                amount=plan["price_usd"],
                currency="USD",
                status="confirmed",
                plan_type=plan_type
            )
        
        await self._db.commit()
        
        return await self.get_subscription(user_id)
    
    async def extend_subscription(
        self,
        user_id: int,
        plan_type: str,
        tx_hash: Optional[str] = None
    ) -> Optional[Subscription]:
        """Extend existing subscription or create new one"""
        existing = await self.get_subscription(user_id)
        
        if existing and not existing.is_expired:
            # Extend from current expiration
            plan = getattr(SUBSCRIPTION_PLANS, plan_type, None)
            if plan:
                new_expires = existing.expires_at + timedelta(days=plan["duration_days"])
                
                await self._db.execute(
                    """
                    UPDATE subscriptions
                    SET expires_at = ?,
                        requests_limit = CASE 
                            WHEN requests_limit = -1 THEN -1
                            ELSE requests_limit + ?
                        END,
                        is_active = 1
                    WHERE user_id = ?
                    """,
                    (
                        new_expires.isoformat(),
                        plan["max_requests"],
                        user_id
                    )
                )
                
                if tx_hash:
                    await self._log_payment(
                        user_id, tx_hash, plan["price_usd"], "USD", "confirmed", plan_type
                    )
                
                await self._db.commit()
        else:
            return await self.create_subscription(user_id, plan_type, tx_hash)
        
        return await self.get_subscription(user_id)
    
    async def cancel_subscription(self, user_id: int) -> bool:
        """Cancel user's subscription"""
        await self._ensure_init()
        
        cursor = await self._db.execute(
            "UPDATE subscriptions SET is_active = 0 WHERE user_id = ?",
            (user_id,)
        )
        await self._db.commit()
        
        return cursor.rowcount > 0
    
    async def get_remaining_requests(self, user_id: int) -> int:
        """Get remaining requests for user"""
        subscription = await self.get_subscription(user_id)
        
        if not subscription:
            return 0
        
        if subscription.is_expired:
            return 0
        
        return subscription.requests_remaining
    
    async def increment_requests(self, user_id: int) -> bool:
        """Increment request count for user"""
        await self._ensure_init()
        
        await self._db.execute(
            "UPDATE subscriptions SET requests_used = requests_used + 1 WHERE user_id = ?",
            (user_id,)
        )
        await self._db.commit()
        
        return True
    
    async def get_user_request_count(self, user_id: int) -> int:
        """Get total requests made by user"""
        subscription = await self.get_subscription(user_id)
        
        if not subscription:
            return 0
        
        return subscription.requests_used
    
    async def _log_payment(
        self,
        user_id: int,
        tx_hash: str,
        amount: str,
        currency: str,
        status: str,
        plan_type: str
    ):
        """Log payment transaction"""
        await self._db.execute(
            """
            INSERT INTO payment_logs 
            (user_id, tx_hash, amount, currency, status, plan_type)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, tx_hash, str(amount), currency, status, plan_type)
        )
    
    async def verify_payment(self, tx_hash: str) -> Optional[Dict]:
        """
        Verify blockchain payment
        
        In production, this would:
        1. Query the blockchain for the transaction
        2. Verify the amount matches the plan price
        3. Verify the destination address is correct
        4. Check for sufficient confirmations
        """
        await self._ensure_init()
        
        cursor = await self._db.execute(
            "SELECT * FROM payment_logs WHERE tx_hash = ?",
            (tx_hash,)
        )
        
        row = await cursor.fetchone()
        
        if row:
            return {
                "tx_hash": row[2],
                "amount": row[3],
                "status": row[5],
                "confirmed": row[5] == "confirmed"
            }
        
        return None
    
    async def add_admin(self, user_id: int) -> bool:
        """Add admin user"""
        await self._ensure_init()
        
        try:
            await self._db.execute(
                "INSERT OR IGNORE INTO admin_users (user_id) VALUES (?)",
                (user_id,)
            )
            await self._db.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding admin: {e}")
            return False
    
    async def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        await self._ensure_init()
        
        cursor = await self._db.execute(
            "SELECT 1 FROM admin_users WHERE user_id = ?",
            (user_id,)
        )
        
        row = await cursor.fetchone()
        return row is not None
    
    async def get_all_subscriptions(self) -> List[Subscription]:
        """Get all subscriptions (admin only)"""
        await self._ensure_init()
        
        cursor = await self._db.execute(
            "SELECT * FROM subscriptions ORDER BY created_at DESC"
        )
        
        rows = await cursor.fetchall()
        
        subscriptions = []
        for row in rows:
            subscriptions.append(Subscription(
                user_id=row[0],
                plan_name=row[1],
                plan_type=row[2],
                started_at=datetime.fromisoformat(row[3]),
                expires_at=datetime.fromisoformat(row[4]),
                requests_used=row[5],
                requests_limit=row[6],
                tx_hash=row[7],
                is_active=bool(row[8])
            ))
        
        return subscriptions
    
    async def get_stats(self) -> Dict:
        """Get subscription statistics"""
        await self._ensure_init()
        
        cursor = await self._db.execute(
            "SELECT COUNT(*) FROM subscriptions WHERE is_active = 1"
        )
        active_count = (await cursor.fetchone())[0]
        
        cursor = await self._db.execute(
            "SELECT COUNT(*) FROM subscriptions"
        )
        total_count = (await cursor.fetchone())[0]
        
        cursor = await self._db.execute(
            """
            SELECT SUM(requests_used) FROM subscriptions 
            WHERE is_active = 1 AND requests_limit != -1
            """
        )
        total_requests = (await cursor.fetchone())[0] or 0
        
        return {
            "active_subscriptions": active_count,
            "total_subscriptions": total_count,
            "total_requests": total_requests
        }
    
    async def close(self):
        """Close database connection"""
        if self._db:
            await self._db.close()
            self._db = None
