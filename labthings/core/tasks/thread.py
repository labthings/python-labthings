import ctypes
import datetime
import logging
import traceback
import uuid

import threading

_LOG = logging.getLogger(__name__)


class ThreadTerminationError(SystemExit):
    """Sibling of SystemExit, but specific to thread termination."""


class TaskThread(threading.Thread):
    def __init__(self, target=None, name=None, args=None, kwargs=None, daemon=True):
        threading.Thread.__init__(
            self,
            group=None,
            target=target,
            name=name,
            args=args,
            kwargs=kwargs,
            daemon=daemon,
        )
        # Handle arguments
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}

        # A UUID for the TaskThread (not the same as the threading.Thread ident)
        self._ID = uuid.uuid4()  # Task ID

        # Make _target, _args, and _kwargs available to the subclass
        self._target = target
        self._args = args
        self._kwargs = kwargs

        # Nice string representation of target function
        self.target_string = f"{self._target}(args={self._args}, kwargs={self._kwargs})"

        # Private state properties
        self._status: str = "idle"  # Task status
        self._return_value = None  # Return value
        self._start_time = None  # Task start time
        self._end_time = None  # Task end time

        # Public state properties
        self.progress: int = None  # Percent progress of the task
        self.data = {}  # Dictionary of custom data added during the task

        # Stuff for handling termination
        self._running_lock = (
            threading.Lock()
        )  # Lock obtained while self._target is running
        self._killed = (
            threading.Event()
        )  # Event triggered when thread is manually terminated

    @property
    def id(self):
        """
        Return ID of current TaskThread
        """
        return self._ID

    @property
    def state(self):
        return {
            "function": self.target_string,
            "id": self._ID,
            "status": self._status,
            "progress": self.progress,
            "data": self.data,
            "return": self._return_value,
            "start_time": self._start_time,
            "end_time": self._end_time,
        }

    def update_progress(self, progress: int):
        # Update progress of the task
        self.progress = progress

    def update_data(self, data: dict):
        # Store data to be used before task finishes (eg for real-time plotting)
        self.data.update(data)

    def _thread_proc(self, f):
        """
        Wraps the target function to handle recording `status` and `return` to `state`.
        Happens inside the task thread.
        """

        def wrapped(*args, **kwargs):
            nonlocal self

            self._status = "running"
            self._start_time = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
            try:
                self._return_value = f(*args, **kwargs)
                self._status = "success"
            except Exception as e:
                logging.error(e)
                logging.error(traceback.format_exc())
                self._return_value = str(e)
                self._status = "error"
            finally:
                self._end_time = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")

        return wrapped

    def run(self):
        """
        Overrides default threading.Thread run() method
        """
        logging.debug((self._args, self._kwargs))
        try:
            with self._running_lock:
                if self._killed.is_set():
                    raise ThreadTerminationError()
                if self._target:
                    self._thread_proc(self._target)(*self._args, **self._kwargs)
        finally:
            # Avoid a refcycle if the thread is running a function with
            # an argument that has a member that points to the thread.
            del self._target, self._args, self._kwargs

    def wait(self):
        """
        Start waiting for the task to finish before returning
        """
        print("Joining thread {}".format(self))
        self.join()
        return self._return_value

    def async_raise(self, exc_type):
        """Raise an exception in this thread."""
        # Should only be called on a started thread, so raise otherwise.
        if self.ident is None:
            raise RuntimeError(
                "Cannot halt a thread that hasn't started. No valid running thread identifier."
            )

        # If the thread has died we don't want to raise an exception so log.
        if not self.is_alive():
            _LOG.debug(
                "Not raising %s because thread %s (%s) is not alive",
                exc_type,
                self.name,
                self.ident,
            )
            return

        result = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(self.ident), ctypes.py_object(exc_type)
        )
        if result == 0 and self.is_alive():
            # Don't raise an exception an error unnecessarily if the thread is dead.
            raise ValueError("Thread ID was invalid.", self.ident)
        elif result > 1:
            # Something bad happened, call with a NULL exception to undo.
            ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, None)
            raise RuntimeError(
                "Error: PyThreadState_SetAsyncExc %s %s (%s) %s"
                % (exc_type, self.name, self.ident, result)
            )

    def _is_thread_proc_running(self):
        """
        Test if thread funtion (_thread_proc) is running,
        by attemtping to acquire the lock _thread_proc acquires at runtime.
        Returns:
            bool: If _thread_proc is currently running
        """
        could_acquire = self._running_lock.acquire(0)
        if could_acquire:
            self._running_lock.release()
            return False
        return True

    def terminate(self):
        """
        Raise ThreadTerminatedException in the context of the given thread,
        which should cause the thread to exit silently.
        """
        _LOG.warning(f"Terminating thread {self}")
        self._killed.set()
        if not self.is_alive():
            logging.debug("Cannot kill thread that is no longer running.")
            return
        if not self._is_thread_proc_running():
            logging.debug(
                "Thread's _thread_proc function is no longer running, "
                "will not kill; letting thread exit gracefully."
            )
            return
        self.async_raise(ThreadTerminationError)

        # Wait for the thread for finish closing. If the threaded function has cleanup code in a try-except,
        # this pause allows it to finish running before the main process can continue.
        while self._is_thread_proc_running():
            pass

        # Set state to terminated
        self._status = "terminated"
        self.progress = None
