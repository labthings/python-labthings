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
    global DEFAULT_TASK_MASTER
    return DEFAULT_TASK_MASTER.tasks


def dictionary():
    """
    Dictionary of tasks in default taskmaster
    Returns:
        dict: Dictionary of tasks in default taskmaster
    """
    global DEFAULT_TASK_MASTER
    return DEFAULT_TASK_MASTER.dict


def states():
    """
    Dictionary of TaskThread.state dictionaries. Key is TaskThread ID.
    Returns:
        dict: Dictionary of task states in default taskmaster
    """
    global DEFAULT_TASK_MASTER
    return DEFAULT_TASK_MASTER.states


def cleanup_tasks():
    """Remove all finished tasks from the task list"""
    global DEFAULT_TASK_MASTER
    return DEFAULT_TASK_MASTER.cleanup()


def remove_task(task_id: str):
    """Remove a particular task from the task list

    Arguments:
        task_id {str} -- ID of the target task
    """
    global DEFAULT_TASK_MASTER
    return DEFAULT_TASK_MASTER.remove(task_id)


# Operations on the current task


def current_task():
    """Return the Task instance in which the caller is currently running.

    If this function is called from outside a Task thread, it will return None.

    Returns:
        TaskThread -- Currently running Task thread.
    """
    current_task_thread = threading.current_thread()
    if not isinstance(current_task_thread, TaskThread):
        return None
    return current_task_thread


def update_task_progress(progress: int):
    """Update the progress of the Task in which the caller is currently running.

    If this function is called from outside a Task thread, it will do nothing.

    Arguments:
        progress {int} -- Current progress, in percent (0-100)
    """
    if current_task():
        current_task().update_progress(progress)
    else:
        logging.info("Cannot update task progress of __main__ thread. Skipping.")


def update_task_data(data: dict):
    """Update the data of the Task in which the caller is currently running.

    If this function is called from outside a Task thread, it will do nothing.

    Arguments:
        data {dict} -- Additional data to merge with the Task data
    """
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
        task = DEFAULT_TASK_MASTER.new(
            f, *args, **kwargs
        )  # Append to parent object's task list
        task.start()  # Start the function
        return task

    return wrapped


# Create our default, protected, module-level task pool
DEFAULT_TASK_MASTER = TaskMaster()
