import logging
from functools import wraps
from gevent import getcurrent
from gevent.pool import Pool as _Pool, PoolFull

from .thread import TaskThread


# TODO: Handle discarding old tasks. Action views now use deques
class Pool(_Pool):
    def __init__(self, size=None):
        _Pool.__init__(self, size=size, greenlet_class=TaskThread)

    def add(self, greenlet, blocking=True, timeout=None):
        """
        Override the default Gevent pool `add` method so that
        tasks are not discarded as soon as they finish.
        """
        if not self._semaphore.acquire(blocking=blocking, timeout=timeout):
            # We failed to acquire the semaphore.
            # If blocking was True, then there was a timeout. If blocking was
            # False, then there was no capacity. Either way, raise PoolFull.
            raise PoolFull()

        try:
            self.greenlets.add(greenlet)
            self._empty_event.clear()
        except:
            self._semaphore.release()
            raise

    def tasks(self):
        """
        Returns:
            list: List of TaskThread objects.
        """
        return list(self.greenlets)

    def states(self):
        """
        Returns:
            dict: Dictionary of TaskThread.state dictionaries. Key is TaskThread ID.
        """
        return {str(t.id): t.state for t in self.greenlets}

    def to_dict(self):
        """
        Returns:
            dict: Dictionary of TaskThread objects. Key is TaskThread ID.
        """
        return {str(t.id): t for t in self.greenlets}

    def discard_id(self, task_id):
        marked_for_discard = set()
        for task in self.greenlets:
            if (str(task.id) == str(task_id)) and task.dead:
                marked_for_discard.add(task)

        for greenlet in marked_for_discard:
            self.discard(greenlet)

    def cleanup(self):
        marked_for_discard = set()
        for task in self.greenlets:
            if task.dead:
                marked_for_discard.add(task)

        for greenlet in marked_for_discard:
            self.discard(greenlet)


# Operations on the current task


def current_task():
    """Return the Task instance in which the caller is currently running.

    If this function is called from outside a Task thread, it will return None.

    Returns:
        TaskThread -- Currently running Task thread.
    """
    current_task_thread = getcurrent()
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
    global default_pool

    @wraps(f)
    def wrapped(*args, **kwargs):
        task = default_pool.spawn(
            f, *args, **kwargs
        )  # Append to parent object's task list
        return task

    return wrapped


# Create our default, protected, module-level task pool
default_pool = Pool()

tasks = default_pool.tasks
to_dict = default_pool.to_dict
states = default_pool.states
cleanup = default_pool.cleanup
discard_id = default_pool.discard_id
