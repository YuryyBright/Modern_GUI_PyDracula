# ///////////////////////////////////////////////////////////////
#
# BY: WANDERSON M.PIMENTA
# PROJECT MADE WITH: Qt Designer and PySide6
# V: 2.0.0
#
# Modified with async/threading support for scalable applications
# FIXED: Web Assistant integration with Research Widget
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


# ==================== ДОДАТКОВІ ІМПОРТИ ====================

from core.services.web_analyzer_service import WebAnalyzerService
from core.ui.control_panel import ControlPanel
from core.ui.text_display_widget import TextDisplayWidget
from core.ui.llm_response_widget import LLMResponseWidget
from core.ui.history_widget import HistoryWidget
from core.ui.debug_panel import DebugPanel
from core.ui.research_widget import ResearchWidget
from core.utils.logger import get_logger

logger = get_logger(__name__)

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

        # Ініціалізація Web Assistant Service
        self.web_analyzer = WebAnalyzerService()
        
        # Додавання Web Assistant UI компонентів
        self.setup_web_assistant_ui()
        
        # Підключення Web Assistant подій
        self.connect_web_assistant_events()
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
    
    def onNavigateResearch(self):
        """Перехід на сторінку дослідження"""
        if hasattr(self, 'research_widget'):
            widgets.stackedWidget.setCurrentWidget(self.research_widget)
            # Якщо є кнопка для Research в меню, оновити стиль
            if hasattr(widgets, 'btn_research'):
                UIFunctions.resetStyle(self, "btn_research")
                widgets.btn_research.setStyleSheet(UIFunctions.selectMenu(widgets.btn_research.styleSheet()))
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


    # ==================== ORIGINAL METHODS ====================
       
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
        
        # Якщо є кнопка Research в меню
        if hasattr(widgets, 'btn_research'):
            widgets.btn_research.clicked.connect(lambda: self.event_handler.handle('navigate_research'))
        
        # ACTION BUTTONS with async support
        # widgets.start.clicked.connect(lambda: self.event_handler.handle('start_task'))
        # widgets.stop.clicked.connect(lambda: self.event_handler.handle('stop_task'))

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
        self.event_handler.register('navigate_research', self.onNavigateResearch)  # НОВЕ
        
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

    def setup_web_assistant_ui(self):
        """Налаштування UI компонентів Web Assistant"""
        
        # Control Panel (панель керування)
        self.control_panel = ControlPanel(widgets, self)

        # widgets.work_tab.layout().addWidget(self.control_panel)
        
        # Text Display Widget (оригінальний текст)
        self.text_display = TextDisplayWidget(self)
        widgets.stackedWidget.addWidget(self.text_display)
        
        # LLM Response Widget (відповідь LLM)
        self.llm_response = LLMResponseWidget(self)
        widgets.stackedWidget.addWidget(self.llm_response)
        
        # History Widget (історія запитів)
        self.history_widget = HistoryWidget(self)
        widgets.stackedWidget.addWidget(self.history_widget)
        
        # Research Widget (дослідження селекторів)
        self.research_widget = ResearchWidget(self)
        widgets.stackedWidget.addWidget(self.research_widget)
        
        # Debug Panel
        self.debug_panel = DebugPanel(self)
        widgets.stackedWidget.addWidget(self.debug_panel)
        
        logger.info("Web Assistant UI components initialized")

    def connect_web_assistant_events(self):
        """Підключення обробників подій Web Assistant"""
        
        # Control Panel signals
        self.control_panel.start_session_signal.connect(self.on_start_session)
        self.control_panel.stop_session_signal.connect(self.on_stop_session)
        self.control_panel.navigate_signal.connect(self.on_navigate)
        self.control_panel.extract_signal.connect(self.on_extract_text)
        self.control_panel.analyze_signal.connect(self.on_analyze_text)
        self.control_panel.clear_cache_signal.connect(self.on_clear_cache)
        
        # Research Widget signals
        self.research_widget.test_selector_signal.connect(self.on_test_selector)
        self.research_widget.use_selector_signal.connect(self.on_use_selector)
        
        # History Widget signals
        self.history_widget.load_item_signal.connect(self.on_load_history_item)
        self.history_widget.refresh_button.clicked.connect(self.on_refresh_history)
        self.history_widget.clear_button.clicked.connect(self.on_clear_history)
        
        logger.info("Web Assistant events connected")

    def on_start_session(self, mode: str):
        """Асинхронний запуск сесії"""
        logger.info(f"Starting Web Assistant session: mode={mode}")
        
        def task(progress_callback=None):
            if progress_callback:
                progress_callback(0, "Ініціалізація сесії...")
            session_id = self.web_analyzer.start_session(mode)
            if progress_callback:
                progress_callback(100, "Сесія запущена")
            return {'success': True, 'session_id': session_id}
        
        def on_complete(result: dict):
            if result.get('success'):
                session_id = result['session_id']
                self.control_panel.set_status(f"Сесія активна: {session_id[:8]}...")
                self.debug_panel.log(f"Session started: {session_id}", "SUCCESS")
                logger.info(f"Session started: {session_id}")
            else:
                self.control_panel.set_status("Помилка запуску сесії")
                self.debug_panel.log("Failed to start session", "ERROR")
        
        def on_error(error: tuple):
            exc_type, exc_value, _ = error
            self.control_panel.set_status(f"Помилка: {exc_value}")
            self.debug_panel.log(f"Error: {exc_value}", "ERROR")
            logger.error(f"Error starting session: {exc_value}")
        
        def on_progress(progress: int, message: str):
            logger.info(f"Progress: {progress}% - {message}")
            self.control_panel.set_status(message)
        
        self.runBackgroundTask(
            task,
            on_complete=on_complete,
            on_error=on_error,
            on_progress=on_progress
        )
        
        self.control_panel.set_status("Запуск сесії...")

    def on_stop_session(self):
        """Асинхронна зупинка сесії"""
        logger.info("Stopping Web Assistant session")
        
        def task(progress_callback=None):
            if progress_callback:
                progress_callback(0, "Зупинка сесії...")
            self.web_analyzer.end_session()
            if progress_callback:
                progress_callback(100, "Сесія зупинена")
            return {'success': True}
        
        def on_complete(result: dict):
            if result.get('success'):
                self.control_panel.set_status("Сесія зупинена")
                self.debug_panel.log("Session stopped", "SUCCESS")
                logger.info("Session stopped")
            else:
                self.control_panel.set_status("Помилка зупинки сесії")
                self.debug_panel.log("Failed to stop session", "ERROR")
        
        def on_error(error: tuple):
            exc_type, exc_value, _ = error
            self.control_panel.set_status(f"Помилка: {exc_value}")
            self.debug_panel.log(f"Error: {exc_value}", "ERROR")
            logger.error(f"Error stopping session: {exc_value}")
        
        def on_progress(progress: int, message: str):
            logger.info(f"Progress: {progress}% - {message}")
            self.control_panel.set_status(message)
        
        self.runBackgroundTask(
            task,
            on_complete=on_complete,
            on_error=on_error,
            on_progress=on_progress
        )
        
        self.control_panel.set_status("Зупинка сесії...")

    def on_navigate(self, url: str):
        """Асинхронна навігація"""
        logger.info(f"Navigating to: {url}")
        
        def task(progress_callback=None):
            if progress_callback:
                progress_callback(0, "Навігація...")
            self.web_analyzer.navigate_to_url(url)
            if progress_callback:
                progress_callback(100, "Навігація завершена")
            return {'success': True, 'url': url}
        
        def on_complete(result: dict):
            if result.get('success'):
                self.control_panel.set_status(f"Навігація завершена: {result['url']}")
                self.debug_panel.log(f"Navigated to {result['url']}", "INFO")
                logger.info(f"Navigated to: {result['url']}")
                # Оновіть research_widget або інші, якщо потрібно
        
        def on_error(error: tuple):
            exc_type, exc_value, _ = error
            self.control_panel.set_status(f"Помилка навігації: {exc_value}")
            self.debug_panel.log(f"Error navigating: {exc_value}", "ERROR")
            logger.error(f"Error navigating: {exc_value}")
        
        def on_progress(progress: int, message: str):
            logger.info(f"Progress: {progress}% - {message}")
            self.control_panel.set_status(message)
        
        self.runBackgroundTask(
            task,
            on_complete=on_complete,
            on_error=on_error,
            on_progress=on_progress
        )
        
        self.control_panel.set_status(f"Навігація до {url}...")

    def on_extract_text(self, selector: str, selector_type: str):
        """Асинхронне витягування тексту"""
        logger.info(f"Extracting text with selector: {selector} ({selector_type})")
        
        def task(progress_callback=None):
            if progress_callback:
                progress_callback(0, "Витягування тексту...")
            
            extraction_result = self.web_analyzer.extract_text(selector, selector_type)
            
            text = extraction_result['text']
            metadata = extraction_result['metadata']

            if progress_callback:
                progress_callback(100, "Текст витягнуто")
            
            # Return the data structure expected by on_complete
            return {'success': True, 'text': text, 'metadata': metadata}
        
        def on_complete(result: dict):
            if result.get('success'):
                self.text_display.set_text(result['text'], result['metadata'])
                self.control_panel.set_status("Текст витягнуто успішно")
                self.debug_panel.log("Text extracted successfully", "SUCCESS")
                logger.info("Text extracted")
                # Оновіть history_widget.add_item(...)
        
        def on_error(error: tuple):
            exc_type, exc_value, _ = error
            self.control_panel.set_status(f"Помилка витягування: {exc_value}")
            self.debug_panel.log(f"Error extracting: {exc_value}", "ERROR")
            logger.error(f"Error extracting: {exc_value}")
        
        def on_progress(progress: int, message: str):
            logger.info(f"Progress: {progress}% - {message}")
            self.control_panel.set_status(message)
        
        self.runBackgroundTask(
            task,
            on_complete=on_complete,
            on_error=on_error,
            on_progress=on_progress
        )
        
        self.control_panel.set_status("Витягування тексту...")

    def on_analyze_text(self, prompt_type: str):
        """Асинхронний аналіз тексту LLM"""
        logger.info(f"Analyzing text with prompt: {prompt_type}")
        
        def task(progress_callback=None):
            if progress_callback:
                progress_callback(0, "Аналіз LLM...")
            response, stats = self.web_analyzer.analyze_text(prompt_type)
            if progress_callback:
                progress_callback(100, "Аналіз завершено")
            return {'success': True, 'response': response, 'stats': stats}
        
        def on_complete(result: dict):
            if result.get('success'):
                self.llm_response.set_response(result['response'], stats=result['stats'])
                self.control_panel.set_status("Аналіз завершено")
                self.debug_panel.log("Analysis completed", "SUCCESS")
                logger.info("Text analyzed")
        
        def on_error(error: tuple):
            exc_type, exc_value, _ = error
            self.control_panel.set_status(f"Помилка аналізу: {exc_value}")
            self.debug_panel.log(f"Error analyzing: {exc_value}", "ERROR")
            logger.error(f"Error analyzing: {exc_value}")
        
        def on_progress(progress: int, message: str):
            logger.info(f"Progress: {progress}% - {message}")
            self.control_panel.set_status(message)
        
        self.runBackgroundTask(
            task,
            on_complete=on_complete,
            on_error=on_error,
            on_progress=on_progress
        )
        
        self.control_panel.set_status("Аналіз LLM...")

    def on_clear_cache(self):
        """Асинхронне очищення кешу"""
        logger.info("Clearing cache")
        
        def task(progress_callback=None):
            if progress_callback:
                progress_callback(0, "Очищення кешу...")
            self.web_analyzer.clear_cache()
            if progress_callback:
                progress_callback(100, "Кеш очищено")
            return {'success': True}
        
        def on_complete(result: dict):
            if result.get('success'):
                self.control_panel.set_status("Кеш очищено")
                self.debug_panel.log("Cache cleared", "INFO")
                logger.info("Cache cleared")
                # Оновіть history_widget, якщо потрібно
        
        def on_error(error: tuple):
            exc_type, exc_value, _ = error
            self.control_panel.set_status(f"Помилка очищення: {exc_value}")
            self.debug_panel.log(f"Error clearing cache: {exc_value}", "ERROR")
            logger.error(f"Error clearing cache: {exc_value}")
        
        def on_progress(progress: int, message: str):
            logger.info(f"Progress: {progress}% - {message}")
            self.control_panel.set_status(message)
        
        self.runBackgroundTask(
            task,
            on_complete=on_complete,
            on_error=on_error,
            on_progress=on_progress
        )
        
        self.control_panel.set_status("Очищення кешу...")

    def on_test_selector(self, selector: str, selector_type: str):
        """Асинхронне тестування селектора в ResearchWidget"""
        logger.info(f"Testing selector: {selector} ({selector_type})")
        
        def task(progress_callback=None):
            if progress_callback:
                progress_callback(0, "Тестування селектора...")
            result = self.web_analyzer.test_selector(selector, selector_type)
            if progress_callback:
                progress_callback(100, "Тест завершено")
            return {'success': True, 'result': result}
        
        def on_complete(result: dict):
            if result.get('success'):
                self.research_widget.display_results(result['result'])
                self.control_panel.set_status("Тест селектора завершено")
                logger.info("Selector tested")
        
        def on_error(error: tuple):
            exc_type, exc_value, _ = error
            self.control_panel.set_status(f"Помилка тесту: {exc_value}")
            logger.error(f"Error testing selector: {exc_value}")
        
        self.runBackgroundTask(
            task,
            on_complete=on_complete,
            on_error=on_error
        )

    def on_use_selector(self, selector: str, selector_type: str):
        """Застосування селектора з ResearchWidget"""
        self.control_panel.selector_input.setText(selector)
        self.control_panel.selector_type_combo.setCurrentText(selector_type.upper())
        self.control_panel.set_status("Селектор застосовано")
        logger.info(f"Selector applied: {selector} ({selector_type})")

    def on_refresh_history(self):
        """Асинхронне оновлення історії"""
        logger.info("Refreshing history")
        
        def task(progress_callback=None):
            history = self.web_analyzer.get_history()
            return {'success': True, 'history': history}
        
        def on_complete(result: dict):
            if result.get('success'):
                self.history_widget.clear()
                for item in result['history']:
                    self.history_widget.add_item(**item)
                self.control_panel.set_status("Історія оновлена")
                logger.info("History refreshed")
        
        def on_error(error: tuple):
            exc_type, exc_value, _ = error
            self.control_panel.set_status(f"Помилка оновлення історії: {exc_value}")
            logger.error(f"Error refreshing history: {exc_value}")
        
        self.runBackgroundTask(
            task,
            on_complete=on_complete,
            on_error=on_error
        )
        
        self.control_panel.set_status("Оновлення історії...")

    def on_clear_history(self):
        """Асинхронне очищення історії"""
        logger.info("Clearing history")
        
        def task(progress_callback=None):
            self.web_analyzer.clear_history()
            return {'success': True}
        
        def on_complete(result: dict):
            if result.get('success'):
                self.history_widget.clear()
                self.control_panel.set_status("Історія очищена")
                logger.info("History cleared")
        
        def on_error(error: tuple):
            exc_type, exc_value, _ = error
            self.control_panel.set_status(f"Помилка очищення історії: {exc_value}")
            logger.error(f"Error clearing history: {exc_value}")
        
        self.runBackgroundTask(
            task,
            on_complete=on_complete,
            on_error=on_error
        )
        
        self.control_panel.set_status("Очищення історії...")

    def on_load_history_item(self, extraction_id: int):
        """Асинхронне завантаження елемента історії"""
        logger.info(f"Loading history item: {extraction_id}")
        
        def task(progress_callback=None):
            data = self.web_analyzer.load_from_history(extraction_id)
            return {'success': True, 'data': data}
        
        def on_complete(result: dict):
            if result.get('success'):
                data = result['data']
                self.text_display.set_text(data['text'], data['metadata'])
                self.llm_response.set_response(data['response'], from_cache=data['from_cache'], 
                                               processing_time=data['time'], tokens_used=data['tokens'])
                self.control_panel.set_status("Елемент історії завантажено")
                logger.info(f"History item loaded: {extraction_id}")
        
        def on_error(error: tuple):
            exc_type, exc_value, _ = error
            self.control_panel.set_status(f"Помилка завантаження: {exc_value}")
            logger.error(f"Error loading history: {exc_value}")
        
        self.runBackgroundTask(
            task,
            on_complete=on_complete,
            on_error=on_error
        )
        
        self.control_panel.set_status("Завантаження елемента історії...")

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
        if hasattr(widgets, 'start'):
            widgets.start.setEnabled(True)
        if hasattr(widgets, 'stop'):
            widgets.stop.setEnabled(False)
        
        # Update UI
        # widgets.statusLabel.setText(result.get('message', 'Task completed'))

    def onTaskError(self, error: tuple):
        """Callback при помилці виконання завдання"""
        exc_type, exc_value, exc_traceback = error
        print(f"[ERROR] Task failed: {exc_value}")
        
        # Re-enable buttons
        if hasattr(widgets, 'start'):
            widgets.start.setEnabled(True)
        if hasattr(widgets, 'stop'):
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
        """Обробка закриття програми"""
        print("[INFO] Closing application...")
        
        # WEB ASSISTANT CLEANUP
        if hasattr(self, 'web_analyzer'):
            try:
                self.web_analyzer.end_session()
                logger.info("Web Assistant session ended")
            except Exception as e:
                logger.error(f"Error ending session: {e}")
        
        # Stop all running tasks
        self.task_manager.stop_all()
        self.task_manager.wait_all()
        
        print("[INFO] Application closed successfully")
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))
    window = MainWindow()
    sys.exit(app.exec())