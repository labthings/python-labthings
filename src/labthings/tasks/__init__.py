__all__ = [
    "current_task",
    "update_task_progress",
    "update_task_data",
    "TaskKillException",
    "ThreadTerminationError",
]

from .pool import (
    current_task,
    update_task_progress,
    update_task_data,
)
from .thread import TaskKillException

# Legacy alias
ThreadTerminationError = TaskKillException
