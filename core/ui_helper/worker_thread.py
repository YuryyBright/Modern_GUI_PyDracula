# ///////////////////////////////////////////////////////////////
#
# Worker Thread Module
# Модуль для виконання завдань у фонових потоках
#
# ///////////////////////////////////////////////////////////////

from PySide6.QtCore import QObject, QThread, Signal, QRunnable, QThreadPool
from typing import Callable, Optional, Any
import traceback
import sys


class WorkerSignals(QObject):
    """
    Сигнали для комунікації між потоками
    """
    finished = Signal(object)  # Завершення з результатом
    error = Signal(tuple)      # Помилка (exc_type, exc_value, exc_traceback)
    progress = Signal(int, str)  # Прогрес (відсоток, повідомлення)
    status = Signal(str)       # Статус виконання


class WorkerThread(QThread):
    """
    Робочий потік для виконання довготривалих завдань
    
    Usage:
        worker = WorkerThread(task_function, arg1, arg2, kwarg1=value1)
        worker.signals.finished.connect(on_complete)
        worker.signals.error.connect(on_error)
        worker.signals.progress.connect(on_progress)
        worker.start()
    """
    
    def __init__(self, fn: Callable, *args, **kwargs):
        super().__init__()
        
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self._is_running = True
        
        # Add progress callback to kwargs if function accepts it
        if 'progress_callback' not in self.kwargs:
            self.kwargs['progress_callback'] = self.report_progress

    def run(self):
        """
        Виконання завдання
        """
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.signals.error.emit((exc_type, exc_value, exc_traceback))
        finally:
            self._is_running = False

    def report_progress(self, progress: int, message: str = ""):
        """
        Звітування про прогрес виконання
        
        Args:
            progress: Відсоток виконання (0-100)
            message: Повідомлення про статус
        """
        self.signals.progress.emit(progress, message)

    def stop(self):
        """
        Зупинка потоку
        """
        self._is_running = False
        self.quit()

    def is_running(self) -> bool:
        """
        Перевірка чи працює потік
        """
        return self._is_running


class Worker(QRunnable):
    """
    Альтернативний варіант - використання QRunnable з QThreadPool
    Більш ефективний для великої кількості коротких завдань
    
    Usage:
        worker = Worker(task_function, arg1, arg2)
        worker.signals.finished.connect(on_complete)
        QThreadPool.globalInstance().start(worker)
    """
    
    def __init__(self, fn: Callable, *args, **kwargs):
        super().__init__()
        
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.setAutoDelete(True)
        
        # Add progress callback
        if 'progress_callback' not in self.kwargs:
            self.kwargs['progress_callback'] = self.report_progress

    def run(self):
        """
        Виконання завдання
        """
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.signals.error.emit((exc_type, exc_value, exc_traceback))

    def report_progress(self, progress: int, message: str = ""):
        """
        Звітування про прогрес виконання
        """
        self.signals.progress.emit(progress, message)


# Приклади використання:

def example_long_task(duration: int = 5, progress_callback: Optional[Callable] = None) -> dict:
    """
    Приклад довготривалого завдання
    
    Args:
        duration: Тривалість виконання в секундах
        progress_callback: Callback для оновлення прогресу
        
    Returns:
        dict: Результат виконання
    """
    import time
    
    for i in range(duration):
        time.sleep(1)
        
        if progress_callback:
            progress = int((i + 1) / duration * 100)
            progress_callback(progress, f"Processing {i+1}/{duration}")
    
    return {'success': True, 'processed': duration}


def example_data_processing(data: list, progress_callback: Optional[Callable] = None) -> list:
    """
    Приклад обробки даних
    
    Args:
        data: Список даних для обробки
        progress_callback: Callback для оновлення прогресу
        
    Returns:
        list: Оброблені дані
    """
    import time
    
    result = []
    total = len(data)
    
    for i, item in enumerate(data):
        # Simulate processing
        time.sleep(0.1)
        processed_item = item * 2  # Example processing
        result.append(processed_item)
        
        if progress_callback:
            progress = int((i + 1) / total * 100)
            progress_callback(progress, f"Processed {i+1}/{total} items")
    
    return result


def example_api_call(url: str, progress_callback: Optional[Callable] = None) -> dict:
    """
    Приклад API запиту
    
    Args:
        url: URL для запиту
        progress_callback: Callback для оновлення прогресу
        
    Returns:
        dict: Відповідь API
    """
    import time
    
    if progress_callback:
        progress_callback(0, "Connecting...")
    
    time.sleep(1)
    
    if progress_callback:
        progress_callback(50, "Sending request...")
    
    time.sleep(1)
    
    if progress_callback:
        progress_callback(100, "Response received")
    
    return {'status': 'success', 'data': 'example response'}