# ==================== utils/hasher.py ====================

import hashlib
from typing import Union


class Hasher:
    """Клас для хешування текстів"""
    
    @staticmethod
    def md5(text: str) -> str:
        """
        MD5 хеш тексту
        
        Args:
            text: Текст для хешування
            
        Returns:
            str: MD5 хеш
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    @staticmethod
    def sha256(text: str) -> str:
        """
        SHA256 хеш тексту
        
        Args:
            text: Текст для хешування
            
        Returns:
            str: SHA256 хеш
        """
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    @staticmethod
    def hash_text(text: str, algorithm: str = "md5") -> str:
        """
        Хешування тексту з вибором алгоритму
        
        Args:
            text: Текст
            algorithm: Алгоритм (md5, sha256)
            
        Returns:
            str: Хеш
        """
        if algorithm == "md5":
            return Hasher.md5(text)
        elif algorithm == "sha256":
            return Hasher.sha256(text)
        else:
            raise ValueError(f"Unknown hash algorithm: {algorithm}")
    
    @staticmethod
    def create_cache_key(*args: Union[str, int, float]) -> str:
        """
        Створення ключа кешу з кількох значень
        
        Args:
            *args: Значення для об'єднання
            
        Returns:
            str: MD5 хеш об'єднаних значень
        """
        combined = "|".join(str(arg) for arg in args)
        return Hasher.md5(combined)