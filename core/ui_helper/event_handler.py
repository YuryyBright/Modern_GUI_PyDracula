# ///////////////////////////////////////////////////////////////
#
# Event Handler Module
# Централізований обробник подій для легкої масштабованості
#
# ///////////////////////////////////////////////////////////////

from typing import Callable, Dict, Any, Optional
from PySide6.QtCore import QObject


class EventHandler(QObject):
    """
    Централізований обробник подій
    
    Переваги:
    - Легке додавання нових обробників
    - Відокремлення логіки від UI
    - Можливість middleware/логування
    - Простота тестування
    
    Usage:
        handler = EventHandler(main_window)
        handler.register('save_data', self.onSaveData)
        handler.handle('save_data', param1=value1)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.handlers: Dict[str, Callable] = {}
        self.middleware: list = []
        self.logging_enabled = True

    def register(self, event_name: str, handler: Callable):
        """
        Реєстрація обробника події
        
        Args:
            event_name: Назва події
            handler: Функція-обробник
        """
        if event_name in self.handlers:
            print(f"[WARNING] Overwriting handler for event '{event_name}'")
        
        self.handlers[event_name] = handler
        
        if self.logging_enabled:
            print(f"[EventHandler] Registered handler for '{event_name}'")

    def unregister(self, event_name: str):
        """
        Видалення обробника події
        
        Args:
            event_name: Назва події
        """
        if event_name in self.handlers:
            del self.handlers[event_name]
            
            if self.logging_enabled:
                print(f"[EventHandler] Unregistered handler for '{event_name}'")

    def handle(self, event_name: str, *args, **kwargs) -> Any:
        """
        Виконання обробника події
        
        Args:
            event_name: Назва події
            *args, **kwargs: Аргументи для обробника
            
        Returns:
            Any: Результат виконання обробника
        """
        if self.logging_enabled:
            print(f"[EventHandler] Handling event '{event_name}'")
        
        # Check if handler exists
        if event_name not in self.handlers:
            print(f"[WARNING] No handler registered for event '{event_name}'")
            return None
        
        # Apply middleware
        for middleware_fn in self.middleware:
            result = middleware_fn(event_name, args, kwargs)
            if result is False:  # Middleware can cancel event
                if self.logging_enabled:
                    print(f"[EventHandler] Event '{event_name}' cancelled by middleware")
                return None
        
        # Execute handler
        try:
            handler = self.handlers[event_name]
            result = handler(*args, **kwargs)
            return result
        except Exception as e:
            print(f"[ERROR] Exception in handler for '{event_name}': {e}")
            import traceback
            traceback.print_exc()
            return None

    def add_middleware(self, middleware_fn: Callable):
        """
        Додавання middleware функції
        
        Middleware виконується перед кожним обробником
        Повертає False для скасування події
        
        Args:
            middleware_fn: Функція middleware(event_name, args, kwargs) -> bool
        """
        self.middleware.append(middleware_fn)

    def has_handler(self, event_name: str) -> bool:
        """
        Перевірка чи зареєстрований обробник
        
        Args:
            event_name: Назва події
            
        Returns:
            bool: True якщо обробник існує
        """
        return event_name in self.handlers

    def list_handlers(self) -> list:
        """
        Список всіх зареєстрованих обробників
        
        Returns:
            list: Список назв подій
        """
        return list(self.handlers.keys())

    def clear_all(self):
        """
        Видалення всіх обробників
        """
        self.handlers.clear()
        if self.logging_enabled:
            print("[EventHandler] All handlers cleared")


class EventBus(QObject):
    """
    Розширена версія EventHandler з підтримкою підписки/відписки
    Для більш складних сценаріїв з множинними слухачами
    """
    
    def __init__(self):
        super().__init__()
        self.listeners: Dict[str, list] = {}

    def subscribe(self, event_name: str, listener: Callable):
        """
        Підписка на подію (можна багато слухачів на одну подію)
        
        Args:
            event_name: Назва події
            listener: Функція-слухач
        """
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        
        self.listeners[event_name].append(listener)
        print(f"[EventBus] Subscribed to '{event_name}' ({len(self.listeners[event_name])} listeners)")

    def unsubscribe(self, event_name: str, listener: Callable):
        """
        Відписка від події
        
        Args:
            event_name: Назва події
            listener: Функція-слухач
        """
        if event_name in self.listeners and listener in self.listeners[event_name]:
            self.listeners[event_name].remove(listener)
            print(f"[EventBus] Unsubscribed from '{event_name}'")

    def emit(self, event_name: str, *args, **kwargs):
        """
        Генерація події (виклик всіх слухачів)
        
        Args:
            event_name: Назва події
            *args, **kwargs: Аргументи для слухачів
        """
        if event_name not in self.listeners:
            return
        
        print(f"[EventBus] Emitting '{event_name}' to {len(self.listeners[event_name])} listeners")
        
        for listener in self.listeners[event_name]:
            try:
                listener(*args, **kwargs)
            except Exception as e:
                print(f"[ERROR] Exception in listener for '{event_name}': {e}")

    def clear(self, event_name: Optional[str] = None):
        """
        Очищення слухачів
        
        Args:
            event_name: Назва події (якщо None - очищає всі)
        """
        if event_name:
            if event_name in self.listeners:
                del self.listeners[event_name]
        else:
            self.listeners.clear()


# Приклади middleware:

def logging_middleware(event_name: str, args: tuple, kwargs: dict) -> bool:
    """
    Middleware для логування всіх подій
    """
    print(f"[LOG] Event: {event_name}, Args: {args}, Kwargs: {kwargs}")
    return True  # Continue execution


def validation_middleware(event_name: str, args: tuple, kwargs: dict) -> bool:
    """
    Middleware для валідації
    """
    # Приклад: перевірка чи є необхідні параметри
    if event_name == 'save_data':
        if 'data' not in kwargs:
            print("[VALIDATION] Missing 'data' parameter for save_data event")
            return False  # Cancel event
    
    return True


def timing_middleware(event_name: str, args: tuple, kwargs: dict) -> bool:
    """
    Middleware для вимірювання часу виконання
    """
    import time
    start_time = time.time()
    
    # Store start time for later use
    if not hasattr(timing_middleware, 'start_times'):
        timing_middleware.start_times = {}
    
    timing_middleware.start_times[event_name] = start_time
    
    return True


# Приклад використання:

if __name__ == "__main__":
    # Simple event handler
    handler = EventHandler()
    
    def on_save():
        print("Saving data...")
    
    def on_load(filename):
        print(f"Loading from {filename}")
    
    handler.register('save', on_save)
    handler.register('load', on_load)
    
    # Add middleware
    handler.add_middleware(logging_middleware)
    
    # Handle events
    handler.handle('save')
    handler.handle('load', filename='data.json')
    
    print("\n--- Event Bus Example ---\n")
    
    # Event bus with multiple listeners
    bus = EventBus()
    
    def listener1(data):
        print(f"Listener 1 received: {data}")
    
    def listener2(data):
        print(f"Listener 2 received: {data}")
    
    bus.subscribe('data_updated', listener1)
    bus.subscribe('data_updated', listener2)
    
    bus.emit('data_updated', data={'value': 42})