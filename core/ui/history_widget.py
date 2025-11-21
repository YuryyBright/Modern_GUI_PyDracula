# ==================== ui/history_widget.py ====================

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QHBoxLayout
)
from PySide6.QtCore import pyqtSignal


class HistoryWidget(QWidget):
    """Віджет історії запитів"""
    
    load_item_signal = pyqtSignal(int)  # extraction_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Час", "URL", "Селектор", "Символів", "Кеш"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.doubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("🔄 Оновити")
        button_layout.addWidget(self.refresh_button)
        
        self.clear_button = QPushButton("🗑️ Очистити")
        button_layout.addWidget(self.clear_button)
        
        layout.addLayout(button_layout)
    
    def add_item(self, timestamp: str, url: str, selector: str, 
                 char_count: int, cached: bool):
        """Додавання запису в історію"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(timestamp))
        self.table.setItem(row, 1, QTableWidgetItem(url[:50] + "..."))
        self.table.setItem(row, 2, QTableWidgetItem(selector[:30]))
        self.table.setItem(row, 3, QTableWidgetItem(str(char_count)))
        self.table.setItem(row, 4, QTableWidgetItem("✓" if cached else "✗"))
    
    def on_item_double_clicked(self):
        """Подвійний клік на записі"""
        row = self.table.currentRow()
        if row >= 0:
            self.load_item_signal.emit(row)