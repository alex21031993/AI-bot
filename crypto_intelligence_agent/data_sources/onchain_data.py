"""
OnChain Data Sources
Ончейн и китовые данные: Whale Alert, Arkham, Etherscan, Solscan и др.
"""

from typing import Dict, List


class OnChainDataSource:
    """
    Источники ончейн данных
    """
    
    SOURCES = {
        # КИТЫ
        "whale_alert": {
            "name": "Whale Alert",
            "url": "https://whale-alert.io",
            "api_url": "https://api.whale-alert.io",
            "priority": "HIGH",
            "description": "Крупные транзакции > $100K"
        },
        "arkham": {
            "name": "Arkham Intelligence",
            "url": "https://platform.arkhamintelligence.com",
            "api_url": "https://api.arkhamintelligence.com",
            "priority": "HIGH",
            "description": "Идентификация кошельков, Smart Money"
        },
        "nansen": {
            "name": "Nansen",
            "url": "https://www.nansen.ai",
            "priority": "MEDIUM",
            "description": "Smart Money анализ, классификация кошельков"
        },
        "bubblemaps": {
            "name": "Bubblemaps",
            "url": "https://bubblemaps.io",
            "priority": "MEDIUM",
            "description": "Визуализация связей кошельков"
        },
        
        # БЛОКЧЧЕЙН ЭКСПЛОРЕРЫ
        "etherscan": {
            "name": "Etherscan",
            "url": "https://etherscan.io",
            "api_url": "https://api.etherscan.io/api",
            "priority": "HIGH",
            "description": "Ethereum транзакции, контракты"
        },
        "solscan": {
            "name": "Solscan",
            "url": "https://solscan.io",
            "api_url": "https://api.solscan.io",
            "priority": "HIGH",
            "description": "Solana транзакции, токены"
        },
        "bscscan": {
            "name": "BscScan",
            "url": "https://bscscan.com",
            "api_url": "https://api.bscscan.com/api",
            "priority": "MEDIUM",
            "description": "BSC транзакции, контракты"
        },
        
        # SOLANA ЭКОСИСТЕМА
        "pump_fun": {
            "name": "Pump.fun",
            "url": "https://pump.fun",
            "priority": "HIGH",
            "description": "Новые мем-токены, ранние сигналы"
        },
        "gmgn": {
            "name": "GMGN",
            "url": "https://gmgn.ai",
            "api_url": "https://gmgn.ai/api",
            "priority": "HIGH",
            "description": "Solana токены, AI Score"
        },
        "photon": {
            "name": "Photon",
            "url": "https://photon-sol.tinyastro.io",
            "priority": "MEDIUM",
            "description": "Solana ликвидность, транзакции"
        },
        "jupiter": {
            "name": "Jupiter",
            "url": "https://jup.ag",
            "api_url": "https://api.jup.ag",
            "priority": "HIGH",
            "description": "DEX агрегатор, объёмы"
        },
        "raydium": {
            "name": "Raydium",
            "url": "https://raydium.io",
            "api_url": "https://api.raydium.io",
            "priority": "MEDIUM",
            "description": "Solana DEX пулы"
        },
    }
    
    @staticmethod
    def get_source_info() -> List[Dict]:
        """Информация о источниках"""
        return [
            {
                "name": data["name"],
                "url": data["url"],
                "priority": data["priority"],
                "description": data["description"],
                "category": "Ончейн и киты"
            }
            for data in OnChainDataSource.SOURCES.values()
        ]
    
    @staticmethod
    def get_solana_sources() -> List[Dict]:
        """Solana специфичные источники"""
        solana_keys = ["pump_fun", "gmgn", "photon", "jupiter", "raydium", "solscan"]
        return [
            {"name": OnChainDataSource.SOURCES[k]["name"], "url": OnChainDataSource.SOURCES[k]["url"]}
            for k in solana_keys if k in OnChainDataSource.SOURCES
        ]