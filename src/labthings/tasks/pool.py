import logging
from functools import wraps

import threading
from .thread import TaskThread


# TODO: Handle discarding old tasks. Action views now use deques
class Pool:
    """ """

    def __init__(self):
        self.threads = set()

    def add(self, thread: TaskThread):
        """

        :param thread: TaskThread: 

        """
        self.threads.add(thread)

    def start(self, thread: TaskThread):
        """

        :param thread: TaskThread: 

        """
        self.add(thread)
        thread.start()

    def spawn(self, function, *args, **kwargs):
        """

        :param function: 
        :param *args: 
        :param **kwargs: 

        """
        thread = TaskThread(target=function, args=args, kwargs=kwargs)
        self.start(thread)
        return thread

    def kill(self, timeout=5):
        """

        :param timeout:  (Default value = 5)

        """
        for thread in self.threads:
            if thread.is_alive():
                thread.stop(timeout=timeout)

    def tasks(self):
        """


        :returns: List of TaskThread objects.

        :rtype: list

        """
        return list(self.threads)

    def states(self):
        """


        :returns: Dictionary of TaskThread.state dictionaries. Key is TaskThread ID.

        :rtype: dict

        """
        return {str(t.id): t.state for t in self.threads}

    def to_dict(self):
        """


        :returns: Dictionary of TaskThread objects. Key is TaskThread ID.

        :rtype: dict

        """
        return {str(t.id): t for t in self.threads}

    def discard_id(self, task_id):
        """

        :param task_id: 

        """
        marked_for_discard = set()
        for task in self.threads:
            if (str(task.id) == str(task_id)) and task.dead:
                marked_for_discard.add(task)

        for thread in marked_for_discard:
            self.threads.remove(thread)

    def cleanup(self):
        """ """
        marked_for_discard = set()
        for task in self.threads:
            if task.dead:
                marked_for_discard.add(task)

        for thread in marked_for_discard:
            self.threads.remove(thread)

    def join(self):
        """ """
        for thread in self.threads:
            thread.join()


# Operations on the current task


def current_task():
    """Return the Task instance in which the caller is currently running.
    
    If this function is called from outside a Task thread, it will return None.


    :returns: TaskThread -- Currently running Task thread.

    """
    current_task_thread = threading.current_thread()
    if not isinstance(current_task_thread, TaskThread):
        return None
    return current_task_thread


def update_task_progress(progress: int):
    """Update the progress of the Task in which the caller is currently running.
    
    If this function is called from outside a Task thread, it will do nothing.

    :param progress: int
    :param progress: int: 

    """
    if current_task():
        current_task().update_progress(progress)
    else:
        logging.info("Cannot update task progress of __main__ thread. Skipping.")


def update_task_data(data: dict):
    """Update the data of the Task in which the caller is currently running.
    
    If this function is called from outside a Task thread, it will do nothing.

    :param data: dict
    :param data: dict: 

    """
    if current_task():
        current_task().update_data(data)
    else:
        logging.info("Cannot update task data of __main__ thread. Skipping.")
