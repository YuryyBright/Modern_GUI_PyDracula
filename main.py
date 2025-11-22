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

    # ==================== НОВИЙ МЕТОД: setupWebAssistantUI ====================

    def setup_web_assistant_ui(self):
        """Налаштування UI компонентів Web Assistant"""
        
        # Control Panel (панель керування)
        self.control_panel = ControlPanel(widgets, self)



        # widgets.work_tab.layout().addWidget(self.control_panel)
        
        # # Text Display Widget (оригінальний текст)
        # self.text_display = TextDisplayWidget(self)
        # widgets.stackedWidget.addWidget(self.text_display)
        
        # # LLM Response Widget (відповідь LLM)
        # self.llm_response = LLMResponseWidget(self)
        # widgets.stackedWidget.addWidget(self.llm_response)
        
        # # History Widget (історія запитів)
        # self.history_widget = HistoryWidget(self)
        # widgets.stackedWidget.addWidget(self.history_widget)
        
        # # Research Widget (дослідження селекторів) - НОВЕ
        # self.research_widget = ResearchWidget(self)
        # widgets.stackedWidget.addWidget(self.research_widget)
        
        # # Debug Panel (логи в реальному часі)
        # self.debug_panel = DebugPanel(self)
        # # Додати до нижньої частини
        # if hasattr(widgets, 'bottomContainer'):
        #     widgets.bottomContainer.layout().addWidget(self.debug_panel)
        
        logger.info("Web Assistant UI components initialized")


    # ==================== НОВИЙ МЕТОД: connectWebAssistantEvents ====================

    def connect_web_assistant_events(self):
        """Підключення обробників подій Web Assistant"""
        
        # Control Panel signals
        self.control_panel.start_session_signal.connect(self.on_start_session)
        self.control_panel.stop_session_signal.connect(self.on_stop_session)
        self.control_panel.navigate_signal.connect(self.on_navigate)
        self.control_panel.extract_signal.connect(self.on_extract_text)
        self.control_panel.analyze_signal.connect(self.on_analyze_text)
        self.control_panel.clear_cache_signal.connect(self.on_clear_cache)
        
        # Research Widget signals - НОВЕ
        # self.research_widget.test_selector_signal.connect(self.on_test_selector)
        # self.research_widget.use_selector_signal.connect(self.on_use_selector_in_analyzer)
        
        logger.info("Web Assistant events connected")
    
    # ==================== WEB ASSISTANT ОБРОБНИКИ ====================

    def on_start_session(self, mode: str):
        """Запуск сесії Web Assistant"""
        logger.info(f"Starting Web Assistant session: mode={mode}")
        
        try:
            session_id = self.web_analyzer.start_session(mode)
            
            # Оновлення UI
            self.control_panel.set_status(f"Сесія активна: {session_id[:8]}...")
            
            # Показати debug panel
            if hasattr(self, 'debug_panel'):
                self.debug_panel.log(f"✅ Сесія запущена: {mode}")
            
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            self.control_panel.set_status(f"Помилка: {e}")


    def on_stop_session(self):
        """Зупинка сесії"""
        logger.info("Stopping Web Assistant session")
        
        try:
            # Отримання статистики перед завершенням
            stats = self.web_analyzer.get_statistics()
            
            self.web_analyzer.end_session()
            
            # Показати статистику
            stats_text = (
                f"Сесія завершена:\n"
                f"- Сторінок відвідано: {stats['session']['pages_visited']}\n"
                f"- Витягувань: {stats['session']['extractions_count']}\n"
                f"- LLM запитів: {stats['session']['llm_requests_count']}\n"
                f"- Cache hits: {stats['session']['cache_hits']}"
            )
            
            if hasattr(self, 'debug_panel'):
                self.debug_panel.log(stats_text)
            
            self.control_panel.set_status("Сесія завершена")
            
        except Exception as e:
            logger.error(f"Failed to stop session: {e}")


    def on_navigate(self, url: str):
        """Навігація на URL"""
        logger.info(f"Navigating to: {url}")
        
        # Запуск у фоновому потоці
        def navigate_task(progress_callback=None):
            try:
                if progress_callback:
                    progress_callback(0, "Навігація...")
                
                success = self.web_analyzer.navigate_to_url(url)
                
                if progress_callback:
                    progress_callback(100, "Завершено")
                
                return {'success': success, 'url': url}
                
            except Exception as e:
                logger.error(f"Navigation error: {e}")
                return {'success': False, 'error': str(e)}
        
        self.runBackgroundTask(
            navigate_task,
            on_complete=self.on_navigate_complete,
            on_error=self.on_navigate_error,
            on_progress=self.onTaskProgress
        )


    def on_navigate_complete(self, result: dict):
        """Callback після навігації"""
        if result['success']:
            message = f"✅ Завантажено: {result['url']}"
            self.control_panel.set_status("Готовий до витягування")
        else:
            message = f"❌ Помилка навігації: {result.get('error', 'Unknown')}"
        
        if hasattr(self, 'debug_panel'):
            self.debug_panel.log(message)


    def on_extract_text(self, selector: str, selector_type: str):
        """Витягування тексту"""
        logger.info(f"Extracting text: selector={selector}, type={selector_type}")
        
        def extract_task(progress_callback=None):
            try:
                if progress_callback:
                    progress_callback(0, "Витягування тексту...")
                
                result = self.web_analyzer.extract_text(
                    selector=selector,
                    selector_type=selector_type
                )
                
                if progress_callback:
                    progress_callback(100, "Текст витягнуто")
                
                return result
                
            except Exception as e:
                logger.error(f"Extraction error: {e}")
                raise
        
        self.runBackgroundTask(
            extract_task,
            on_complete=self.on_extract_complete,
            on_error=self.on_extract_error,
            on_progress=self.onTaskProgress
        )


    def on_extract_complete(self, result: dict):
        """Callback після витягування"""
        # Відображення тексту
        if hasattr(self, 'text_display'):
            self.text_display.set_text(
                text=result['text'],
                metadata=result['metadata']
            )
        
        # Лог
        message = (
            f"✅ Текст витягнуто:\n"
            f"  - Символів: {len(result['text'])}\n"
            f"  - Слів: {result['metadata']['word_count']}\n"
            f"  - Hash: {result['text_hash'][:16]}..."
        )
        
        if hasattr(self, 'debug_panel'):
            self.debug_panel.log(message)
        
        self.control_panel.set_status("Текст витягнуто. Готовий до аналізу")
        
        # Збереження для подальшого аналізу
        self.last_extraction = result


    def on_analyze_text(self, prompt_type: str):
        """Аналіз тексту через LLM"""
        if not hasattr(self, 'last_extraction'):
            logger.warning("No text to analyze")
            self.control_panel.set_status("Спочатку витягніть текст")
            return
        
        logger.info(f"Analyzing text: prompt_type={prompt_type}")
        
        def analyze_task(progress_callback=None):
            try:
                if progress_callback:
                    progress_callback(0, "Відправка до LLM...")
                
                result = self.web_analyzer.analyze_with_llm(
                    text=self.last_extraction['text'],
                    extraction_id=self.last_extraction['extraction_id'],
                    url=self.last_extraction['url'],
                    selector=self.last_extraction['selector'],
                    prompt_type=prompt_type
                )
                
                if progress_callback:
                    progress_callback(100, "Аналіз завершено")
                
                return result
                
            except Exception as e:
                logger.error(f"Analysis error: {e}")
                raise
        
        self.runBackgroundTask(
            analyze_task,
            on_complete=self.on_analyze_complete,
            on_error=self.on_analyze_error,
            on_progress=self.onTaskProgress
        )


    def on_analyze_complete(self, result: dict):
        """Callback після аналізу"""
        # Відображення відповіді LLM
        if hasattr(self, 'llm_response'):
            self.llm_response.set_response(
                response=result['response'],
                from_cache=result['from_cache'],
                processing_time=result['processing_time'],
                tokens_used=result['tokens_used']
            )
        
        # Лог
        cache_status = "📦 З кешу" if result['from_cache'] else "🆕 Нова відповідь"
        message = (
            f"✅ Аналіз завершено:\n"
            f"  - {cache_status}\n"
            f"  - Час: {result['processing_time']:.2f}s\n"
            f"  - Токенів: {result['tokens_used']}"
        )
        
        if hasattr(self, 'debug_panel'):
            self.debug_panel.log(message)
        
        self.control_panel.set_status("Аналіз завершено")


    def on_clear_cache(self):
        """Очищення кешу"""
        logger.info("Clearing cache")
        
        try:
            count = self.web_analyzer.clear_cache()
            
            message = f"✅ Кеш очищено: {count} записів видалено"
            
            if hasattr(self, 'debug_panel'):
                self.debug_panel.log(message)
            
            self.control_panel.set_status("Кеш очищено")
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")


    # ==================== RESEARCH WIDGET HANDLERS ====================
    
    def on_test_selector(self, selector: str, selector_type: str):
        """Тестування селектора"""
        logger.info(f"Testing selector: {selector} (type: {selector_type})")
        
        def test_task(progress_callback=None):
            try:
                if progress_callback:
                    progress_callback(0, "Тестування селектора...")
                
                result = self.web_analyzer.test_selector(
                    selector=selector,
                    selector_type=selector_type
                )
                
                if progress_callback:
                    progress_callback(100, "Тестування завершено")
                
                return result
                
            except Exception as e:
                logger.error(f"Selector test error: {e}")
                raise
        
        self.runBackgroundTask(
            test_task,
            on_complete=self.on_test_selector_complete,
            on_error=self.on_test_selector_error,
            on_progress=self.onTaskProgress
        )
    
    def on_test_selector_complete(self, result: dict):
        """Callback після тестування селектора"""
        # Відображення результатів в Research Widget
        if hasattr(self, 'research_widget'):
            self.research_widget.display_results(result)
        
        # Лог
        if hasattr(self, 'debug_panel'):
            message = result.get('message', 'Тестування завершено')
            self.debug_panel.log(message)
    
    def on_test_selector_error(self, error: tuple):
        """Обробка помилки тестування"""
        exc_type, exc_value, exc_traceback = error
        logger.error(f"Test selector error: {exc_value}")
        
        if hasattr(self, 'research_widget'):
            self.research_widget.set_status(f"❌ Помилка: {exc_value}", "error")
        
        if hasattr(self, 'debug_panel'):
            self.debug_panel.log(f"❌ Помилка тестування: {exc_value}")
    
    def on_use_selector_in_analyzer(self, selector: str, selector_type: str):
        """Застосування селектора в аналізаторі"""
        logger.info(f"Applying selector to analyzer: {selector}")
        
        # Переключення на вкладку аналізатора
        widgets.stackedWidget.setCurrentWidget(widgets.new_page)
        
        # Заповнення поля селектора в Control Panel
        if hasattr(self.control_panel, 'selector_input'):
            self.control_panel.selector_input.setText(selector)
        
        if hasattr(self.control_panel, 'selector_type_combo'):
            idx = 0 if selector_type == "css" else 1
            self.control_panel.selector_type_combo.setCurrentIndex(idx)
        
        # Лог
        if hasattr(self, 'debug_panel'):
            self.debug_panel.log(f"✅ Селектор застосовано: {selector}")
        
        # Статус
        self.control_panel.set_status(f"Селектор готовий: {selector[:50]}...")


    # ==================== ПОМИЛКИ ====================

    def on_navigate_error(self, error: tuple):
        """Обробка помилки навігації"""
        exc_type, exc_value, exc_traceback = error
        logger.error(f"Navigate error: {exc_value}")
        
        self.control_panel.set_status(f"Помилка: {exc_value}")
        
        if hasattr(self, 'debug_panel'):
            self.debug_panel.log(f"❌ Помилка навігації: {exc_value}")


    def on_extract_error(self, error: tuple):
        """Обробка помилки витягування"""
        exc_type, exc_value, exc_traceback = error
        logger.error(f"Extract error: {exc_value}")
        
        self.control_panel.set_status(f"Помилка витягування: {exc_value}")
        
        if hasattr(self, 'debug_panel'):
            self.debug_panel.log(f"❌ Помилка витягування: {exc_value}")


    def on_analyze_error(self, error: tuple):
        """Обробка помилки аналізу"""
        exc_type, exc_value, exc_traceback = error
        logger.error(f"Analyze error: {exc_value}")
        
        self.control_panel.set_status(f"Помилка LLM: {exc_value}")
        
        if hasattr(self, 'debug_panel'):
            self.debug_panel.log(f"❌ Помилка LLM: {exc_value}")
    
    
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