"""
Crypto Intelligence Agent - Main Entry Point

100% Button-Only Telegram Bot
All interaction through buttons ONLY
Admin password only allowed text input
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from loguru import logger

from crypto_intelligence_agent.telegram.button_bot import ButtonBot
from crypto_intelligence_agent.agents.crypto_agent import CryptoIntelligenceAgent


def setup_logging():
    """Configure logging"""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <message>",
        level="INFO"
    )
    
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
    
    admin_list = []
    if admin_ids:
        try:
            admin_list = [int(x.strip()) for x in admin_ids.split(",")]
        except ValueError:
            pass
    
    return {
        "telegram_token": telegram_token,
        "admin_ids": admin_list
    }


async def test_agent():
    """Test the crypto agent"""
    logger.info("Testing Crypto Intelligence Agent...")
    
    agent = CryptoIntelligenceAgent()
    test_tokens = ["BTC", "ETH", "SOL"]
    
    for token in test_tokens:
        result = await agent.execute(token=token)
        
        if result.success:
            rec = result.data.get('recommendation', {})
            scores = result.data.get('scores', {})
            
            emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡', 'WAIT': '⚪'}
            e = emoji.get(rec.get('action', '?'), '?')
            
            logger.info(f"✅ {token} {e} {rec.get('action', '?')} | Score: {scores.get('total', 0):.0f}%")
        else:
            logger.error(f"❌ {token} failed")
    
    for analyzer in agent.analyzers.values():
        if hasattr(analyzer, 'close'):
            await analyzer.close()
    
    logger.info("✅ Tests completed!")


async def main():
    """Main entry point"""
    setup_logging()
    logger.info("🚀 Starting Crypto Intelligence Bot")
    logger.info("📱 100% Button-Only Interface")
    
    config = load_config()
    
    if not config["telegram_token"]:
        logger.warning("No Telegram token. Running test mode...")
        await test_agent()
        return
    
    # Create button-only bot
    bot = ButtonBot(
        token=config["telegram_token"],
        admin_ids=config["admin_ids"]
    )
    
    await bot.initialize()
    
    logger.info("✅ Database initialized")
    logger.info("✅ Background monitor ready")
    logger.info("📱 Starting button-only bot...")
    
    asyncio.create_task(bot.start_monitoring())
    
    try:
        app = bot.create_app()
        app.run_polling(allowed_updates=["callback_query", "message"])
    except KeyboardInterrupt:
        logger.info("Bot stopped")
    finally:
        await bot.stop_monitoring()
        await bot.db.close()


if __name__ == "__main__":
    asyncio.run(main())
