import ctypes
import datetime
import logging
import threading
import traceback
import uuid

from flask import request, copy_current_request_context, has_request_context

from ..utilities import TimeoutTracker
from ..deque import Deque

_LOG = logging.getLogger(__name__)


class ActionKilledException(SystemExit):
    """Sibling of SystemExit, but specific to thread termination."""


class ActionThread(threading.Thread):
    """
    A native thread with extra functionality for tracking progress and thread termination.
    """

    def __init__(
        self,
        action,
        target=None,
        name=None,
        args=None,
        kwargs=None,
        daemon=True,
        default_stop_timeout: int = 5,
        log_len: int = 100,
    ):
        threading.Thread.__init__(
            self,
            group=None,
            target=target,
            name=name,
            args=args,
            kwargs=kwargs,
            daemon=daemon,
        )

        # Safely populate missing arguments
        args = args or ()
        kwargs = kwargs or {}

        # Action resource corresponding to this action object
        self.action = action

        # A UUID for the ActionThread (not the same as the threading.Thread ident)
        self._ID = uuid.uuid4()  # Task ID

        # Event to track if the task has started
        self.started = threading.Event()
        # Event to track if the user has requested stop
        self.stopping = threading.Event()
        self.default_stop_timeout = default_stop_timeout

        # Make _target, _args, and _kwargs available to the subclass
        self._target = target
        self._args = args
        self._kwargs = kwargs

        # Nice string representation of target function
        self.target_string = f"{self._target}(args={self._args}, kwargs={self._kwargs})"

        # copy_current_request_context allows threads to access flask current_app
        if has_request_context():
            logging.debug(f"Copying request context to {self._target}")
            self._target = copy_current_request_context(self._target)
            try:
                self.input = request.json
            except BadRequest:
                self.input = None
        else:
            logging.debug("No request context to copy")
            self.input = None

        # Private state properties
        self._status: str = "pending"  # Task status
        self._return_value = None  # Return value
        self._request_time = datetime.datetime.now()
        self._start_time = None  # Task start time
        self._end_time = None  # Task end time

        # Public state properties
        self.progress: int = None  # Percent progress of the task
        self.data = {}  # Dictionary of custom data added during the task
        self.log = Deque(
            None, log_len
        )  # The log will hold dictionary objects with log information

        # Stuff for handling termination
        self._running_lock = (
            threading.Lock()
        )  # Lock obtained while self._target is running

    @property
    def id(self):
        """
        UUID for the thread. Note this not the same as the native thread ident.
        """
        return self._ID

    @property
    def output(self):
        """
        Return value of the Action function. If the Action is still running, returns None.
        """
        return self._return_value

    @property
    def status(self):
        """
        Current running status of the thread.

        ==============  =============================================
        Status          Meaning
        ==============  =============================================
        ``pending``     Not yet started
        ``running``     Currently in-progress
        ``completed``   Finished without error
        ``cancelled``   Thread stopped after a cancel request
        ``error``       Exception occured in thread
        ==============  =============================================
        """
        return self._status

    @property
    def dead(self):
        """
        Has the thread finished, by any means (return, exception, termination).
        """
        return not self.is_alive()

    @property
    def stopped(self):
        """ """
        return self.stopping.is_set()

    def update_progress(self, progress: int):
        """
        Update the progress of the ActionThread.

        :param progress: int: Action progress, in percent (0-100)

        """
        # Update progress of the task
        self.progress = progress

    def update_data(self, data: dict):
        """

        :param data: dict:

        """
        # Store data to be used before task finishes (eg for real-time plotting)
        self.data.update(data)

    def run(self):
        """Overrides default threading.Thread run() method"""
        logging.debug((self._args, self._kwargs))
        try:
            if self._target:
                with self._running_lock:
                    self._thread_proc(self._target)(*self._args, **self._kwargs)
        finally:
            # Avoid a refcycle if the thread is running a function with
            # an argument that has a member that points to the thread.
            del self._target, self._args, self._kwargs

    def _thread_proc(self, f):
        """Wraps the target function to handle recording `status` and `return` to `state`.
        Happens inside the task thread.

        :param f:

        """

        def wrapped(*args, **kwargs):
            """

            :param *args:
            :param **kwargs:

            """
            nonlocal self

            # Capture just this thread's log messages
            handler = ThreadLogHandler(thread=self, dest=self.log)
            logging.getLogger().addHandler(handler)

            self._status = "running"
            self._start_time = datetime.datetime.now()
            self.started.set()
            try:
                self._return_value = f(*args, **kwargs)
                self._status = "completed"
            except (ActionKilledException, SystemExit) as e:
                logging.error(e)
                # Set state to stopped
                self._status = "cancelled"
                self.progress = None
            except Exception as e:  # skipcq: PYL-W0703
                logging.error(e)
                logging.error(traceback.format_exc())
                self._return_value = str(e)
                self._status = "error"
                raise e
            finally:
                self._end_time = datetime.datetime.now()
                logging.getLogger().removeHandler(handler)  # Stop logging this thread
                # If we don't remove the handler, it's a memory leak.

        return wrapped

    def get(self, block=True, timeout=None):
        """Start waiting for the task to finish before returning

        :param block:  (Default value = True)
        :param timeout:  (Default value = None)

        """
        if not block:
            if self.is_alive():
                raise TimeoutError
        self.join(timeout=timeout)
        return self._return_value

    def _async_raise(self, exc_type):
        """

        :param exc_type:

        """
        # Should only be called on a started thread, so raise otherwise.
        if self.ident is None:
            raise RuntimeError("Only started threads have thread identifier")

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
        """Test if thread funtion (_thread_proc) is running,
        by attemtping to acquire the lock _thread_proc acquires at runtime.


        :returns: If _thread_proc is currently running

        :rtype: bool

        """
        could_acquire = self._running_lock.acquire(0)
        if could_acquire:
            self._running_lock.release()
            return False
        return True

    def terminate(self, exception=ActionKilledException):
        """

        :param exception:  (Default value = ActionKilledException)
        :raises which: should cause the thread to exit silently

        """
        _LOG.warning(f"Terminating thread {self}")
        if not (self.is_alive() or self._is_thread_proc_running()):
            logging.debug("Cannot kill thread that is no longer running.")
            return False
        self._async_raise(exception)

        # Wait (block) for the thread to finish closing. If the threaded function has cleanup code in a try-except,
        # this pause allows it to finish running before the main thread can continue.
        while self._is_thread_proc_running():
            pass

        # Set state to stopped
        self._status = "cancelled"
        self.progress = None
        return True

    def stop(self, timeout=None, exception=ActionKilledException):
        """Sets the threads internal stopped event, waits for timeout seconds for the
        thread to stop nicely, then forcefully kills the thread.

        :param timeout: Time to wait before killing thread forecefully. Defaults to ``self.default_stop_timeout``
        :type timeout: int
        :param exception:  (Default value = ActionKilledException)

        """
        if timeout is None:
            timeout = self.default_stop_timeout

        self.stopping.set()
        timeout_tracker = TimeoutTracker(timeout)
        # While the timeout hasn't expired
        while not timeout_tracker.stopped:
            # If the thread has stopped
            if not self.is_alive():
                # Break
                self._status = "cancelled"
                return True
        # If the timeout tracker stopped before the thread died, kill it
        logging.warning(f"Forcefully terminating thread {self}")
        return self.terminate(exception=exception)


class ThreadLogHandler(logging.Handler):
    def __init__(
        self, thread=None, dest=None, level=logging.INFO, default_log_len: int = 100
    ):
        """Set up a log handler that appends messages to a list.

        This log handler will first filter by ``thread``, if one is
        supplied.  This should be a ``threading.Thread`` object.
        Only log entries from the specified thread will be
        saved.

        ``dest`` should specify a list, to which we will append
        each log entry as it comes in.  If none is specified, a
        new list will be created.

        NB this log handler does not currently rotate or truncate
        the list - so if you use it on a thread that produces a
        lot of log messages, you may run into memory problems.


        """
        logging.Handler.__init__(self)
        self.setLevel(level)
        self.thread = thread
        self.dest = dest if dest is not None else Deque(None, default_log_len)
        self.addFilter(self.check_thread)

    def check_thread(self, record):
        """Determine if a thread matches the desired record

        :param record:

        """
        if self.thread is None:
            return 1
        if threading.get_ident() == self.thread.ident:
            return 1
        return 0

    def emit(self, record):
        """Do something with a logged message

        :param record:

        """
        self.dest.append(record)
        # TODO: think about whether any of the keys are security flaws


# Backwards compatibility
ActionThread = ActionThread
