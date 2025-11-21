"""
Utilities Module
Включає logger, hasher, validators, exceptions
"""

# ==================== utils/logger.py ====================

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler
from colorlog import ColoredFormatter


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: str = "INFO",
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    colored: bool = True
) -> logging.Logger:
    """
    Налаштування логера з підтримкою файлів та кольорового виводу
    
    Args:
        name: Ім'я логера
        log_file: Шлях до файлу логів
        level: Рівень логування
        max_bytes: Максимальний розмір файлу
        backup_count: Кількість бекапів
        colored: Використовувати кольоровий вивід
        
    Returns:
        logging.Logger: Налаштований логер
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Уникнення дублікатів handlers
    if logger.handlers:
        return logger
    
    # Формат логів
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    if colored:
        colored_formatter = ColoredFormatter(
            "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt=date_format,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler.setFormatter(colored_formatter)
    else:
        console_formatter = logging.Formatter(log_format, datefmt=date_format)
        console_handler.setFormatter(console_formatter)
    
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Створення директорії для логів
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(log_format, datefmt=date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Отримання логера для модуля
    
    Args:
        name: Ім'я модуля (__name__)
        
    Returns:
        logging.Logger: Логер
    """
    return setup_logger(name, log_file=f"logs/{name}.log")