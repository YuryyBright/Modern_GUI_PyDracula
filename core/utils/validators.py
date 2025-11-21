# ==================== utils/validators.py ====================

import re
from urllib.parse import urlparse
from typing import Optional


class Validators:
    """Валідатори для різних типів даних"""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Перевірка валідності URL
        
        Args:
            url: URL для перевірки
            
        Returns:
            bool: True якщо валідний
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def is_valid_selector(selector: str, selector_type: str = "css") -> bool:
        """
        Базова перевірка селектора
        
        Args:
            selector: Селектор
            selector_type: Тип (css, xpath)
            
        Returns:
            bool: True якщо виглядає валідним
        """
        if not selector or not selector.strip():
            return False
        
        if selector_type == "css":
            # Базова перевірка CSS селектора
            return len(selector) > 0 and not selector.startswith("//")
        
        elif selector_type == "xpath":
            # XPath повинен починатися з / або //
            return selector.startswith("/") or selector.startswith("//")
        
        return False
    
    @staticmethod
    def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
        """
        Очищення тексту від зайвих символів
        
        Args:
            text: Текст
            max_length: Максимальна довжина
            
        Returns:
            str: Очищений текст
        """
        # Видалення зайвих пробілів
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Обмеження довжини
        if max_length and len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text
    
    @staticmethod
    def extract_domain(url: str) -> Optional[str]:
        """
        Витягування домену з URL
        
        Args:
            url: URL
            
        Returns:
            str: Домен або None
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return None
    
    @staticmethod
    def is_valid_css_selector(selector: str) -> bool:
        """
        Детальна перевірка CSS селектора
        
        Args:
            selector: CSS селектор
            
        Returns:
            bool: True якщо валідний
        """
        # Прості правила для базової валідації
        invalid_patterns = [
            r'^\s*$',  # Порожній
            r'[<>]',   # HTML теги
            r'^\d',    # Починається з цифри (невалідно для class/id)
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, selector):
                return False
        
        return True