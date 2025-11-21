# ==================== scripts/clear_cache.py ====================

"""
Скрипт очищення кешу
Запускати: python scripts/clear_cache.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database.repository import DatabaseRepository
from core.cache.cache_manager import CacheManager


def clear_cache():
    """Очищення кешу"""
    print("=" * 50)
    print("Web Assistant - Clear Cache")
    print("=" * 50)
    
    repo = DatabaseRepository()
    cache_manager = CacheManager(repo)
    
    # Статистика перед очищенням
    stats_before = cache_manager.get_cache_stats()
    print(f"\n📊 Cache statistics:")
    print(f"   - Total entries: {stats_before['total_entries']}")
    print(f"   - Valid entries: {stats_before['valid_entries']}")
    print(f"   - Total hits: {stats_before['total_hits']}")
    
    # Очищення
    print("\n🗑️  Clearing cache...")
    count = cache_manager.clear_cache()
    
    print(f"✅ Cleared {count} cache entries")
    
    # Очищення прострочених
    print("\n🧹 Cleaning expired entries...")
    expired_count = cache_manager.clean_expired_cache()
    print(f"✅ Removed {expired_count} expired entries")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    clear_cache()