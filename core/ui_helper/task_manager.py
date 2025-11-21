# ///////////////////////////////////////////////////////////////
#
# Task Manager Module
# Менеджер для управління фоновими завданнями
#
# ///////////////////////////////////////////////////////////////

from typing import Callable, Optional, List
from PySide6.QtCore import QThreadPool
from core.ui_helper.worker_thread import WorkerThread, Worker


class TaskManager:
    """
    Менеджер для управління фоновими завданнями
    
    Підтримує:
    - Запуск завдань у потоках
    - Відстеження активних завдань
    - Зупинку всіх завдань
    - Callbacks для завершення/помилок
    """
    
    def __init__(self):
        self.active_threads: List[WorkerThread] = []
        self.thread_pool = QThreadPool.globalInstance()
        self._should_stop = False
        
        # Configure thread pool
        max_threads = self.thread_pool.maxThreadCount()
        print(f"[TaskManager] Thread pool initialized with {max_threads} threads")

    def run_task(
        self,
        task: Callable,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        on_progress: Optional[Callable] = None,
        use_thread_pool: bool = False,
        *args,
        **kwargs
    ) -> WorkerThread:
        """
        Запуск завдання в фоновому потоці
        
        Args:
            task: Функція для виконання
            on_complete: Callback після успішного завершення (приймає результат)
            on_error: Callback при помилці (приймає tuple з exc_info)
            on_progress: Callback для оновлення прогресу (приймає progress, message)
            use_thread_pool: Використовувати QThreadPool замість QThread
            *args, **kwargs: Аргументи для task
            
        Returns:
            WorkerThread: Об'єкт потоку (якщо use_thread_pool=False)
        """
        self._should_stop = False
        
        if use_thread_pool:
            return self._run_with_pool(task, on_complete, on_error, on_progress, *args, **kwargs)
        else:
            return self._run_with_thread(task, on_complete, on_error, on_progress, *args, **kwargs)

    def _run_with_thread(
        self,
        task: Callable,
        on_complete: Optional[Callable],
        on_error: Optional[Callable],
        on_progress: Optional[Callable],
        *args,
        **kwargs
    ) -> WorkerThread:
        """
        Запуск через QThread (рекомендовано для довготривалих завдань)
        """
        worker = WorkerThread(task, *args, **kwargs)
        
        # Connect signals
        if on_complete:
            worker.signals.finished.connect(on_complete)
        
        if on_error:
            worker.signals.error.connect(on_error)
        
        if on_progress:
            worker.signals.progress.connect(on_progress)
        
        # Clean up on finish
        worker.signals.finished.connect(lambda: self._remove_thread(worker))
        worker.signals.error.connect(lambda: self._remove_thread(worker))
        
        # Track and start
        self.active_threads.append(worker)
        worker.start()
        
        print(f"[TaskManager] Started thread task (active: {len(self.active_threads)})")
        return worker

    def _run_with_pool(
        self,
        task: Callable,
        on_complete: Optional[Callable],
        on_error: Optional[Callable],
        on_progress: Optional[Callable],
        *args,
        **kwargs
    ):
        """
        Запуск через QThreadPool (рекомендовано для багатьох коротких завдань)
        """
        worker = Worker(task, *args, **kwargs)
        
        # Connect signals
        if on_complete:
            worker.signals.finished.connect(on_complete)
        
        if on_error:
            worker.signals.error.connect(on_error)
        
        if on_progress:
            worker.signals.progress.connect(on_progress)
        
        # Start in thread pool
        self.thread_pool.start(worker)
        
        print("[TaskManager] Started pool task")
        return worker

    def _remove_thread(self, thread: WorkerThread):
        """
        Видалення потоку зі списку активних
        """
        if thread in self.active_threads:
            self.active_threads.remove(thread)
            print(f"[TaskManager] Thread completed (active: {len(self.active_threads)})")

    def stop_all(self):
        """
        Зупинка всіх активних завдань
        """
        self._should_stop = True
        
        print(f"[TaskManager] Stopping {len(self.active_threads)} active threads...")
        
        for thread in self.active_threads:
            thread.stop()
        
        # Stop thread pool tasks
        self.thread_pool.clear()

    def wait_all(self, timeout: int = 5000):
        """
        Очікування завершення всіх завдань
        
        Args:
            timeout: Максимальний час очікування в мілісекундах
        """
        for thread in self.active_threads[:]:  # Copy list to avoid modification during iteration
            thread.wait(timeout)
        
        # Wait for thread pool
        self.thread_pool.waitForDone(timeout)
        
        print("[TaskManager] All tasks completed")

    def should_stop(self) -> bool:
        """
        Перевірка чи потрібно зупинити виконання
        
        Використовуйте в циклах довготривалих завдань:
        
        for item in items:
            if task_manager.should_stop():
                break
            # process item
        """
        return self._should_stop

    def active_count(self) -> int:
        """
        Кількість активних завдань
        """
        return len(self.active_threads) + self.thread_pool.activeThreadCount()

    def is_busy(self) -> bool:
        """
        Перевірка чи є активні завдання
        """
        return self.active_count() > 0


# Приклад використання:

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    import time
    
    app = QApplication(sys.argv)
    
    manager = TaskManager()
    
    def example_task(duration: int, progress_callback=None):
        """Приклад завдання"""
        for i in range(duration):
            if manager.should_stop():
                return {'status': 'stopped', 'completed': i}
            
            time.sleep(1)
            
            if progress_callback:
                progress = int((i + 1) / duration * 100)
                progress_callback(progress, f"Step {i+1}/{duration}")
        
        return {'status': 'completed', 'duration': duration}
    
    def on_complete(result):
        print(f"Task completed: {result}")
    
    def on_error(error):
        exc_type, exc_value, exc_traceback = error
        print(f"Task error: {exc_value}")
    
    def on_progress(progress, message):
        print(f"Progress: {progress}% - {message}")
    
    # Запуск завдання
    manager.run_task(
        example_task,
        5,  # duration
        on_complete=on_complete,
        on_error=on_error,
        on_progress=on_progress
    )
    
    print("Task started, running event loop...")
    sys.exit(app.exec())