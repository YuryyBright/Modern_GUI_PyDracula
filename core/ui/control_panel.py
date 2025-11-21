# ==================== ui/control_panel.py ====================

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QComboBox, QLineEdit, QGroupBox, QTextEdit
)
from PySide6.QtCore import pyqtSignal, Qt

from utils.logger import get_logger


logger = get_logger(__name__)


class ControlPanel(QWidget):
    """
    Панель керування Web Assistant
    Кнопки та контроли для управління асистентом
    """
    
    # Сигнали для комунікації з головним вікном
    start_session_signal = pyqtSignal(str)  # mode
    stop_session_signal = pyqtSignal()
    navigate_signal = pyqtSignal(str)  # url
    extract_signal = pyqtSignal(str, str)  # selector, selector_type
    analyze_signal = pyqtSignal(str)  # prompt_type
    clear_cache_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        """Ініціалізація панелі керування"""
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Налаштування UI"""
        layout = QVBoxLayout(self)
        
        # ==================== Session Control ====================
        session_group = QGroupBox("Сесія")
        session_layout = QVBoxLayout()
        
        # Mode selector
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Режим:"))
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Ручний", "Напівавтоматичний", "Автоматичний"])
        mode_layout.addWidget(self.mode_combo)
        session_layout.addLayout(mode_layout)
        
        # Session buttons
        session_buttons = QHBoxLayout()
        
        self.start_button = QPushButton("🚀 Запустити")
        self.start_button.clicked.connect(self.on_start_session)
        session_buttons.addWidget(self.start_button)
        
        self.stop_button = QPushButton("⏹️ Зупинити")
        self.stop_button.clicked.connect(self.on_stop_session)
        self.stop_button.setEnabled(False)
        session_buttons.addWidget(self.stop_button)
        
        session_layout.addLayout(session_buttons)
        session_group.setLayout(session_layout)
        layout.addWidget(session_group)
        
        # ==================== Navigation ====================
        nav_group = QGroupBox("Навігація")
        nav_layout = QVBoxLayout()
        
        # URL input
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL:"))
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        url_layout.addWidget(self.url_input)
        
        self.navigate_button = QPushButton("➡️ Перейти")
        self.navigate_button.clicked.connect(self.on_navigate)
        url_layout.addWidget(self.navigate_button)
        
        nav_layout.addLayout(url_layout)
        nav_group.setLayout(nav_layout)
        layout.addWidget(nav_group)
        
        # ==================== Extraction ====================
        extract_group = QGroupBox("Витягування")
        extract_layout = QVBoxLayout()
        
        # Selector input
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Селектор:"))
        
        self.selector_input = QLineEdit()
        self.selector_input.setPlaceholderText("article, .content, //div[@class='main']")
        selector_layout.addWidget(self.selector_input)
        
        # Selector type
        self.selector_type_combo = QComboBox()
        self.selector_type_combo.addItems(["CSS", "XPath"])
        selector_layout.addWidget(self.selector_type_combo)
        
        extract_layout.addLayout(selector_layout)
        
        # Extract button
        self.extract_button = QPushButton("📄 Витягти текст")
        self.extract_button.clicked.connect(self.on_extract)
        extract_layout.addWidget(self.extract_button)
        
        extract_group.setLayout(extract_layout)
        layout.addWidget(extract_group)
        
        # ==================== Analysis ====================
        analysis_group = QGroupBox("Аналіз")
        analysis_layout = QVBoxLayout()
        
        # Prompt type
        prompt_layout = QHBoxLayout()
        prompt_layout.addWidget(QLabel("Тип аналізу:"))
        
        self.prompt_type_combo = QComboBox()
        self.prompt_type_combo.addItems([
            "Загальний аналіз",
            "Резюме",
            "Витягти інформацію"
        ])
        prompt_layout.addWidget(self.prompt_type_combo)
        analysis_layout.addLayout(prompt_layout)
        
        # Analyze button
        self.analyze_button = QPushButton("🧠 Аналізувати")
        self.analyze_button.clicked.connect(self.on_analyze)
        analysis_layout.addWidget(self.analyze_button)
        
        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)
        
        # ==================== Utilities ====================
        utils_group = QGroupBox("Утиліти")
        utils_layout = QHBoxLayout()
        
        self.clear_cache_button = QPushButton("🗑️ Очистити кеш")
        self.clear_cache_button.clicked.connect(self.on_clear_cache)
        utils_layout.addWidget(self.clear_cache_button)
        
        self.refresh_button = QPushButton("🔄 Оновити сторінку")
        utils_layout.addWidget(self.refresh_button)
        
        utils_group.setLayout(utils_layout)
        layout.addWidget(utils_group)
        
        # ==================== Status ====================
        self.status_label = QLabel("Статус: Готовий")
        self.status_label.setStyleSheet("padding: 5px; background-color: #2d2d2d; border-radius: 3px;")
        layout.addWidget(self.status_label)
        
        # Stretch at the end
        layout.addStretch()
    
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
        url = self.url_input.text().strip()
        if url:
            self.navigate_signal.emit(url)
            self.status_label.setText(f"Навігація: {url}")
            logger.info(f"Navigate requested: {url}")
    
    def on_extract(self):
        """Обробка витягування"""
        selector = self.selector_input.text().strip()
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