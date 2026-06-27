"""
Whale Analyzer - Tracks and analyzes whale activity
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import aiohttp
from loguru import logger

from ..config.settings import API_ENDPOINTS, WHALE_THRESHOLDS


@dataclass
class WhaleMetrics:
    """Whale activity metrics"""
    large_transactions: int = 0
    total_whale_volume: float = 0.0
    
    large_buys: int = 0
    large_sells: int = 0
    
    accumulation_score: float = 0.0
    distribution_score: float = 0.0
    
    new_wallets: int = 0
    suspicious_activity: int = 0
    
    concentration_ratio: float = 0.0
    balance_changes: List[Dict] = None
    
    def __post_init__(self):
        if self.balance_changes is None:
            self.balance_changes = []


class WhaleAnalyzer:
    """
    Analyzes whale activity and large transactions
    
    Sources:
    - Whale Alert API
    - DexScreener
    - Blockchain explorers (Etherscan, Solscan, etc.)
    - Arkham Intelligence
    - Nansen
    - DeBank
    - Lookonchain
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.api_keys = self.config.get("api_keys", {})
        self.session: Optional[aiohttp.ClientSession] = None
        
        # API key for Whale Alert
        self.whale_alert_key = self.api_keys.get("whale_alert", "")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def analyze(self, token: str) -> Dict[str, Any]:
        """
        Perform whale activity analysis
        
        Args:
            token: Token symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Dict with whale analysis results including score (0-100)
        """
        try:
            logger.info(f"Starting whale analysis for {token}")
            
            # Gather data from multiple sources
            whale_alert_data = await self._get_whale_alert_transactions(token)
            dex_data = await self._get_dex_large_transactions(token)
            on_chain_data = await self._get_on_chain_metrics(token)
            
            # Aggregate metrics
            metrics = WhaleMetrics()
            
            # Whale Alert data
            if whale_alert_data:
                metrics.large_transactions = whale_alert_data.get("count", 0)
                metrics.total_whale_volume = whale_alert_data.get("volume_usd", 0)
                metrics.large_buys = whale_alert_data.get("buys", 0)
                metrics.large_sells = whale_alert_data.get("sells", 0)
            
            # DEX data
            if dex_data:
                metrics.large_transactions += dex_data.get("count", 0)
                metrics.total_whale_volume += dex_data.get("volume_usd", 0)
            
            # On-chain data
            if on_chain_data:
                metrics.new_wallets = on_chain_data.get("new_wallets", 0)
                metrics.concentration_ratio = on_chain_data.get("concentration", 0)
                metrics.balance_changes = on_chain_data.get("changes", [])
            
            # Calculate accumulation/distribution
            metrics.accumulation_score = self._calculate_accumulation(
                metrics.large_buys,
                metrics.large_sells,
                metrics.new_wallets
            )
            metrics.distribution_score = self._calculate_distribution(
                metrics.large_sells,
                metrics.large_buys,
                metrics.concentration_ratio
            )
            
            # Detect suspicious activity
            metrics.suspicious_activity = self._detect_suspicious_activity(
                metrics.balance_changes
            )
            
            # Calculate whale score
            score = self._calculate_whale_score(metrics)
            
            # Determine dumping risk
            dumping_risk = metrics.large_sells > metrics.large_buys * 2
            accumulation_signals = int(metrics.accumulation_score / 20)
            distribution_signals = int(metrics.distribution_score / 20)
            
            return {
                "success": True,
                "score": score,
                "whale_score_label": self._get_whale_label(score),
                "data": {
                    "large_transactions": metrics.large_transactions,
                    "total_whale_volume_usd": metrics.total_whale_volume,
                    "large_buys": metrics.large_buys,
                    "large_sells": metrics.large_sells,
                    "accumulation_score": metrics.accumulation_score,
                    "distribution_score": metrics.distribution_score,
                    "new_wallets": metrics.new_wallets,
                    "concentration_ratio": metrics.concentration_ratio,
                    "suspicious_activity": metrics.suspicious_activity
                },
                "accumulation_signals": accumulation_signals,
                "distribution_signals": distribution_signals,
                "large_buys": metrics.large_buys,
                "large_sells": metrics.large_sells,
                "dumping_risk": dumping_risk,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Whale analysis error: {e}")
            return {
                "success": False,
                "score": 50,
                "error": str(e)
            }
    
    async def _get_whale_alert_transactions(self, token: str) -> Dict[str, Any]:
        """Get whale transactions from Whale Alert API"""
        try:
            if not self.whale_alert_key:
                # Demo mode - return simulated data
                logger.info("Whale Alert API key not configured, using demo data")
                return self._generate_demo_whale_data(token)
            
            session = await self._get_session()
            
            # Whale Alert API
            url = f"{API_ENDPOINTS.WHALE_ALERT}/transactions"
            params = {
                "api_key": self.whale_alert_key,
                "min_value": int(WHALE_THRESHOLDS.MIN_TRANSACTION_USD),
                "symbol": token.upper()
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    transactions = data.get("transactions", [])
                    
                    buys = 0
                    sells = 0
                    volume = 0
                    
                    for tx in transactions:
                        amount = tx.get("amount_usd", 0)
                        tx_type = tx.get("transaction_type", "")
                        
                        volume += amount
                        
                        if amount > WHALE_THRESHOLDS.LARGE_TRANSACTION_USD:
                            if tx_type == "buy":
                                buys += 1
                            elif tx_type == "sell":
                                sells += 1
                    
                    return {
                        "count": len(transactions),
                        "volume_usd": volume,
                        "buys": buys,
                        "sells": sells
                    }
            
            return {}
            
        except Exception as e:
            logger.warning(f"Whale Alert API error: {e}")
            return self._generate_demo_whale_data(token)
    
    def _generate_demo_whale_data(self, token: str) -> Dict[str, Any]:
        """Generate demo whale data for testing"""
        # Simulated data for demo purposes
        import random
        random.seed(hash(token) % 1000)
        
        transactions = random.randint(5, 50)
        buys = random.randint(0, transactions)
        sells = transactions - buys
        
        return {
            "count": transactions,
            "volume_usd": random.randint(100000, 5000000),
            "buys": buys,
            "sells": sells
        }
    
    async def _get_dex_large_transactions(self, token: str) -> Dict[str, Any]:
        """Get large DEX transactions"""
        try:
            session = await self._get_session()
            
            # DexScreener API
            url = f"{API_ENDPOINTS.DEX_SCREENER}/latest/dex/pairs"
            params = {"network": "solana"}  # Can be ethereum, bsc, etc.
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    pairs = data.get("pairs", [])
                    
                    # Filter for the token
                    relevant_pairs = [
                        p for p in pairs 
                        if token.upper() in p.get("baseToken", {}).get("symbol", "").upper()
                    ]
                    
                    if relevant_pairs:
                        pair = relevant_pairs[0]
                        return {
                            "count": pair.get("txns", {}).get("h24", 0),
                            "volume_usd": pair.get("volume", {}).get("h24", 0)
                        }
            
            return {}
            
        except Exception as e:
            logger.warning(f"DexScreener API error: {e}")
            return {}
    
    async def _get_on_chain_metrics(self, token: str) -> Dict[str, Any]:
        """Get on-chain metrics for the token"""
        try:
            # In production, use:
            # - Arkham Intelligence
            # - Nansen
            # - DeBank
            # - Blockchain explorers API
            
            # Demo data
            import random
            random.seed(hash(token) % 1000)
            
            return {
                "new_wallets": random.randint(0, 100),
                "concentration": random.uniform(0.1, 0.9),
                "changes": []
            }
            
        except Exception as e:
            logger.warning(f"On-chain metrics error: {e}")
            return {}
    
    def _calculate_accumulation(
        self, 
        buys: int, 
        sells: int, 
        new_wallets: int
    ) -> float:
        """Calculate accumulation score (0-100)"""
        if buys == 0 and sells == 0:
            return 0
        
        # More buys than sells = accumulation
        buy_ratio = buys / max(1, buys + sells)
        
        # Score based on buy ratio and new wallets
        base_score = buy_ratio * 60
        wallet_boost = min(40, new_wallets * 2)
        
        return min(100, base_score + wallet_boost)
    
    def _calculate_distribution(
        self,
        sells: int,
        buys: int,
        concentration: float
    ) -> float:
        """Calculate distribution score (0-100)"""
        if sells == 0 and buys == 0:
            return 0
        
        # More sells than buys = distribution
        sell_ratio = sells / max(1, sells + buys)
        
        # High concentration + sells = distribution
        base_score = sell_ratio * 60
        concentration_boost = concentration * 40 if sells > buys else 0
        
        return min(100, base_score + concentration_boost)
    
    def _detect_suspicious_activity(self, balance_changes: List[Dict]) -> int:
        """Detect suspicious whale activity"""
        suspicious_count = 0
        
        for change in balance_changes:
            # Check for sudden large changes
            if change.get("change_percent", 0) > 50:
                suspicious_count += 1
            
            # Check for newly created wallets
            if change.get("is_new", False) and change.get("balance_usd", 0) > 100000:
                suspicious_count += 1
        
        return suspicious_count
    
    def _get_whale_label(self, score: float) -> str:
        """Get whale activity label"""
        if score >= 80:
            return "🟢 Сильный бычий сигнал"
        elif score >= 60:
            return "🟡 Умеренная активность"
        elif score >= 40:
            return "⚪ Нейтральная активность"
        elif score >= 20:
            return "🟠 Осторожность"
        else:
            return "🔴 Медвежий сигнал"
    
    def _calculate_whale_score(self, metrics: WhaleMetrics) -> float:
        """
        Calculate final whale score (0-100)
        
        Higher score = more bullish whale activity
        
        Factors:
        - Accumulation: 35%
        - Buy/Sell ratio: 30%
        - New wallets: 20%
        - Volume: 15%
        """
        # Accumulation score
        accum_score = metrics.accumulation_score * 0.35
        
        # Buy/Sell ratio
        total_tx = metrics.large_buys + metrics.large_sells
        if total_tx > 0:
            buy_ratio = metrics.large_buys / total_tx
        else:
            buy_ratio = 0.5
        buy_sell_score = buy_ratio * 30
        
        # New wallets score
        wallet_score = min(20, metrics.new_wallets * 0.5)
        
        # Volume score (log scale)
        if metrics.total_whale_volume > 0:
            volume_score = min(15, (metrics.total_whale_volume / 1000000) * 3)
        else:
            volume_score = 0
        
        total = accum_score + buy_sell_score + wallet_score + volume_score
        
        return min(100, max(0, total))
