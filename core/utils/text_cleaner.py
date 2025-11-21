# ==================== utils/text_cleaner.py ====================

import re
from typing import List, Optional
from bs4 import BeautifulSoup


class TextCleaner:
    """Утиліти для очищення та обробки тексту"""
    
    @staticmethod
    def remove_html_tags(text: str) -> str:
        """
        Видалення HTML тегів
        
        Args:
            text: Текст з HTML
            
        Returns:
            str: Чистий текст
        """
        soup = BeautifulSoup(text, 'html.parser')
        return soup.get_text(separator=' ', strip=True)
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """
        Нормалізація пробілів
        
        Args:
            text: Текст
            
        Returns:
            str: Текст з нормалізованими пробілами
        """
        # Заміна множинних пробілів на один
        text = re.sub(r'\s+', ' ', text)
        # Видалення пробілів на початку/кінці рядків
        text = '\n'.join(line.strip() for line in text.split('\n'))
        # Видалення множинних порожніх рядків
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()
    
    @staticmethod
    def remove_special_characters(text: str, keep: Optional[List[str]] = None) -> str:
        """
        Видалення спеціальних символів
        
        Args:
            text: Текст
            keep: Список символів для збереження
            
        Returns:
            str: Очищений текст
        """
        if keep is None:
            keep = [' ', '.', ',', '!', '?', '-', '\n']
        
        # Створення regex pattern
        keep_pattern = ''.join(re.escape(char) for char in keep)
        pattern = f'[^a-zA-Zа-яА-ЯіІїЇєЄґҐ0-9{keep_pattern}]'
        
        return re.sub(pattern, '', text)
    
    @staticmethod
    def truncate(text: str, max_length: int, suffix: str = "...") -> str:
        """
        Обрізання тексту до максимальної довжини
        
        Args:
            text: Текст
            max_length: Максимальна довжина
            suffix: Суфікс для обрізаного тексту
            
        Returns:
            str: Обрізаний текст
        """
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def extract_sentences(text: str, max_sentences: Optional[int] = None) -> List[str]:
        """
        Витягування речень з тексту
        
        Args:
            text: Текст
            max_sentences: Максимальна кількість речень
            
        Returns:
            List[str]: Список речень
        """
        # Простий розділ по крапках
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if max_sentences:
            sentences = sentences[:max_sentences]
        
        return sentences
    
    @staticmethod
    def word_count(text: str) -> int:
        """
        Підрахунок слів у тексті
        
        Args:
            text: Текст
            
        Returns:
            int: Кількість слів
        """
        words = re.findall(r'\b\w+\b', text)
        return len(words)
    
    @staticmethod
    def clean_for_llm(text: str, max_length: int = 50000) -> str:
        """
        Комплексне очищення тексту для LLM
        
        Args:
            text: Вихідний текст
            max_length: Максимальна довжина
            
        Returns:
            str: Очищений текст
        """
        # 1. Видалення HTML
        text = TextCleaner.remove_html_tags(text)
        
        # 2. Нормалізація пробілів
        text = TextCleaner.normalize_whitespace(text)
        
        # 3. Обрізання якщо потрібно
        if len(text) > max_length:
            text = TextCleaner.truncate(text, max_length)
        
        return text