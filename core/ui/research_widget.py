"""
Research Widget - Інструмент для дослідження HTML-селекторів
Дозволяє тестувати CSS/XPath селектори перед використанням
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QPushButton, QComboBox,
    QGroupBox, QSplitter, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from core.utils.logger import get_logger

logger = get_logger(__name__)


class ResearchWidget(QWidget):
    """
    Віджет для дослідження селекторів
    Дозволяє вводити селектори та бачити результати в реальному часі
    """
    
    # Сигнали
    test_selector_signal = Signal(str, str)  # selector, selector_type
    use_selector_signal = Signal(str, str)   # selector, selector_type - застосувати в аналізаторі
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()
        
        logger.info("ResearchWidget initialized")
    
    def setup_ui(self):
        """Налаштування UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # === ЗАГОЛОВОК ===
        title = QLabel("🔬 Дослідження селекторів")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # === ПАНЕЛЬ ВВЕДЕННЯ ===
        input_group = QGroupBox("Введення селектора")
        input_layout = QVBoxLayout(input_group)
        
        # Рядок 1: Тип селектора
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Тип:"))
        
        self.selector_type_combo = QComboBox()
        self.selector_type_combo.addItems(["CSS Selector", "XPath"])
        self.selector_type_combo.setCurrentIndex(0)
        type_layout.addWidget(self.selector_type_combo)
        type_layout.addStretch()
        
        input_layout.addLayout(type_layout)
        
        # Рядок 2: Селектор
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Селектор:"))
        
        self.selector_input = QLineEdit()
        self.selector_input.setPlaceholderText("Наприклад: div.content, //div[@class='content']")
        selector_layout.addWidget(self.selector_input)
        
        input_layout.addLayout(selector_layout)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.test_btn = QPushButton("🧪 Тестувати")
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        buttons_layout.addWidget(self.test_btn)
        
        self.use_btn = QPushButton("✅ Використати в аналізаторі")
        self.use_btn.setEnabled(False)
        self.use_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 20px;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        buttons_layout.addWidget(self.use_btn)
        
        self.clear_btn = QPushButton("🗑️ Очистити")
        buttons_layout.addWidget(self.clear_btn)
        
        buttons_layout.addStretch()
        input_layout.addLayout(buttons_layout)
        
        main_layout.addWidget(input_group)
        
        # === SPLITTER для результатів ===
        splitter = QSplitter(Qt.Horizontal)
        
        # === СПИСОК ЗНАЙДЕНИХ ЕЛЕМЕНТІВ ===
        elements_group = QGroupBox("Знайдені елементи")
        elements_layout = QVBoxLayout(elements_group)
        
        self.elements_count_label = QLabel("Елементів: 0")
        self.elements_count_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        elements_layout.addWidget(self.elements_count_label)
        
        self.elements_list = QListWidget()
        self.elements_list.setAlternatingRowColors(True)
        elements_layout.addWidget(self.elements_list)
        
        splitter.addWidget(elements_group)
        
        # === ПОПЕРЕДНІЙ ПЕРЕГЛЯД ТЕКСТУ ===
        preview_group = QGroupBox("Попередній перегляд тексту")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("Тут буде відображено текст вибраного елемента...")
        preview_layout.addWidget(self.preview_text)
        
        splitter.addWidget(preview_group)
        
        splitter.setSizes([300, 500])
        main_layout.addWidget(splitter)
        
        # === СТАТУС ===
        self.status_label = QLabel("Готовий до тестування")
        self.status_label.setStyleSheet("""
            background-color: #e3f2fd;
            padding: 10px;
            border-radius: 4px;
            font-size: 13px;
        """)
        main_layout.addWidget(self.status_label)
        
        # === ПОРАДИ ===
        tips_group = QGroupBox("💡 Корисні поради")
        tips_layout = QVBoxLayout(tips_group)
        
        tips_text = QLabel(
            "<b>CSS Селектори:</b><br>"
            "• <code>div.class-name</code> - елемент з класом<br>"
            "• <code>#element-id</code> - елемент з ID<br>"
            "• <code>article > p</code> - прямі нащадки<br>"
            "• <code>div[data-attr='value']</code> - з атрибутом<br><br>"
            
            "<b>XPath:</b><br>"
            "• <code>//div[@class='content']</code> - елемент з класом<br>"
            "• <code>//article/p[1]</code> - перший параграф в article<br>"
            "• <code>//div[contains(text(), 'текст')]</code> - містить текст"
        )
        tips_text.setWordWrap(True)
        tips_text.setTextFormat(Qt.RichText)
        tips_layout.addWidget(tips_text)
        
        main_layout.addWidget(tips_group)
    
    def connect_signals(self):
        """Підключення сигналів"""
        self.test_btn.clicked.connect(self.on_test_clicked)
        self.use_btn.clicked.connect(self.on_use_clicked)
        self.clear_btn.clicked.connect(self.on_clear_clicked)
        self.elements_list.currentItemChanged.connect(self.on_element_selected)
        
        # Enter в полі селектора
        self.selector_input.returnPressed.connect(self.on_test_clicked)
    
    def on_test_clicked(self):
        """Обробник кнопки "Тестувати" """
        selector = self.selector_input.text().strip()
        
        if not selector:
            self.set_status("❌ Введіть селектор", "error")
            return
        
        selector_type = "css" if self.selector_type_combo.currentText() == "CSS Selector" else "xpath"
        
        self.set_status(f"🔍 Тестування селектора: {selector}", "info")
        self.use_btn.setEnabled(False)
        
        # Відправка сигналу
        self.test_selector_signal.emit(selector, selector_type)
    
    def on_use_clicked(self):
        """Обробник кнопки "Використати в аналізаторі" """
        selector = self.selector_input.text().strip()
        selector_type = "css" if self.selector_type_combo.currentText() == "CSS Selector" else "xpath"
        
        logger.info(f"Using selector in analyzer: {selector}")
        self.use_selector_signal.emit(selector, selector_type)
        
        self.set_status(f"✅ Селектор застосовано в аналізаторі", "success")
    
    def on_clear_clicked(self):
        """Очищення всіх полів"""
        self.selector_input.clear()
        self.elements_list.clear()
        self.preview_text.clear()
        self.elements_count_label.setText("Елементів: 0")
        self.use_btn.setEnabled(False)
        self.set_status("Готовий до тестування", "info")
    
    def on_element_selected(self, current, previous):
        """Обробник вибору елемента зі списку"""
        if not current:
            return
        
        # Отримуємо текст з userData
        element_data = current.data(Qt.UserRole)
        if element_data:
            text = element_data.get('full_text', '')
            self.preview_text.setPlainText(text)
    
    def display_results(self, result: dict):
        """
        Відображення результатів тестування
        
        Args:
            result: Dict з результатами від test_selector()
        """
        self.elements_list.clear()
        
        if not result.get('found', False):
            self.elements_count_label.setText("Елементів: 0")
            self.set_status(result.get('message', 'Елементи не знайдено'), "warning")
            self.use_btn.setEnabled(False)
            return
        
        # Відображення кількості
        count = result.get('count', 0)
        self.elements_count_label.setText(f"Елементів: {count}")
        
        # Додавання елементів до списку
        elements = result.get('elements', [])
        for elem in elements:
            if 'error' in elem:
                item_text = f"❌ Елемент #{elem['index']}: {elem['error']}"
                item = QListWidgetItem(item_text)
            else:
                tag = elem.get('tag', 'unknown')
                preview = elem.get('text_preview', '')[:50]
                length = elem.get('text_length', 0)
                
                item_text = f"📄 #{elem['index']} <{tag}> - {length} символів\n   {preview}..."
                item = QListWidgetItem(item_text)
                
                # Зберігаємо повний текст в userData
                item.setData(Qt.UserRole, {
                    'full_text': elem.get('text_preview', ''),
                    'tag': tag,
                    'index': elem['index']
                })
        
            self.elements_list.addItem(item)
        
        # Статус
        self.set_status(result.get('message', f'Знайдено {count} елементів'), "success")
        self.use_btn.setEnabled(True)
        
        # Автоматично вибираємо перший елемент
        if self.elements_list.count() > 0:
            self.elements_list.setCurrentRow(0)
    
    def set_status(self, message: str, status_type: str = "info"):
        """
        Встановлення статусу
        
        Args:
            message: Повідомлення
            status_type: Тип (info, success, warning, error)
        """
        self.status_label.setText(message)
        
        colors = {
            'info': '#e3f2fd',
            'success': '#c8e6c9',
            'warning': '#fff9c4',
            'error': '#ffcdd2'
        }
        
        color = colors.get(status_type, colors['info'])
        self.status_label.setStyleSheet(f"""
            background-color: {color};
            padding: 10px;
            border-radius: 4px;
            font-size: 13px;
        """)
    
    def get_current_selector(self) -> tuple:
        """
        Отримання поточного селектора
        
        Returns:
            tuple: (selector, selector_type)
        """
        selector = self.selector_input.text().strip()
        selector_type = "css" if self.selector_type_combo.currentText() == "CSS Selector" else "xpath"
        return selector, selector_type