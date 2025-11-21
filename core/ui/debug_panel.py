# ==================== ui/debug_panel.py ====================

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from datetime import datetime


class DebugPanel(QWidget):
    """Debug панель з логами"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Log display
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setMaximumHeight(200)
        self.log_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(self.log_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("Очистити")
        self.clear_button.clicked.connect(self.clear_logs)
        button_layout.addWidget(self.clear_button)
        
        self.save_button = QPushButton("Зберегти")
        button_layout.addWidget(self.save_button)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def log(self, message: str, level: str = "INFO"):
        """Додавання логу"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Кольорове кодування
        color_map = {
            "INFO": "#4a9eff",
            "SUCCESS": "#50fa7b",
            "WARNING": "#f1fa8c",
            "ERROR": "#ff5555"
        }
        
        color = color_map.get(level, "#d4d4d4")
        
        formatted = f'<span style="color: #888;">[{timestamp}]</span> '
        formatted += f'<span style="color: {color};">{message}</span>'
        
        self.log_edit.append(formatted)
        
        # Auto-scroll
        scrollbar = self.log_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_logs(self):
        """Очищення логів"""
        self.log_edit.clear()