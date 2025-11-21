"""
Cache Manager та приклад UI компонента
"""

# ==================== core/cache/cache_manager.py ====================

from typing import Optional
from datetime import datetime, timedelta

from core.database.repository import DatabaseRepository
from core.database.models import CachedResponse
from core.config.settings import get_settings
from core.utils.hasher import Hasher
from core.utils.logger import get_logger


logger = get_logger(__name__)


class CacheManager:
    """
    Менеджер кешування відповідей LLM
    Дедуплікація та швидкий доступ до раніше отриманих результатів
    """
    
    def __init__(self, db_repository: DatabaseRepository):
        """
        Ініціалізація менеджера кешу
        
        Args:
            db_repository: Репозиторій бази даних
        """
        self.db = db_repository
        self.settings = get_settings()
        self.enabled = self.settings.cache.enabled
        self.ttl = self.settings.cache.ttl
        self.max_size = self.settings.cache.max_size
        
        logger.info(f"CacheManager initialized: enabled={self.enabled}, ttl={self.ttl}s")
    
    def generate_cache_key(
        self,
        text: str,
        provider: str,
        prompt_type: str,
        model: Optional[str] = None
    ) -> str:
        """
        Генерація ключа кешу
        
        Args:
            text: Вхідний текст
            provider: Провайдер LLM
            prompt_type: Тип промпту
            model: Модель (опціонально)
            
        Returns:
            str: Унікальний ключ кешу
        """
        components = [
            text,
            provider,
            prompt_type
        ]
        
        if model:
            components.append(model)
        
        cache_key = Hasher.create_cache_key(*components)
        logger.debug(f"Generated cache key: {cache_key[:16]}...")
        
        return cache_key
    
    def get_cached_response(self, cache_key: str) -> Optional[CachedResponse]:
        """
        Отримання кешованої відповіді
        
        Args:
            cache_key: Ключ кешу
            
        Returns:
            CachedResponse або None
        """
        if not self.enabled:
            return None
        
        try:
            cached = self.db.get_cached_response(cache_key)
            
            if cached:
                logger.info(
                    f"Cache HIT: key={cache_key[:16]}..., "
                    f"hits={cached.hits}, "
                    f"age={self._get_cache_age(cached)}s"
                )
            else:
                logger.debug(f"Cache MISS: key={cache_key[:16]}...")
            
            return cached
            
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            return None
    
    def cache_response(
        self,
        cache_key: str,
        input_text: str,
        provider: str,
        model: str,
        prompt_template: str,
        response: str
    ) -> Optional[CachedResponse]:
        """
        Збереження відповіді в кеш
        
        Args:
            cache_key: Ключ кешу
            input_text: Вхідний текст
            provider: Провайдер
            model: Модель
            prompt_template: Шаблон промпту
            response: Відповідь LLM
            
        Returns:
            CachedResponse або None
        """
        if not self.enabled:
            return None
        
        try:
            # Перевірка розміру кешу
            current_size = self._get_cache_size()
            if current_size >= self.max_size:
                logger.warning(f"Cache full ({current_size}/{self.max_size}), cleaning...")
                self._clean_old_entries()
            
            # Хешування вхідного тексту
            input_hash = Hasher.hash_text(input_text)
            
            # Розрахунок часу експірації
            ttl_seconds = self.ttl if self.ttl > 0 else None
            
            # Збереження
            cached = self.db.add_cached_response(
                cache_key=cache_key,
                input_text=input_text,
                input_hash=input_hash,
                provider=provider,
                model=model,
                prompt_template=prompt_template,
                response=response,
                ttl_seconds=ttl_seconds
            )
            
            logger.info(f"Cached response saved: key={cache_key[:16]}...")
            return cached
            
        except Exception as e:
            logger.error(f"Cache save error: {e}")
            return None
    
    def invalidate_cache_entry(self, cache_key: str) -> bool:
        """
        Інвалідація конкретного запису кешу
        
        Args:
            cache_key: Ключ кешу
            
        Returns:
            bool: True якщо інвалідовано
        """
        try:
            count = self.db.invalidate_cache(cache_key)
            logger.info(f"Cache invalidated: {count} entries")
            return count > 0
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return False
    
    def clear_cache(self) -> int:
        """
        Повне очищення кешу
        
        Returns:
            int: Кількість видалених записів
        """
        try:
            count = self.db.invalidate_cache()
            logger.info(f"Cache cleared: {count} entries")
            return count
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
    
    def clean_expired_cache(self) -> int:
        """
        Видалення прострочених записів
        
        Returns:
            int: Кількість видалених записів
        """
        try:
            count = self.db.clean_expired_cache()
            logger.info(f"Expired cache cleaned: {count} entries")
            return count
        except Exception as e:
            logger.error(f"Expired cache cleaning error: {e}")
            return 0
    
    def get_cache_stats(self) -> dict:
        """
        Статистика кешу
        
        Returns:
            dict: Статистика
        """
        with self.db.get_session() as session:
            from sqlalchemy import func
            from core.database.models import CachedResponse
            
            stats = {
                'total_entries': session.query(func.count(CachedResponse.id)).scalar(),
                'valid_entries': session.query(func.count(CachedResponse.id)).filter(
                    CachedResponse.is_valid == True
                ).scalar(),
                'total_hits': session.query(func.sum(CachedResponse.hits)).scalar() or 0,
                'enabled': self.enabled,
                'max_size': self.max_size,
                'ttl': self.ttl
            }
            
            return stats
    
    def _get_cache_size(self) -> int:
        """Отримання поточного розміру кешу"""
        with self.db.get_session() as session:
            from sqlalchemy import func
            from core.database.models import CachedResponse
            
            return session.query(func.count(CachedResponse.id)).filter(
                CachedResponse.is_valid == True
            ).scalar()
    
    def _clean_old_entries(self, remove_count: Optional[int] = None) -> int:
        """
        Видалення старих записів кешу
        
        Args:
            remove_count: Кількість записів для видалення
            
        Returns:
            int: Кількість видалених записів
        """
        if remove_count is None:
            remove_count = max(1, int(self.max_size * 0.1))  # 10% від max_size
        
        # Спочатку видаляємо прострочені
        expired = self.clean_expired_cache()
        
        if expired >= remove_count:
            return expired
        
        # Якщо недостатньо, видаляємо найстаріші
        with self.db.get_session() as session:
            from core.database.models import CachedResponse
            from sqlalchemy import select, delete
            
            # Знаходимо найстаріші записи
            stmt = (
                select(CachedResponse.id)
                .order_by(CachedResponse.last_hit.asc(), CachedResponse.created_at.asc())
                .limit(remove_count - expired)
            )
            
            old_ids = [row[0] for row in session.execute(stmt).all()]
            
            if old_ids:
                delete_stmt = delete(CachedResponse).where(CachedResponse.id.in_(old_ids))
                result = session.execute(delete_stmt)
                return expired + result.rowcount
        
        return expired
    
    def _get_cache_age(self, cached: CachedResponse) -> int:
        """
        Вік запису кешу у секундах
        
        Args:
            cached: Запис кешу
            
        Returns:
            int: Вік у секундах
        """
        age = datetime.utcnow() - cached.created_at
        return int(age.total_seconds())


