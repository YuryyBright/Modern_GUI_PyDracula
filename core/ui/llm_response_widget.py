# ==================== ui/llm_response_widget.py ====================

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel, QHBoxLayout


class LLMResponseWidget(QWidget):
    """Віджет для відображення відповіді LLM"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        self.header = QLabel("Відповідь LLM")
        self.header.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(self.header)
        
        self.cache_badge = QLabel("")
        header_layout.addWidget(self.cache_badge)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Response display
        self.response_edit = QTextEdit()
        self.response_edit.setReadOnly(True)
        self.response_edit.setPlaceholderText("Відповідь LLM з'явиться тут...")
        layout.addWidget(self.response_edit)
        
        # Stats
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("font-size: 10px; color: #888;")
        layout.addWidget(self.stats_label)
    
    def set_response(self, response: str, from_cache: bool = False, 
                     processing_time: float = 0, tokens_used: int = 0):
        """Встановлення відповіді"""
        self.response_edit.setPlainText(response)
        
        # Cache badge
        if from_cache:
            self.cache_badge.setText("📦 З кешу")
            self.cache_badge.setStyleSheet("color: #4a9eff; padding: 3px;")
        else:
            self.cache_badge.setText("🆕 Нова")
            self.cache_badge.setStyleSheet("color: #50fa7b; padding: 3px;")
        
        # Stats
        stats = f"Час: {processing_time:.2f}s | Токени: {tokens_used}"
        self.stats_label.setText(stats)