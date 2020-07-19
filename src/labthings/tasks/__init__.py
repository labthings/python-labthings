__all__ = [
    "current_task",
    "current_task_stopped",
    "update_task_progress",
    "update_task_data",
    "TaskKillException",
    "ThreadTerminationError",
]

from .pool import (
    current_task,
    current_task_stopped,
    update_task_progress,
    update_task_data,
)
from .thread import TaskKillException

# Legacy alias
ThreadTerminationError = TaskKillException
