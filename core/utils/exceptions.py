# ==================== utils/exceptions.py ====================

class WebAssistantException(Exception):
    """Базовий виняток для Web Assistant"""
    pass


class ConfigError(WebAssistantException):
    """Помилка конфігурації"""
    pass


class DatabaseError(WebAssistantException):
    """Помилка бази даних"""
    pass


class BrowserError(WebAssistantException):
    """Помилка браузера/Selenium"""
    pass


class ElementNotFoundError(BrowserError):
    """Елемент не знайдено на сторінці"""
    pass


class LLMError(WebAssistantException):
    """Помилка LLM"""
    pass


class LLMTimeoutError(LLMError):
    """Таймаут LLM запиту"""
    pass


class LLMUnavailableError(LLMError):
    """LLM сервер недоступний"""
    pass


class CacheError(WebAssistantException):
    """Помилка кешування"""
    pass


class ValidationError(WebAssistantException):
    """Помилка валідації даних"""
    pass


class ExtractionError(WebAssistantException):
    """Помилка витягування тексту"""
    pass
