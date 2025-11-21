"""
Web Analyzer Service
Головний сервіс, який координує роботу Selenium, LLM та кешування
"""

from typing import Optional, Dict, Any, Callable
from datetime import datetime
import uuid

from core.selenium.browser import SeleniumBrowser
from core.llm.base import create_llm_client, BaseLLMClient
from core.database.repository import DatabaseRepository
from core.cache.cache_manager import CacheManager
from core.config.settings import get_settings
from utils.logger import get_logger
from utils.hasher import Hasher
from utils.validators import Validators
from utils.text_cleaner import TextCleaner
from utils.exceptions import (
    BrowserError, LLMError, ExtractionError, ValidationError
)


logger = get_logger(__name__)


class WebAnalyzerService:
    """
    Головний сервіс для аналізу веб-сторінок
    Координує роботу всіх компонентів
    """
    
    def __init__(self):
        """Ініціалізація сервісу"""
        self.settings = get_settings()
        
        # Ініціалізація компонентів
        self.browser: Optional[SeleniumBrowser] = None
        self.llm_client: Optional[BaseLLMClient] = None
        self.db_repository = DatabaseRepository()
        self.cache_manager = CacheManager(self.db_repository)
        
        # Поточна сесія
        self.session_id: Optional[str] = None
        self.current_mode: str = "manual"
        
        # Статистика сесії
        self.session_stats = {
            'pages_visited': 0,
            'extractions_count': 0,
            'llm_requests_count': 0,
            'cache_hits': 0
        }
        
        logger.info("WebAnalyzerService initialized")
    
    def start_session(self, mode: str = "manual") -> str:
        """
        Початок нової сесії
        
        Args:
            mode: Режим роботи (auto, semi_auto, manual)
            
        Returns:
            str: ID сесії
        """
        self.session_id = str(uuid.uuid4())
        self.current_mode = mode
        
        # Ініціалізація браузера
        if not self.browser:
            self.browser = SeleniumBrowser()
        
        # Ініціалізація LLM клієнта
        if not self.llm_client:
            self.llm_client = create_llm_client()
        
        # Збереження сесії в БД
        llm_provider = self.settings.llm.provider
        self.db_repository.create_session(
            session_id=self.session_id,
            mode=mode,
            llm_provider=llm_provider
        )
        
        logger.info(f"Session started: {self.session_id}, mode: {mode}")
        return self.session_id
    
    def end_session(self) -> None:
        """Завершення сесії"""
        if self.session_id:
            # Оновлення статистики
            self.db_repository.update_session_stats(
                session_id=self.session_id,
                **self.session_stats
            )
            
            # Завершення сесії
            self.db_repository.end_session(self.session_id)
            
            logger.info(f"Session ended: {self.session_id}")
            self.session_id = None
        
        # Закриття браузера
        if self.browser:
            self.browser.quit()
            self.browser = None
    
    def navigate_to_url(self, url: str) -> bool:
        """
        Навігація на URL
        
        Args:
            url: URL сторінки
            
        Returns:
            bool: True якщо успішно
        """
        # Валідація URL
        if not Validators.is_valid_url(url):
            logger.error(f"Invalid URL: {url}")
            raise ValidationError(f"Invalid URL: {url}")
        
        if not self.browser:
            raise BrowserError("Browser not initialized. Call start_session() first.")
        
        # Навігація
        success = self.browser.navigate_to(url)
        
        if success:
            self.session_stats['pages_visited'] += 1
            logger.info(f"Navigated to: {url}")
        
        return success
    
    def extract_text(
        self,
        selector: str,
        selector_type: str = "css",
        url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Витягування тексту з елемента
        
        Args:
            selector: CSS/XPath селектор
            selector_type: Тип селектора
            url: URL (якщо None - береться поточний)
            
        Returns:
            Dict з ключами: text, text_hash, url, selector, metadata
        """
        if not self.browser:
            raise BrowserError("Browser not initialized")
        
        # Валідація селектора
        if not Validators.is_valid_selector(selector, selector_type):
            raise ValidationError(f"Invalid selector: {selector}")
        
        # URL
        if url is None:
            url = self.browser.get_current_url()
        
        # Витягування тексту
        try:
            if selector_type == "css":
                from selenium.webdriver.common.by import By
                text = self.browser.get_element_text(selector, By.CSS_SELECTOR)
            elif selector_type == "xpath":
                from selenium.webdriver.common.by import By
                text = self.browser.get_element_text(selector, By.XPATH)
            else:
                raise ValidationError(f"Unknown selector type: {selector_type}")
            
            if not text:
                raise ExtractionError(f"No text found for selector: {selector}")
            
            # Очищення тексту
            text = TextCleaner.clean_for_llm(
                text,
                max_length=self.settings.security.max_text_length
            )
            
            # Хешування
            text_hash = Hasher.hash_text(
                text,
                algorithm=self.settings.cache.hash_algorithm
            )
            
            # Метадані
            metadata = {
                'page_title': self.browser.get_page_title(),
                'word_count': TextCleaner.word_count(text),
                'char_count': len(text),
                'extracted_at': datetime.utcnow().isoformat()
            }
            
            # Збереження в БД
            extraction = self.db_repository.add_extraction(
                url=url,
                selector=selector,
                extracted_text=text,
                text_hash=text_hash,
                selector_type=selector_type,
                extraction_mode=self.current_mode,
                page_title=metadata['page_title']
            )
            
            # Оновлення статистики
            self.session_stats['extractions_count'] += 1
            
            logger.info(
                f"Text extracted: {len(text)} chars, "
                f"hash: {text_hash[:8]}..., "
                f"extraction_id: {extraction.id}"
            )
            
            return {
                'text': text,
                'text_hash': text_hash,
                'url': url,
                'selector': selector,
                'extraction_id': extraction.id,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            raise ExtractionError(f"Failed to extract text: {e}")
    
    def analyze_with_llm(
        self,
        text: str,
        extraction_id: Optional[int] = None,
        url: Optional[str] = None,
        selector: Optional[str] = None,
        prompt_type: str = "analyze_text",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Аналіз тексту за допомогою LLM
        
        Args:
            text: Текст для аналізу
            extraction_id: ID витягування
            url: URL сторінки
            selector: Селектор
            prompt_type: Тип промпту (analyze_text, summarize, extract_info)
            use_cache: Використовувати кеш
            
        Returns:
            Dict з ключами: response, from_cache, processing_time, tokens_used
        """
        if not self.llm_client:
            raise LLMError("LLM client not initialized")
        
        # Генерація ключа кешу
        cache_key = self.cache_manager.generate_cache_key(
            text=text,
            provider=self.settings.llm.provider,
            prompt_type=prompt_type
        )
        
        # Перевірка кешу
        if use_cache and self.settings.cache.enabled:
            cached = self.cache_manager.get_cached_response(cache_key)
            if cached:
                self.session_stats['cache_hits'] += 1
                logger.info(f"Cache hit for key: {cache_key[:16]}...")
                
                return {
                    'response': cached.response,
                    'from_cache': True,
                    'cache_hits': cached.hits,
                    'processing_time': 0,
                    'tokens_used': 0
                }
        
        # Підготовка промпту
        try:
            if prompt_type == "analyze_text":
                response = self.llm_client.analyze_text(
                    text=text,
                    url=url or "unknown",
                    selector=selector or "unknown"
                )
            elif prompt_type == "summarize":
                response = self.llm_client.summarize_text(text)
            elif prompt_type == "extract_info":
                response = self.llm_client.extract_information(text)
            else:
                # Загальний запит
                result = self.llm_client.generate(prompt=text)
                response = result['response']
            
            # Отримання повної відповіді для статистики
            if isinstance(response, str):
                # Якщо метод повернув тільки текст, робимо повний запит
                full_result = self.llm_client.generate(
                    prompt=text,
                    system_prompt=self.settings.llm.prompts.system
                )
            else:
                full_result = response
                response = response['response']
            
            # Збереження в БД
            text_hash = Hasher.hash_text(text)
            response_hash = Hasher.hash_text(response)
            
            llm_request = self.db_repository.add_llm_request(
                provider=self.settings.llm.provider,
                model=full_result.get('model', 'unknown'),
                prompt=text,
                prompt_hash=text_hash,
                response=response,
                response_hash=response_hash,
                extraction_id=extraction_id,
                tokens_used=full_result.get('tokens_used'),
                processing_time=full_result.get('processing_time'),
                status='success'
            )
            
            # Збереження в кеш
            if use_cache and self.settings.cache.enabled:
                self.cache_manager.cache_response(
                    cache_key=cache_key,
                    input_text=text,
                    provider=self.settings.llm.provider,
                    model=full_result.get('model', 'unknown'),
                    prompt_template=prompt_type,
                    response=response
                )
            
            # Оновлення статистики
            self.session_stats['llm_requests_count'] += 1
            
            logger.info(f"LLM analysis completed: request_id={llm_request.id}")
            
            return {
                'response': response,
                'from_cache': False,
                'processing_time': full_result.get('processing_time', 0),
                'tokens_used': full_result.get('tokens_used', 0),
                'request_id': llm_request.id
            }
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            
            # Збереження помилки в БД
            self.db_repository.add_llm_request(
                provider=self.settings.llm.provider,
                model='unknown',
                prompt=text,
                prompt_hash=Hasher.hash_text(text),
                response='',
                response_hash='',
                extraction_id=extraction_id,
                status='error',
                error_message=str(e)
            )
            
            raise LLMError(f"LLM analysis failed: {e}")
    
    def extract_and_analyze(
        self,
        selector: str,
        selector_type: str = "css",
        prompt_type: str = "analyze_text",
        use_cache: bool = True,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Комбінована операція: витягування + аналіз
        
        Args:
            selector: Селектор
            selector_type: Тип селектора
            prompt_type: Тип промпту
            use_cache: Використовувати кеш
            progress_callback: Callback для прогресу
            
        Returns:
            Dict з результатами витягування та аналізу
        """
        # Крок 1: Витягування
        if progress_callback:
            progress_callback(0, "Extracting text...")
        
        extraction_result = self.extract_text(selector, selector_type)
        
        if progress_callback:
            progress_callback(50, "Analyzing with LLM...")
        
        # Крок 2: Аналіз
        analysis_result = self.analyze_with_llm(
            text=extraction_result['text'],
            extraction_id=extraction_result['extraction_id'],
            url=extraction_result['url'],
            selector=selector,
            prompt_type=prompt_type,
            use_cache=use_cache
        )
        
        if progress_callback:
            progress_callback(100, "Completed!")
        
        # Об'єднання результатів
        return {
            'extraction': extraction_result,
            'analysis': analysis_result,
            'session_id': self.session_id
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Отримання статистики
        
        Returns:
            Dict зі статистикою
        """
        db_stats = self.db_repository.get_statistics()
        
        return {
            'session': self.session_stats,
            'database': db_stats,
            'session_id': self.session_id,
            'mode': self.current_mode
        }
    
    def clear_cache(self) -> int:
        """
        Очищення кешу
        
        Returns:
            int: Кількість видалених записів
        """
        count = self.cache_manager.clear_cache()
        logger.info(f"Cache cleared: {count} entries removed")
        return count
    
    def __enter__(self):
        """Context manager entry"""
        self.start_session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.end_session()