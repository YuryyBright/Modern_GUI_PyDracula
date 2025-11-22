# ==================== ui/control_panel.py ====================

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QComboBox, QLineEdit, QGroupBox, QTextEdit
)

from PySide6.QtCore import Signal
from core.utils.logger import get_logger


logger = get_logger(__name__)


class ControlPanel(QWidget):
    """
    Панель керування Web Assistant
    Кнопки та контроли для управління асистентом
    """
    
    # Сигнали для комунікації з головним вікном
    start_session_signal = Signal(str)  # mode
    stop_session_signal = Signal()
    navigate_signal = Signal(str)  # url
    extract_signal = Signal(str, str)  # selector, selector_type
    analyze_signal = Signal(str)  # prompt_type
    clear_cache_signal = Signal()
    
    def __init__(self, widgets, parent=None):
        """Ініціалізація панелі керування з посиланням на існуючі widgets"""
        super().__init__(parent)
        
        # Присвоюємо існуючі елементи з widgets до self
        try:
            # Сесія
            self.start_button = widgets.start_button
            self.stop_button = widgets.stop_button
            self.mode_combo = widgets.mode_combo
            
            # Навігація
            self.url_input = widgets.url_input
            self.navigate_button = widgets.navigate_button
            
            # Витягування
            self.selector_input = widgets.selector_input
            self.selector_type_combo = widgets.selector_type_combo
            self.extract_button = widgets.extract_button
            
            # Аналіз
            self.prompt_type_combo = widgets.prompt_type_combo
            self.analyze_button = widgets.analyze_button
            
            # Утиліти
            self.clear_cache_button = widgets.clear_cache_button
            self.refresh_button = widgets.refresh_button  # Якщо є, або замініть на ваш
            
            # Статус
            self.status_label = widgets.status_label
            
            logger.info("ControlPanel: UI elements linked successfully")
        except AttributeError as e:
            logger.error(f"Missing UI element: {e}")
            raise ValueError("One or more UI elements are missing in widgets. Check Qt Designer.")
        
        # Підключаємо події (clicked) до обробників
        self.connect_events()
    
    def connect_events(self):
        """Підключення обробників подій до кнопок"""
        self.start_button.clicked.connect(self.on_start_session)
        self.stop_button.clicked.connect(self.on_stop_session)
        self.navigate_button.clicked.connect(self.on_navigate)
        self.extract_button.clicked.connect(self.on_extract)
        self.analyze_button.clicked.connect(self.on_analyze)
        self.clear_cache_button.clicked.connect(self.on_clear_cache)
        
        # Якщо є refresh_button, підключіть його
        # self.refresh_button.clicked.connect(self.on_refresh)
        
        logger.info("ControlPanel events connected to existing buttons")
    
    # Методи обробників (залишаються без змін, але тепер використовують self.* елементи)
    def on_start_session(self):
        """Обробка запуску сесії"""
        mode_map = {
            "Ручний": "manual",
            "Напівавтоматичний": "semi_auto",
            "Автоматичний": "auto"
        }
        
        mode = mode_map[self.mode_combo.currentText()]
        self.start_session_signal.emit(mode)
        
        # UI updates
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.mode_combo.setEnabled(False)
        self.status_label.setText(f"Статус: Активна сесія ({self.mode_combo.currentText()})")
        
        logger.info(f"Session start requested: {mode}")
    
    def on_stop_session(self):
        """Обробка зупинки сесії"""
        self.stop_session_signal.emit()
        
        # UI updates
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.mode_combo.setEnabled(True)
        self.status_label.setText("Статус: Зупинено")
        
        logger.info("Session stop requested")
    
    def on_navigate(self):
        """Обробка навігації"""
        url = self.url_input.toPlainText().strip()
        if url:
            self.navigate_signal.emit(url)
            self.status_label.setText(f"Навігація: {url}")
            logger.info(f"Navigate requested: {url}")
    
    def on_extract(self):
        """Обробка витягування"""
        selector = self.selector_input.toPlainText().strip()
        selector_type = self.selector_type_combo.currentText().lower()
        
        if selector:
            self.extract_signal.emit(selector, selector_type)
            self.status_label.setText("Витягування тексту...")
            logger.info(f"Extract requested: {selector} ({selector_type})")
    
    def on_analyze(self):
        """Обробка аналізу"""
        prompt_type_map = {
            "Загальний аналіз": "analyze_text",
            "Резюме": "summarize",
            "Витягти інформацію": "extract_info"
        }
        
        prompt_type = prompt_type_map[self.prompt_type_combo.currentText()]
        self.analyze_signal.emit(prompt_type)
        self.status_label.setText("Аналіз LLM...")
        logger.info(f"Analysis requested: {prompt_type}")
    
    def on_clear_cache(self):
        """Обробка очищення кешу"""
        self.clear_cache_signal.emit()
        self.status_label.setText("Кеш очищено")
        logger.info("Cache clear requested")
    
    def set_status(self, message: str):
        """Встановлення статусу"""
        self.status_label.setText(f"Статус: {message}")