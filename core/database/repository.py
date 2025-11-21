"""
Database Repository
Репозиторій для роботи з базою даних (паттерн Repository)
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, select, update, delete, func, and_, or_
from sqlalchemy.orm import sessionmaker, Session as DBSession
from contextlib import contextmanager

from .models import (
    Base, ExtractionHistory, LLMRequest, CachedResponse, 
    Session as AppSession, Selector
)
from ..config.settings import get_settings


class DatabaseRepository:
    """Репозиторій для роботи з базою даних"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Ініціалізація репозиторію
        
        Args:
            database_url: URL бази даних (якщо None - береться з конфігу)
        """
        settings = get_settings()
        
        if database_url is None:
            db_path = settings.database.path
            database_url = f"sqlite:///{db_path}"
        
        self.engine = create_engine(
            database_url,
            echo=settings.database.echo,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Створення таблиць
        Base.metadata.create_all(bind=self.engine)
    
    @contextmanager
    def get_session(self):
        """Context manager для сесії БД"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    # ==================== ExtractionHistory ====================
    
    def add_extraction(
        self,
        url: str,
        selector: str,
        extracted_text: str,
        text_hash: str,
        selector_type: str = "css",
        extraction_mode: str = "manual",
        page_title: Optional[str] = None,
        page_language: Optional[str] = None
    ) -> ExtractionHistory:
        """
        Додавання запису про витягування
        
        Args:
            url: URL сторінки
            selector: CSS/XPath селектор
            extracted_text: Витягнутий текст
            text_hash: Hash тексту
            selector_type: Тип селектора
            extraction_mode: Режим витягування
            page_title: Заголовок сторінки
            page_language: Мова сторінки
            
        Returns:
            ExtractionHistory: Створений запис
        """
        with self.get_session() as session:
            extraction = ExtractionHistory(
                url=url,
                selector=selector,
                selector_type=selector_type,
                extracted_text=extracted_text,
                text_hash=text_hash,
                text_length=len(extracted_text),
                extraction_mode=extraction_mode,
                page_title=page_title,
                page_language=page_language
            )
            session.add(extraction)
            session.flush()
            session.refresh(extraction)
            return extraction
    
    def get_extraction_by_id(self, extraction_id: int) -> Optional[ExtractionHistory]:
        """Отримання витягування за ID"""
        with self.get_session() as session:
            return session.get(ExtractionHistory, extraction_id)
    
    def get_extractions_by_url(
        self,
        url: str,
        limit: int = 10
    ) -> List[ExtractionHistory]:
        """Отримання витягувань за URL"""
        with self.get_session() as session:
            stmt = (
                select(ExtractionHistory)
                .where(ExtractionHistory.url == url)
                .order_by(ExtractionHistory.created_at.desc())
                .limit(limit)
            )
            return list(session.execute(stmt).scalars().all())
    
    def get_extractions_by_hash(self, text_hash: str) -> List[ExtractionHistory]:
        """Отримання витягувань за hash"""
        with self.get_session() as session:
            stmt = (
                select(ExtractionHistory)
                .where(ExtractionHistory.text_hash == text_hash)
                .order_by(ExtractionHistory.created_at.desc())
            )
            return list(session.execute(stmt).scalars().all())
    
    def get_recent_extractions(
        self,
        limit: int = 50,
        mode: Optional[str] = None
    ) -> List[ExtractionHistory]:
        """Отримання останніх витягувань"""
        with self.get_session() as session:
            stmt = select(ExtractionHistory)
            
            if mode:
                stmt = stmt.where(ExtractionHistory.extraction_mode == mode)
            
            stmt = stmt.order_by(ExtractionHistory.created_at.desc()).limit(limit)
            return list(session.execute(stmt).scalars().all())
    
    # ==================== LLMRequest ====================
    
    def add_llm_request(
        self,
        provider: str,
        model: str,
        prompt: str,
        prompt_hash: str,
        response: str,
        response_hash: str,
        extraction_id: Optional[int] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        tokens_used: Optional[int] = None,
        processing_time: Optional[float] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> LLMRequest:
        """Додавання запиту до LLM"""
        with self.get_session() as session:
            request = LLMRequest(
                extraction_id=extraction_id,
                provider=provider,
                model=model,
                prompt=prompt,
                prompt_hash=prompt_hash,
                response=response,
                response_hash=response_hash,
                temperature=temperature,
                max_tokens=max_tokens,
                tokens_used=tokens_used,
                processing_time=processing_time,
                status=status,
                error_message=error_message
            )
            session.add(request)
            session.flush()
            session.refresh(request)
            return request
    
    def get_llm_request_by_id(self, request_id: int) -> Optional[LLMRequest]:
        """Отримання запиту за ID"""
        with self.get_session() as session:
            return session.get(LLMRequest, request_id)
    
    def get_llm_requests_by_extraction(
        self,
        extraction_id: int
    ) -> List[LLMRequest]:
        """Отримання запитів за extraction_id"""
        with self.get_session() as session:
            stmt = (
                select(LLMRequest)
                .where(LLMRequest.extraction_id == extraction_id)
                .order_by(LLMRequest.created_at.desc())
            )
            return list(session.execute(stmt).scalars().all())
    
    # ==================== CachedResponse ====================
    
    def add_cached_response(
        self,
        cache_key: str,
        input_text: str,
        input_hash: str,
        provider: str,
        model: str,
        prompt_template: str,
        response: str,
        ttl_seconds: Optional[int] = None
    ) -> CachedResponse:
        """Додавання кешованої відповіді"""
        with self.get_session() as session:
            expires_at = None
            if ttl_seconds:
                expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            
            cached = CachedResponse(
                cache_key=cache_key,
                input_text=input_text,
                input_hash=input_hash,
                provider=provider,
                model=model,
                prompt_template=prompt_template,
                response=response,
                expires_at=expires_at
            )
            session.add(cached)
            session.flush()
            session.refresh(cached)
            return cached
    
    def get_cached_response(self, cache_key: str) -> Optional[CachedResponse]:
        """
        Отримання кешованої відповіді
        
        Returns:
            CachedResponse або None якщо не знайдено/прострочено
        """
        with self.get_session() as session:
            stmt = (
                select(CachedResponse)
                .where(
                    and_(
                        CachedResponse.cache_key == cache_key,
                        CachedResponse.is_valid == True,
                        or_(
                            CachedResponse.expires_at.is_(None),
                            CachedResponse.expires_at > datetime.utcnow()
                        )
                    )
                )
            )
            cached = session.execute(stmt).scalar_one_or_none()
            
            if cached:
                # Оновлюємо статистику
                cached.hits += 1
                cached.last_hit = datetime.utcnow()
                session.add(cached)
            
            return cached
    
    def invalidate_cache(self, cache_key: Optional[str] = None) -> int:
        """
        Інвалідація кешу
        
        Args:
            cache_key: Конкретний ключ або None для всього кешу
            
        Returns:
            int: Кількість інвалідованих записів
        """
        with self.get_session() as session:
            if cache_key:
                stmt = (
                    update(CachedResponse)
                    .where(CachedResponse.cache_key == cache_key)
                    .values(is_valid=False)
                )
            else:
                stmt = update(CachedResponse).values(is_valid=False)
            
            result = session.execute(stmt)
            return result.rowcount
    
    def clean_expired_cache(self) -> int:
        """Видалення прострочених записів кешу"""
        with self.get_session() as session:
            stmt = (
                delete(CachedResponse)
                .where(
                    and_(
                        CachedResponse.expires_at.isnot(None),
                        CachedResponse.expires_at < datetime.utcnow()
                    )
                )
            )
            result = session.execute(stmt)
            return result.rowcount
    
    # ==================== Session ====================
    
    def create_session(
        self,
        session_id: str,
        mode: str,
        llm_provider: str
    ) -> AppSession:
        """Створення нової сесії"""
        with self.get_session() as session:
            app_session = AppSession(
                session_id=session_id,
                mode=mode,
                llm_provider=llm_provider
            )
            session.add(app_session)
            session.flush()
            session.refresh(app_session)
            return app_session
    
    def update_session_stats(
        self,
        session_id: str,
        **kwargs
    ) -> Optional[AppSession]:
        """Оновлення статистики сесії"""
        with self.get_session() as session:
            stmt = (
                select(AppSession)
                .where(AppSession.session_id == session_id)
            )
            app_session = session.execute(stmt).scalar_one_or_none()
            
            if app_session:
                for key, value in kwargs.items():
                    if hasattr(app_session, key):
                        setattr(app_session, key, value)
                session.add(app_session)
            
            return app_session
    
    def end_session(self, session_id: str) -> Optional[AppSession]:
        """Завершення сесії"""
        with self.get_session() as session:
            stmt = (
                select(AppSession)
                .where(AppSession.session_id == session_id)
            )
            app_session = session.execute(stmt).scalar_one_or_none()
            
            if app_session and not app_session.ended_at:
                app_session.ended_at = datetime.utcnow()
                app_session.duration_seconds = int(
                    (app_session.ended_at - app_session.started_at).total_seconds()
                )
                session.add(app_session)
            
            return app_session
    
    # ==================== Selector ====================
    
    def add_selector(
        self,
        selector: str,
        selector_type: str = "css",
        name: Optional[str] = None,
        description: Optional[str] = None,
        domain_pattern: Optional[str] = None,
        category: Optional[str] = None
    ) -> Selector:
        """Додавання селектора"""
        with self.get_session() as session:
            sel = Selector(
                selector=selector,
                selector_type=selector_type,
                name=name,
                description=description,
                domain_pattern=domain_pattern,
                category=category
            )
            session.add(sel)
            session.flush()
            session.refresh(sel)
            return sel
    
    def get_selectors_by_domain(
        self,
        domain: str,
        category: Optional[str] = None
    ) -> List[Selector]:
        """Отримання селекторів для домену"""
        with self.get_session() as session:
            stmt = select(Selector).where(
                and_(
                    Selector.is_active == True,
                    or_(
                        Selector.domain_pattern.is_(None),
                        Selector.domain_pattern == domain
                    )
                )
            )
            
            if category:
                stmt = stmt.where(Selector.category == category)
            
            stmt = stmt.order_by(Selector.usage_count.desc())
            return list(session.execute(stmt).scalars().all())
    
    # ==================== Statistics ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Отримання загальної статистики"""
        with self.get_session() as session:
            stats = {
                'total_extractions': session.query(func.count(ExtractionHistory.id)).scalar(),
                'total_llm_requests': session.query(func.count(LLMRequest.id)).scalar(),
                'total_cached': session.query(func.count(CachedResponse.id)).scalar(),
                'total_sessions': session.query(func.count(AppSession.id)).scalar(),
                'cache_hit_rate': 0.0
            }
            
            # Розрахунок cache hit rate
            total_cached = session.query(func.sum(CachedResponse.hits)).scalar() or 0
            if stats['total_llm_requests'] > 0:
                stats['cache_hit_rate'] = (total_cached / stats['total_llm_requests']) * 100
            
            return stats
    
    # ==================== Cleanup ====================
    
    def clear_all_data(self) -> Dict[str, int]:
        """Очищення всіх даних"""
        with self.get_session() as session:
            counts = {}
            
            counts['extractions'] = session.query(func.count(ExtractionHistory.id)).scalar()
            counts['llm_requests'] = session.query(func.count(LLMRequest.id)).scalar()
            counts['cached'] = session.query(func.count(CachedResponse.id)).scalar()
            counts['sessions'] = session.query(func.count(AppSession.id)).scalar()
            
            # Видалення
            session.query(ExtractionHistory).delete()
            session.query(LLMRequest).delete()
            session.query(CachedResponse).delete()
            session.query(AppSession).delete()
            
            return counts