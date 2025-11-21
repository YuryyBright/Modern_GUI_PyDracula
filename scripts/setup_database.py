# ==================== scripts/setup_database.py ====================

"""
Скрипт ініціалізації бази даних
Запускати: python scripts/setup_database.py
"""

import sys
import os

# Додавання кореневої директорії до path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database.repository import DatabaseRepository
from core.config.settings import get_settings
from core.utils.logger import get_logger

logger = get_logger(__name__)


def setup_database():
    """Ініціалізація бази даних"""
    print("=" * 50)
    print("Web Assistant - Database Setup")
    print("=" * 50)
    
    settings = get_settings()
    db_path = settings.database.path
    
    print(f"\n📁 Database path: {db_path}")
    
    # Створення директорії якщо не існує
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"✅ Created directory: {db_dir}")
    
    # Ініціалізація репозиторію (автоматично створює таблиці)
    print("\n🔧 Initializing database...")
    repo = DatabaseRepository()
    
    # Перевірка таблиць
    from core.database.models import Base
    tables = Base.metadata.tables.keys()
    
    print(f"\n✅ Database initialized successfully!")
    print(f"📊 Created tables:")
    for table in tables:
        print(f"   - {table}")
    
    # Статистика
    stats = repo.get_statistics()
    print(f"\n📈 Current statistics:")
    print(f"   - Extractions: {stats['total_extractions']}")
    print(f"   - LLM Requests: {stats['total_llm_requests']}")
    print(f"   - Cached: {stats['total_cached']}")
    print(f"   - Sessions: {stats['total_sessions']}")
    
    print("\n" + "=" * 50)
    print("✅ Setup completed!")
    print("=" * 50)


if __name__ == "__main__":
    setup_database()