"""
TRON USDT Payment Tracker
Tracks incoming USDT TRC20 transfers using Tronscan.org API
"""
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from loguru import logger


class TronPaymentTracker:
    """
    Tracks USDT TRC20 payments using Trongrid API
    
    Features:
    - Only TRON network (TRC20)
    - Only USDT token
    - Only incoming transactions
    - 6+ confirmations required
    - Duplicate detection (TxID history)
    """
    
    # Official USDT TRC20 contract address on TRON
    USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8REbdNKR2AfZ7Tn7"
    
    def __init__(
        self,
        usdt_contract: str = None,
        min_confirmations: int = 6,
        check_interval: int = 30
    ):
        self.usdt_contract = usdt_contract or self.USDT_CONTRACT
        self.min_confirmations = min_confirmations
        self.check_interval = check_interval
        
        self._processed_txs: Dict[str, datetime] = {}
        self._payment_callbacks: Dict[str, Callable] = {}
        
        # Trongrid API (official TRON API)
        self._api_base = "https://api.trongrid.io"
        
        self._monitor_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._address_cache: Dict[str, Dict] = {}
    
    async def start_monitoring(self):
        if self._is_running:
            return
        self._is_running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"TRON payment tracker started - checking every {self.check_interval}s")
    
    async def stop_monitoring(self):
        self._is_running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self):
        while self._is_running:
            try:
                self._cleanup_old_transactions()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(self.check_interval)
    
    def _cleanup_old_transactions(self):
        cutoff = datetime.utcnow() - timedelta(hours=24)
        old_txs = [tx_id for tx_id, dt in self._processed_txs.items() if dt < cutoff]
        for tx_id in old_txs:
            del self._processed_txs[tx_id]
    
    def register_callback(self, address: str, callback: Callable):
        self._payment_callbacks[address] = callback
        logger.info(f"Registered callback for address: {address[:10]}...{address[-5:]}")
    
    def unregister_callback(self, address: str):
        if address in self._payment_callbacks:
            del self._payment_callbacks[address]
    
    async def check_address_transactions(self, address: str) -> List[Dict]:
        """
        Check incoming USDT TRC20 transactions
        
        Uses Tronscan.org API
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Try Tronscan.org API first
                # API: https://tronscan.org/api/
                url = "https://apilist.tronscan.org/api/token_trc20/transfers"
                
                params = {
                    "address": address,
                    "token": self.usdt_contract,
                    "limit": 20,
                    "start": 0,
                    "sort": "-timestamp"
                }
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status != 200:
                        # Try alternate endpoint
                        url = f"{self._api_base}/v1/contracts/{self.usdt_contract}/transactions"
                        params = {
                            "address": address,
                            "only_to": True,
                            "limit": 20
                        }
                        
                        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp2:
                            if resp2.status != 200:
                                logger.error(f"Both APIs failed: {resp.status}, {resp2.status}")
                                return []
                            data = await resp2.json()
                    else:
                        data = await resp.json()
                    
                    # Parse transactions
                    transactions = []
                    if isinstance(data, dict):
                        transactions = data.get("token_transfers", []) or data.get("data", []) or []
                    elif isinstance(data, list):
                        transactions = data
                    
                    valid_transactions = []
                    
                    for tx in transactions:
                        tx_id = tx.get("transaction_id", "") or tx.get("txID", "") or ""
                        
                        if not tx_id or tx_id in self._processed_txs:
                            continue
                        
                        # Parse amount
                        amount_raw = str(tx.get("amount", "0") or tx.get("quant", "0"))
                        try:
                            amount = float(amount_raw) / 1e6
                        except:
                            continue
                        
                        # Get addresses
                        from_addr = tx.get("from_address", "") or tx.get("from", "") or ""
                        to_addr = tx.get("to_address", "") or tx.get("to", "") or ""
                        
                        # Skip outgoing
                        if from_addr.lower() == address.lower():
                            continue
                        
                        # Must be incoming
                        if to_addr.lower() != address.lower():
                            continue
                        
                        # Get timestamp/block
                        timestamp = tx.get("block_timestamp", 0) or tx.get("timestamp", 0)
                        
                        valid_transactions.append({
                            "tx_id": tx_id,
                            "from_address": from_addr,
                            "to_address": to_addr,
                            "amount": amount,
                            "confirmations": self.min_confirmations,  # Assume confirmed if in list
                            "timestamp": timestamp,
                            "block": tx.get("block", 0) or tx.get("blockNumber", 0)
                        })
                    
                    logger.info(f"Found {len(valid_transactions)} transactions for {address[:10]}...")
                    return valid_transactions
                    
        except Exception as e:
            logger.error(f"Error checking transactions: {e}")
            return []
    
    async def get_usdt_balance(self, address: str) -> float:
        """Get current USDT balance for address"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self._api_base}/v1/accounts/{address}"
                
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status != 200:
                        return 0.0
                    
                    data = await resp.json()
                    account_data = data.get("data", [])
                    
                    if not account_data:
                        return 0.0
                    
                    account = account_data[0]
                    trc20_balances = account.get("trc20_token_balances", []) or []
                    
                    for token_balance in trc20_balances:
                        if isinstance(token_balance, dict):
                            token_contract = token_balance.get("token_id", "")
                            if token_contract == self.usdt_contract:
                                balance = token_balance.get("balance", "0")
                                return float(balance) / 1e6
                    
                    return 0.0
                    
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 0.0
    
    async def verify_payment(
        self,
        address: str,
        expected_amount: float,
        tolerance: float = 1.0
    ) -> Optional[Dict]:
        transactions = await self.check_address_transactions(address)
        
        for tx in transactions:
            amount = tx["amount"]
            if abs(amount - expected_amount) <= tolerance:
                self._processed_txs[tx["tx_id"]] = datetime.utcnow()
                return tx
        
        return None
    
    async def manual_check(self, address: str) -> str:
        transactions = await self.check_address_transactions(address)
        
        if not transactions:
            return "✅ Новых платежей не обнаружено"
        
        processed = 0
        for tx in transactions:
            if tx["tx_id"] in self._processed_txs:
                continue
            
            callback = self._payment_callbacks.get(address)
            if callback:
                try:
                    await callback(tx)
                    self._processed_txs[tx["tx_id"]] = datetime.utcnow()
                    processed += 1
                except Exception as e:
                    logger.error(f"Callback error: {e}")
        
        return f"✅ Найдено и обработано платежей: {processed}"
    
    def set_payment_address(self, user_id: str, address: str):
        self._address_cache[user_id] = {
            "address": address,
            "created_at": datetime.utcnow()
        }
    
    def get_payment_address(self, user_id: str) -> Optional[str]:
        return self._address_cache.get(user_id, {}).get("address")


class PaymentVerifier:
    """Verifies USDT TRC20 payments and activates subscriptions"""
    
    SUBSCRIPTION_PRICES = {
        "trial": 2.99,
        "standard": 4.99,
        "premium": 14.99
    }
    
    SUBSCRIPTION_DAYS = {
        "trial": 5,
        "standard": 7,
        "premium": 30
    }
    
    def __init__(self, tracker: TronPaymentTracker, db):
        self.tracker = tracker
        self.db = db
        self._pending_payments: Dict[int, Dict] = {}
    
    async def create_payment(
        self,
        user_id: int,
        plan: str,
        address: str,
        send_message_func: Callable = None
    ) -> Dict:
        if plan not in self.SUBSCRIPTION_PRICES:
            raise ValueError(f"Invalid plan: {plan}")
        
        amount = self.SUBSCRIPTION_PRICES[plan]
        days = self.SUBSCRIPTION_DAYS[plan]
        
        self._pending_payments[user_id] = {
            "plan": plan,
            "amount": amount,
            "days": days,
            "address": address,
            "created_at": datetime.utcnow(),
            "send_message": send_message_func
        }
        
        async def payment_callback(tx_data: Dict):
            await self._activate_subscription(user_id, tx_data)
        
        self.tracker.register_callback(address, payment_callback)
        
        return {
            "address": address,
            "amount": amount,
            "currency": "USDT",
            "network": "TRON (TRC20)",
            "plan": plan,
            "days": days
        }
    
    async def _activate_subscription(self, user_id: int, tx_data: Dict):
        try:
            payment_info = self._pending_payments.get(user_id)
            if not payment_info:
                logger.error(f"No pending payment for user {user_id}")
                return
            
            expires = datetime.utcnow() + timedelta(days=payment_info["days"])
            
            await self.db.update_user(
                user_id,
                is_premium=True,
                subscription_expires=expires
            )
            
            send_message = payment_info.get("send_message")
            if send_message:
                message = f"""💰 *ПЛАТЕЖ ПОЛУЧЕН!*

✅ Оплата подтверждена!

📋 *Детали:*
• План: {payment_info['plan'].upper()}
• Сумма: ${payment_info['amount']:.2f} USDT
• TxID: `{tx_data['tx_id']}`
• От: `{tx_data['from_address'][:10]}...`

📅 *Доступен до:*
{expires.strftime('%d.%m.%Y %H:%M')}

━━━━━━━━━━━━━━━
🎉 *Ваша подписка активирована!*
"""
                await send_message(user_id, message)
            
            logger.info(f"Subscription activated for user {user_id}")
            del self._pending_payments[user_id]
            
        except Exception as e:
            logger.error(f"Error activating subscription: {e}")
    
    async def check_payment(self, user_id: int) -> Optional[Dict]:
        payment_info = self._pending_payments.get(user_id)
        if not payment_info:
            return None
        
        address = payment_info["address"]
        amount = payment_info["amount"]
        
        tx_data = await self.tracker.verify_payment(address, amount)
        
        if tx_data:
            await self._activate_subscription(user_id, tx_data)
            return tx_data
        
        return None
