from gevent import Greenlet
import datetime
import logging
import traceback
import uuid

_LOG = logging.getLogger(__name__)


class ThreadTerminationError(SystemExit):
    """Sibling of SystemExit, but specific to thread termination."""


class TaskKillException(Exception):
    """Sibling of SystemExit, but specific to thread termination."""


class TaskThread(Greenlet):
    def __init__(self, target=None, args=None, kwargs=None):
        Greenlet.__init__(self)
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

    @property
    def id(self):
        """Return ID of current TaskThread"""
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

    def _run(self):
        return self._thread_proc(self._target)(*self._args, **self._kwargs)

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
            except Exception as e:  # skipcq: PYL-W0703
                logging.error(e)
                logging.error(traceback.format_exc())
                self._return_value = str(e)
                self._status = "error"
            finally:
                self._end_time = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")

        return wrapped

    def kill(self, exception=TaskKillException, block=True, timeout=None):
        # Kill the greenlet
        Greenlet.kill(self, exception=exception, block=block, timeout=timeout)
        # Set state to terminated
        self._status = "terminated"
        self.progress = None

    def terminate(self):
        return self.kill()
