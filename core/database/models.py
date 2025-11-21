"""
Database Models
SQLAlchemy моделі для збереження історії та кешу
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Integer, Text, DateTime, Boolean, Float,
    Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовий клас для всіх моделей"""
    pass


class ExtractionHistory(Base):
    """
    Історія витягування даних з веб-сторінок
    """
    __tablename__ = "extraction_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # URL та селектор
    url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    selector: Mapped[str] = mapped_column(String(512), nullable=False)
    selector_type: Mapped[str] = mapped_column(String(50), default="css")  # css, xpath
    
    # Витягнутий текст
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    text_length: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Метадані сторінки
    page_title: Mapped[Optional[str]] = mapped_column(String(512))
    page_language: Mapped[Optional[str]] = mapped_column(String(10))
    
    # Режим витягування
    extraction_mode: Mapped[str] = mapped_column(String(50), default="manual")  # auto, semi_auto, manual
    
    # Часові мітки
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Індекси для швидкого пошуку
    __table_args__ = (
        Index('idx_url_selector', 'url', 'selector'),
        Index('idx_text_hash_created', 'text_hash', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<ExtractionHistory(id={self.id}, url={self.url[:50]}..., mode={self.extraction_mode})>"


class LLMRequest(Base):
    """
    Історія запитів до LLM
    """
    __tablename__ = "llm_requests"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Зв'язок з витягнутим текстом
    extraction_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    
    # Параметри запиту
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # lm_studio, ollama
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Промпт та відповідь
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    response_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    
    # Параметри генерації
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2000)
    
    # Статистика
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    processing_time: Mapped[Optional[float]] = mapped_column(Float)  # секунди
    
    # Статус
    status: Mapped[str] = mapped_column(String(50), default="success")  # success, error, timeout
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Часові мітки
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Індекси
    __table_args__ = (
        Index('idx_prompt_hash_provider', 'prompt_hash', 'provider'),
        Index('idx_extraction_created', 'extraction_id', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<LLMRequest(id={self.id}, provider={self.provider}, model={self.model}, status={self.status})>"


class CachedResponse(Base):
    """
    Кешовані відповіді LLM для дедуплікації
    """
    __tablename__ = "cached_responses"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Ключ кешу (hash тексту + параметрів)
    cache_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    
    # Вхідні дані
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    
    # Параметри запиту
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_template: Mapped[str] = mapped_column(String(100), nullable=False)  # analyze, summarize, extract
    
    # Кешована відповідь
    response: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Статистика використання
    hits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_hit: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Часові мітки
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    
    # Флаг валідності
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    __table_args__ = (
        Index('idx_input_hash_provider', 'input_hash', 'provider', 'prompt_template'),
    )
    
    def __repr__(self) -> str:
        return f"<CachedResponse(id={self.id}, cache_key={self.cache_key}, hits={self.hits})>"


class Session(Base):
    """
    Сесії роботи з асистентом
    """
    __tablename__ = "sessions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Ідентифікатор сесії
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    
    # Параметри сесії
    mode: Mapped[str] = mapped_column(String(50), nullable=False)  # auto, semi_auto, manual
    llm_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Статистика
    pages_visited: Mapped[int] = mapped_column(Integer, default=0)
    extractions_count: Mapped[int] = mapped_column(Integer, default=0)
    llm_requests_count: Mapped[int] = mapped_column(Integer, default=0)
    cache_hits: Mapped[int] = mapped_column(Integer, default=0)
    
    # Часові мітки
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Тривалість
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, session_id={self.session_id}, mode={self.mode})>"


class Selector(Base):
    """
    Збережені селектори для швидкого доступу
    """
    __tablename__ = "selectors"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Селектор
    selector: Mapped[str] = mapped_column(String(512), nullable=False)
    selector_type: Mapped[str] = mapped_column(String(50), default="css")  # css, xpath
    
    # Опис
    name: Mapped[Optional[str]] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Домен для якого призначений
    domain_pattern: Mapped[Optional[str]] = mapped_column(String(512), index=True)
    
    # Категорія
    category: Mapped[Optional[str]] = mapped_column(String(100), index=True)  # article, news, blog, etc.
    
    # Статистика використання
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Часові мітки
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Флаг активності
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    __table_args__ = (
        Index('idx_domain_category', 'domain_pattern', 'category'),
        UniqueConstraint('selector', 'domain_pattern', name='uq_selector_domain'),
    )
    
    def __repr__(self) -> str:
        return f"<Selector(id={self.id}, name={self.name}, selector={self.selector[:50]}...)>"