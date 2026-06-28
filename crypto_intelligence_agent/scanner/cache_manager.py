"""
Cache Manager - Управление кэшированием API ответов
"""
import json
import time
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from loguru import logger


class CacheManager:
    """
    Простой кэш для API ответов
    
    Особенности:
    - TTL (time to live)
    - Автоочистка устаревших записей
    - Ограничение размера
    """
    
    def __init__(self, max_size: int = 100, default_ttl: int = 60):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl  # секунды
    
    def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Проверяем TTL
        if time.time() > entry["expires_at"]:
            del self.cache[key]
            return None
        
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Установить значение в кэш"""
        if ttl is None:
            ttl = self.default_ttl
        
        # Очищаем старые записи если достигли лимита
        if len(self.cache) >= self.max_size:
            self._cleanup()
        
        self.cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
            "created_at": time.time()
        }
    
    def _cleanup(self) -> None:
        """Очистка устаревших записей"""
        now = time.time()
        expired_keys = [k for k, v in self.cache.items() if now > v["expires_at"]]
        
        for key in expired_keys:
            del self.cache[key]
        
        # Если всё ещё много - удаляем самые старые
        if len(self.cache) >= self.max_size:
            sorted_keys = sorted(self.cache.keys(), key=lambda k: self.cache[k]["created_at"])
            for key in sorted_keys[:self.max_size // 4]:
                del self.cache[key]
    
    def clear(self) -> None:
        """Очистить весь кэш"""
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Статистика кэша"""
        now = time.time()
        valid = sum(1 for v in self.cache.values() if now <= v["expires_at"])
        
        return {
            "total": len(self.cache),
            "valid": valid,
            "expired": len(self.cache) - valid,
            "max_size": self.max_size
        }


# Глобальный экземпляр
api_cache = CacheManager(max_size=200, default_ttl=60)