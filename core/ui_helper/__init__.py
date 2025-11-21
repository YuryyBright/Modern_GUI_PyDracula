# ///////////////////////////////////////////////////////////////
#
# Core Module Initialization
# Централізований доступ до всіх core компонентів
#
# ///////////////////////////////////////////////////////////////

from .worker_thread import WorkerThread, Worker, WorkerSignals
from .task_manager import TaskManager
from .event_handler import EventHandler, EventBus

__all__ = [
    'WorkerThread',
    'Worker',
    'WorkerSignals',
    'TaskManager',
    'EventHandler',
    'EventBus'
]

__version__ = '2.0.0'
__author__ = 'Your Name'

print(f"[Core] Module loaded v{__version__}")