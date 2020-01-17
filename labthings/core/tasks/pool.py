import threading
import logging
from functools import wraps

from .thread import TaskThread

from flask import copy_current_request_context


class TaskMaster:
    def __init__(self, *args, **kwargs):
        self._tasks = []

    @property
    def tasks(self):
        """
        Returns:
            list: List of TaskThread objects. 
        """
        return self._tasks

    @property
    def dict(self):
        """
        Returns:
            dict: Dictionary of TaskThread objects. Key is TaskThread ID.
        """
        return {str(t.id): t for t in self._tasks}

    @property
    def states(self):
        """
        Returns:
            dict: Dictionary of TaskThread.state dictionaries. Key is TaskThread ID.
        """
        return {str(t.id): t.state for t in self._tasks}

    def new(self, f, *args, **kwargs):
        # copy_current_request_context allows threads to access flask current_app
        task = TaskThread(
            target=copy_current_request_context(f), args=args, kwargs=kwargs
        )
        self._tasks.append(task)
        return task

    def remove(self, task_id):
        for task in self._tasks:
            if (task.id == task_id) and not task.isAlive():
                del task

    def cleanup(self):
        for task in self._tasks:
            if not task.isAlive():
                del task


# Task management


def tasks():
    """
    List of tasks in default taskmaster
    Returns:
        list: List of tasks in default taskmaster
    """
    global _default_task_master
    return _default_task_master.tasks


def dict():
    """
    Dictionary of tasks in default taskmaster
    Returns:
        dict: Dictionary of tasks in default taskmaster
    """
    global _default_task_master
    return _default_task_master.dict


def states():
    """
    Dictionary of TaskThread.state dictionaries. Key is TaskThread ID.
    Returns:
        dict: Dictionary of task states in default taskmaster
    """
    global _default_task_master
    return _default_task_master.states


def cleanup_tasks():
    global _default_task_master
    return _default_task_master.cleanup()


def remove_task(task_id: str):
    global _default_task_master
    return _default_task_master.remove(task_id)


# Operations on the current task


def current_task():
    current_task_thread = threading.current_thread()
    if not isinstance(current_task_thread, TaskThread):
        return None
    return current_task_thread


def update_task_progress(progress: int):
    if current_task():
        current_task().update_progress(progress)
    else:
        logging.info("Cannot update task progress of __main__ thread. Skipping.")


def update_task_data(data: dict):
    if current_task():
        current_task().update_data(data)
    else:
        logging.info("Cannot update task data of __main__ thread. Skipping.")


# Main "taskify" functions


def taskify(f):
    """
    A decorator that wraps the passed in function
    and surpresses exceptions should one occur
    """

    @wraps(f)
    def wrapped(*args, **kwargs):
        task = _default_task_master.new(
            f, *args, **kwargs
        )  # Append to parent object's task list
        task.start()  # Start the function
        return task

    return wrapped


# Create our default, protected, module-level task pool
_default_task_master = TaskMaster()
