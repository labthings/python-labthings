__all__ = [
    "current_task",
    "update_task_progress",
    "update_task_data",
    "TaskKillException",
    "ThreadTerminationError",
]

from .pool import (
    Pool,
    current_task,
    update_task_progress,
    update_task_data,
)
from .thread import TaskThread, TaskKillException

# Legacy alias
ThreadTerminationError = TaskKillException
