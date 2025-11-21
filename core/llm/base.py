"""
LLM Base Client and LM Studio Implementation
Базовий клас для LLM та реалізація для LM Studio
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from ..config.settings import get_settings
from ..utils.logger import get_logger



logger = get_logger(__name__)


# ==================== BASE CLIENT ====================

class BaseLLMClient(ABC):
    """Абстрактний базовий клас для LLM клієнтів"""
    
    def __init__(self):
        """Ініціалізація клієнта"""
        self.settings = get_settings()
        self.timeout = 60
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Генерація відповіді
        
        Args:
            prompt: Промпт користувача
            system_prompt: Системний промпт
            temperature: Температура генерації
            max_tokens: Максимальна кількість токенів
            **kwargs: Додаткові параметри
            
        Returns:
            Dict з ключами: response, tokens_used, processing_time, model
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Перевірка доступності LLM сервера
        
        Returns:
            bool: True якщо доступний
        """
        pass
    
    def format_prompt(
        self,
        template: str,
        **kwargs
    ) -> str:
        """
        Форматування промпту з шаблону
        
        Args:
            template: Шаблон промпту
            **kwargs: Змінні для підстановки
            
        Returns:
            str: Відформатований промпт
        """
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing template variable: {e}")
            return template


