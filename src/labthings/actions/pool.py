import logging
from functools import wraps

import threading
from .thread import ActionThread


# TODO: Handle discarding old actions. Action views now use deques
class Pool:
    """ """

    def __init__(self):
        self.threads = set()

    def add(self, thread: ActionThread):
        """

        :param thread: ActionThread: 

        """
        self.threads.add(thread)

    def start(self, thread: ActionThread):
        """

        :param thread: ActionThread: 

        """
        self.add(thread)
        thread.start()

    def spawn(self, function, *args, **kwargs):
        """

        :param function: 
        :param *args: 
        :param **kwargs: 

        """
        thread = ActionThread(target=function, args=args, kwargs=kwargs)
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


        :returns: List of ActionThread objects.

        :rtype: list

        """
        return list(self.threads)

    def states(self):
        """


        :returns: Dictionary of ActionThread.state dictionaries. Key is ActionThread ID.

        :rtype: dict

        """
        return {str(t.id): t.state for t in self.threads}

    def to_dict(self):
        """


        :returns: Dictionary of ActionThread objects. Key is ActionThread ID.

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


def current_action():
    """Return the ActionThread instance in which the caller is currently running.
    
    If this function is called from outside an ActionThread, it will return None.


    :returns: :class:`labthings.actions.ActionThread` -- Currently running ActionThread.

    """
    current_action_thread = threading.current_thread()
    if not isinstance(current_action_thread, ActionThread):
        return None
    return current_action_thread


def update_action_progress(progress: int):
    """Update the progress of the ActionThread in which the caller is currently running.
    
    If this function is called from outside an ActionThread, it will do nothing.

    :param progress: int: Action progress, in percent (0-100)

    """
    if current_action():
        current_action().update_progress(progress)
    else:
        logging.info("Cannot update task progress of __main__ thread. Skipping.")


def update_action_data(data: dict):
    """Update the data of the ActionThread in which the caller is currently running.
    
    If this function is called from outside an ActionThread, it will do nothing.

    :param data: dict: Action data dictionary

    """
    if current_action():
        current_action().update_data(data)
    else:
        logging.info("Cannot update task data of __main__ thread. Skipping.")
