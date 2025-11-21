# ==================== ui/text_display_widget.py ====================

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel
from PySide6.QtCore import Qt


class TextDisplayWidget(QWidget):
    """Віджет для відображення витягнутого тексту"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        self.header = QLabel("Витягнутий текст")
        self.header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(self.header)
        
        # Text display
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlaceholderText("Текст з'явиться тут після витягування...")
        layout.addWidget(self.text_edit)
        
        # Metadata
        self.metadata_label = QLabel("")
        self.metadata_label.setStyleSheet("font-size: 10px; color: #888;")
        layout.addWidget(self.metadata_label)
    
    def set_text(self, text: str, metadata: dict = None):
        """Встановлення тексту"""
        self.text_edit.setPlainText(text)
        
        if metadata:
            meta_text = f"Символів: {metadata.get('char_count', 0)} | Слів: {metadata.get('word_count', 0)}"
            self.metadata_label.setText(meta_text)
