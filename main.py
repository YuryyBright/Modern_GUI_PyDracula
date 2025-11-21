# ///////////////////////////////////////////////////////////////
#
# BY: WANDERSON M.PIMENTA
# PROJECT MADE WITH: Qt Designer and PySide6
# V: 2.0.0
#
# Modified with async/threading support for scalable applications
#
# ///////////////////////////////////////////////////////////////

import sys
import os
import platform
from typing import Callable, Optional, Any
from functools import wraps

# IMPORT / GUI AND MODULES AND WIDGETS
# ///////////////////////////////////////////////////////////////
from modules import *
from widgets import *
from core.ui_helper.worker_thread import WorkerThread, WorkerSignals
from core.ui_helper.task_manager import TaskManager
from core.ui_helper.event_handler import EventHandler

os.environ["QT_FONT_DPI"] = "96"

# SET AS GLOBAL WIDGETS
# ///////////////////////////////////////////////////////////////
widgets = None

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        # SET AS GLOBAL WIDGETS
        # ///////////////////////////////////////////////////////////////
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        global widgets
        widgets = self.ui

        # INITIALIZE CORE COMPONENTS
        # ///////////////////////////////////////////////////////////////
        self.task_manager = TaskManager()
        self.event_handler = EventHandler(self)
        
        # USE CUSTOM TITLE BAR | USE AS "False" FOR MAC OR LINUX
        # ///////////////////////////////////////////////////////////////
        Settings.ENABLE_CUSTOM_TITLE_BAR = True

        # APP INITIALIZATION
        # ///////////////////////////////////////////////////////////////
        self.initializeApp()
        
        # SETUP UI
        # ///////////////////////////////////////////////////////////////
        self.setupUI()
        
        # CONNECT EVENTS
        # ///////////////////////////////////////////////////////////////
        self.connectEvents()

        # SHOW APP
        # ///////////////////////////////////////////////////////////////
        self.show()

        # POST INITIALIZATION (after window is shown)
        # ///////////////////////////////////////////////////////////////
        self.postInitialize()

    def initializeApp(self):
        """
        Ініціалізація додатку - виконується перед показом UI
        Тут можна завантажити конфігурації, підключитись до БД, тощо
        """
        # APP NAME
        title = "Ptichka - Modern GUI"
        description = "AI Assistant APP with Async Support"
        
        # APPLY TEXTS
        self.setWindowTitle(title)
        widgets.titleRightInfo.setText(description)
        
        # Load configurations
        self.loadConfig()
        
        # Initialize database connection (example)
        # self.db = Database()
        
        print("[INFO] Application initialized")

    def loadConfig(self):
        """Завантаження конфігурації"""
        # Example: load settings from file
        self.config = {
            'theme': 'dark',
            'language': 'uk',
            'auto_save': True
        }

    def setupUI(self):
        """Налаштування UI елементів"""
        # SET UI DEFINITIONS
        UIFunctions.uiDefinitions(self)

        # QTableWidget PARAMETERS
        widgets.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # SET CUSTOM THEME
        useCustomTheme = False
        themeFile = "themes/py_dracula_dark.qss"

        if useCustomTheme:
            UIFunctions.theme(self, themeFile, True)
            AppFunctions.setThemeHack(self)

        # SET HOME PAGE AND SELECT MENU
        widgets.stackedWidget.setCurrentWidget(widgets.home)
        widgets.btn_home.setStyleSheet(UIFunctions.selectMenu(widgets.btn_home.styleSheet()))

    def connectEvents(self):
        """
        Підключення всіх обробників подій
        Централізоване місце для всіх з'єднань
        """
        # TOGGLE MENU
        widgets.toggleButton.clicked.connect(lambda: UIFunctions.toggleMenu(self, True))

        # LEFT MENUS - використовуємо event_handler для маршрутизації
        widgets.btn_home.clicked.connect(lambda: self.event_handler.handle('navigate_home'))
        widgets.btn_widgets.clicked.connect(lambda: self.event_handler.handle('navigate_widgets'))
        widgets.btn_new.clicked.connect(lambda: self.event_handler.handle('navigate_new'))
        widgets.btn_save.clicked.connect(lambda: self.event_handler.handle('save_data'))
        
        # ACTION BUTTONS with async support
        widgets.start.clicked.connect(lambda: self.event_handler.handle('start_task'))
        widgets.stop.clicked.connect(lambda: self.event_handler.handle('stop_task'))

        # EXTRA LEFT BOX
        widgets.toggleLeftBox.clicked.connect(lambda: UIFunctions.toggleLeftBox(self, True))
        widgets.extraCloseColumnBtn.clicked.connect(lambda: UIFunctions.toggleLeftBox(self, True))

        # EXTRA RIGHT BOX
        widgets.settingsTopBtn.clicked.connect(lambda: UIFunctions.toggleRightBox(self, True))

        # REGISTER EVENT HANDLERS
        self.registerEventHandlers()

    def registerEventHandlers(self):
        """
        Реєстрація обробників подій
        Тут ви можете легко додавати нові обробники
        """
        # Navigation handlers
        self.event_handler.register('navigate_home', self.onNavigateHome)
        self.event_handler.register('navigate_widgets', self.onNavigateWidgets)
        self.event_handler.register('navigate_new', self.onNavigateNew)
        
        # Action handlers
        self.event_handler.register('save_data', self.onSaveData)
        self.event_handler.register('start_task', self.onStartTask)
        self.event_handler.register('stop_task', self.onStopTask)

    def postInitialize(self):
        """
        Виконується після показу вікна
        Тут можна запускати фонові завдання
        """
        # Example: start background task
        # self.runBackgroundTask(self.checkUpdates, on_complete=self.onUpdatesChecked)
        print("[INFO] Post initialization completed")

    # ===============================================================
    # NAVIGATION HANDLERS
    # ===============================================================
    
    def onNavigateHome(self):
        """Перехід на головну сторінку"""
        widgets.stackedWidget.setCurrentWidget(widgets.home)
        UIFunctions.resetStyle(self, "btn_home")
        widgets.btn_home.setStyleSheet(UIFunctions.selectMenu(widgets.btn_home.styleSheet()))

    def onNavigateWidgets(self):
        """Перехід на сторінку віджетів"""
        widgets.stackedWidget.setCurrentWidget(widgets.widgets)
        UIFunctions.resetStyle(self, "btn_widgets")
        widgets.btn_widgets.setStyleSheet(UIFunctions.selectMenu(widgets.btn_widgets.styleSheet()))

    def onNavigateNew(self):
        """Перехід на нову сторінку"""
        widgets.stackedWidget.setCurrentWidget(widgets.new_page)
        UIFunctions.resetStyle(self, "btn_new")
        widgets.btn_new.setStyleSheet(UIFunctions.selectMenu(widgets.btn_new.styleSheet()))

    # ===============================================================
    # ACTION HANDLERS
    # ===============================================================
    
    def onSaveData(self):
        """Збереження даних"""
        print("[ACTION] Saving data...")
        
        # Example: run save operation in background
        self.runBackgroundTask(
            self.saveDataAsync,
            on_complete=self.onSaveComplete,
            on_error=self.onSaveError
        )

    def onStartTask(self):
        """Запуск довготривалого завдання"""
        print("[ACTION] Starting long task...")
        
        # Disable start button during task execution
        widgets.start.setEnabled(False)
        widgets.stop.setEnabled(True)
        
        # Run task in background with progress updates
        self.runBackgroundTask(
            self.longRunningTask,
            on_progress=self.onTaskProgress,
            on_complete=self.onTaskComplete,
            on_error=self.onTaskError
        )

    def onStopTask(self):
        """Зупинка завдання"""
        print("[ACTION] Stopping task...")
        self.task_manager.stop_all()
        widgets.start.setEnabled(True)
        widgets.stop.setEnabled(False)

    # ===============================================================
    # BACKGROUND TASKS (приклади)
    # ===============================================================
    
    def saveDataAsync(self, progress_callback: Optional[Callable] = None) -> dict:
        """
        Приклад асинхронного збереження даних
        
        Args:
            progress_callback: Callback для оновлення прогресу
            
        Returns:
            dict: Результат операції
        """
        import time
        
        if progress_callback:
            progress_callback(0, "Initializing save...")
        
        time.sleep(1)
        
        if progress_callback:
            progress_callback(50, "Saving data...")
        
        # Simulate save operation
        time.sleep(1)
        
        if progress_callback:
            progress_callback(100, "Save complete")
        
        return {'success': True, 'message': 'Data saved successfully'}

    def longRunningTask(self, progress_callback: Optional[Callable] = None) -> dict:
        """
        Приклад довготривалого завдання з оновленням прогресу
        
        Args:
            progress_callback: Callback для оновлення прогресу (progress, message)
            
        Returns:
            dict: Результат роботи
        """
        import time
        
        total_steps = 10
        
        for step in range(total_steps):
            # Check if task should be stopped
            if self.task_manager.should_stop():
                return {'success': False, 'message': 'Task stopped by user'}
            
            # Simulate work
            time.sleep(0.5)
            
            # Update progress
            if progress_callback:
                progress = int((step + 1) / total_steps * 100)
                progress_callback(progress, f"Processing step {step + 1}/{total_steps}")
        
        return {'success': True, 'message': 'Task completed successfully', 'steps': total_steps}

    # ===============================================================
    # CALLBACKS FOR BACKGROUND TASKS
    # ===============================================================
    
    def onSaveComplete(self, result: dict):
        """Callback після завершення збереження"""
        print(f"[SUCCESS] {result.get('message', 'Save completed')}")
        # Update UI
        # widgets.statusLabel.setText("Data saved successfully")

    def onSaveError(self, error: tuple):
        """Callback при помилці збереження"""
        exc_type, exc_value, exc_traceback = error
        print(f"[ERROR] Save failed: {exc_value}")
        # Show error message
        # QMessageBox.critical(self, "Error", f"Failed to save data: {exc_value}")

    def onTaskProgress(self, progress: int, message: str):
        """Callback для оновлення прогресу завдання"""
        print(f"[PROGRESS] {progress}% - {message}")
        # Update progress bar
        # widgets.progressBar.setValue(progress)
        # widgets.statusLabel.setText(message)

    def onTaskComplete(self, result: dict):
        """Callback після завершення завдання"""
        print(f"[SUCCESS] Task completed: {result}")
        
        # Re-enable buttons
        widgets.start.setEnabled(True)
        widgets.stop.setEnabled(False)
        
        # Update UI
        # widgets.statusLabel.setText(result.get('message', 'Task completed'))

    def onTaskError(self, error: tuple):
        """Callback при помилці виконання завдання"""
        exc_type, exc_value, exc_traceback = error
        print(f"[ERROR] Task failed: {exc_value}")
        
        # Re-enable buttons
        widgets.start.setEnabled(True)
        widgets.stop.setEnabled(False)
        
        # Show error message
        # QMessageBox.critical(self, "Error", f"Task failed: {exc_value}")

    # ===============================================================
    # UTILITY METHODS
    # ===============================================================
    
    def runBackgroundTask(
        self,
        task: Callable,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        on_progress: Optional[Callable] = None,
        *args,
        **kwargs
    ) -> WorkerThread:
        """
        Запуск завдання в фоновому потоці
        
        Args:
            task: Функція для виконання
            on_complete: Callback після успішного завершення
            on_error: Callback при помилці
            on_progress: Callback для оновлення прогресу
            *args, **kwargs: Аргументи для task
            
        Returns:
            WorkerThread: Об'єкт потоку
        """
        return self.task_manager.run_task(
            task,
            on_complete=on_complete,
            on_error=on_error,
            on_progress=on_progress,
            *args,
            **kwargs
        )

    # ===============================================================
    # WINDOW EVENTS
    # ===============================================================
    
    def resizeEvent(self, event):
        """Обробка зміни розміру вікна"""
        UIFunctions.resize_grips(self)

    def mousePressEvent(self, event):
        """Обробка натискання миші"""
        self.dragPos = event.globalPos()

    def closeEvent(self, event):
        """Обробка закриття вікна"""
        print("[INFO] Closing application...")
        
        # Stop all running tasks
        self.task_manager.stop_all()
        self.task_manager.wait_all()
        
        # Clean up resources
        # self.db.close()
        
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))
    window = MainWindow()
    sys.exit(app.exec_())