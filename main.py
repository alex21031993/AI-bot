"""
Crypto Intelligence Agent - Main Entry Point

A comprehensive cryptocurrency analysis bot with:
- User authorization and tracking
- Automatic BUY/SELL/HOLD signals
- 24/7 background monitoring
- Price alerts
- Trading recommendations
"""
import asyncio
import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from loguru import logger

from crypto_intelligence_agent.telegram.advanced_bot import CryptoBot
from crypto_intelligence_agent.agents.crypto_agent import CryptoIntelligenceAgent


def setup_logging():
    """Configure logging"""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # Also log to file
    Path("logs").mkdir(exist_ok=True)
    logger.add(
        "logs/crypto_agent_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG"
    )


def load_config():
    """Load configuration from environment"""
    load_dotenv()
    
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    admin_ids = os.getenv("ADMIN_USER_IDS", "")
    
    # Parse admin IDs
    admin_list = []
    if admin_ids:
        try:
            admin_list = [int(x.strip()) for x in admin_ids.split(",")]
        except ValueError:
            pass
    
    demo_mode = os.getenv("DEMO_MODE", "true").lower() == "true"
    
    return {
        "telegram_token": telegram_token,
        "admin_ids": admin_list,
        "demo_mode": demo_mode
    }


async def test_agent():
    """Test the crypto agent"""
    logger.info("Testing Crypto Intelligence Agent...")
    
    agent = CryptoIntelligenceAgent()
    
    test_tokens = ["BTC", "ETH", "SOL"]
    
    for token in test_tokens:
        logger.info(f"\n{'='*50}\nAnalyzing {token}...\n{'='*50}")
        
        result = await agent.execute(token=token)
        
        if result.success:
            rec = result.data.get('recommendation', {})
            scores = result.data.get('scores', {})
            
            emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡', 'WAIT': '⚪'}
            e = emoji.get(rec.get('action', '?'), '?')
            
            logger.info(f"✅ {token} {e} {rec.get('action', '?')}")
            logger.info(f"   Score: {scores.get('total', 0):.1f}% | Confidence: {rec.get('confidence', 0):.0f}%")
            logger.info(f"   Price: ${result.data.get('price', 'N/A')}")
            
            for r in rec.get('rationale', [])[:2]:
                logger.info(f"   → {r}")
        else:
            logger.error(f"❌ {token} Analysis Failed: {result.error}")
    
    for analyzer in agent.analyzers.values():
        if hasattr(analyzer, 'close'):
            await analyzer.close()
    
    logger.info("\n✅ All tests completed!")


async def main():
    """Main entry point"""
    setup_logging()
    logger.info("🚀 Starting Crypto Intelligence Agent")
    logger.info("🐋 With 24/7 Auto-Signals & Monitoring")
    
    # Load configuration
    config = load_config()
    
    # If no Telegram token, run in test mode
    if not config["telegram_token"]:
        logger.warning("No Telegram bot token found. Running in test mode...")
        await test_agent()
        return
    
    # Create and initialize bot
    bot = CryptoBot(
        token=config["telegram_token"],
        admin_ids=config["admin_ids"]
    )
    
    # Initialize database and monitor
    await bot.initialize()
    
    logger.info("✅ Database initialized")
    logger.info("✅ Background monitor ready")
    logger.info("📱 Starting Telegram bot with auto-signals...")
    
    # Start monitoring in background
    asyncio.create_task(bot.start_monitoring())
    
    try:
        # Create and run app
        app = bot.create_app()
        app.run_polling()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        await bot.stop_monitoring()
        await bot.db.close()


if __name__ == "__main__":
    asyncio.run(main())
