import ctypes
import datetime
import logging
import threading
import traceback
import uuid
from typing import Any, Callable, Dict, Iterable, Optional

from flask import copy_current_request_context, has_request_context, request
from werkzeug.exceptions import BadRequest, HTTPException

from ..deque import LockableDeque
from ..utilities import TimeoutTracker

_LOG = logging.getLogger(__name__)


class ActionKilledException(SystemExit):
    """Sibling of SystemExit, but specific to thread termination."""


class ActionThread(threading.Thread):
    """
    A native thread with extra functionality for tracking progress and thread termination.

    Arguments:
    * `action` is the name of the action that's running
    * `target`, `name`, `args`, `kwargs` and `daemon` are passed to `threading.Thread`
      (though the defualt for `daemon` is changed to `True`)
    * `default_stop_timeout` specifies how long we wait for the `target` function to
      stop nicely (e.g. by checking the `stopping` Event )
    * `log_len` gives the number of log entries before we start dumping them
    * `http_error_lock` allows the calling thread to handle some
      errors initially.  See below.

    ## Error propagation
    If the `target` function throws an Exception, by default this will result in:
    * The thread terminating
    * The Action's status being set to `error`
    * The exception appearing in the logs with a traceback
    * The exception being raised in the background thread.
    However, `HTTPException` subclasses are used in Flask/Werkzeug web apps to
    return HTTP status codes indicating specific errors, and so merit being
    handled differently.

    Normally, when an Action is initiated, the thread handling the HTTP request
    does not return immediately - it waits for a short period to check whether
    the Action has completed or returned an error.  If an HTTPError is raised
    in the Action thread before the initiating thread has sent an HTTP response,
    we **don't** want to propagate the error here, but instead want to re-raise
    it in the calling thread.  This will then mean that the HTTP request is
    answered with the appropriate error code, rather than returning a `201`
    code, along with a description of the task (showing that it was successfully
    started, but also showing that it subsequently failed with an error).

    In order to activate this behaviour, we must pass in a `threading.Lock`
    object.  This lock should already be acquired by the request-handling
    thread.  If an error occurs, and this lock is acquired, the exception
    should not be re-raised until the calling thread has had the chance to deal
    with it.
    """

    def __init__(
        self,
        action: str,
        target: Optional[Callable] = None,
        name: Optional[str] = None,
        args: Optional[Iterable[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        daemon: bool = True,
        default_stop_timeout: int = 5,
        log_len: int = 100,
        http_error_lock: Optional[threading.Lock] = None,
    ):
        threading.Thread.__init__(
            self,
            group=None,
            target=target,
            name=name,
            args=args or (),
            kwargs=kwargs or {},
            daemon=daemon,
        )

        # Action resource corresponding to this action object
        self.action = action

        # A UUID for the ActionThread (not the same as the threading.Thread ident)
        self._ID = uuid.uuid4()  # Task ID

        # Event to track if the task has started
        self.started: threading.Event = threading.Event()
        # Event to track if the user has requested stop
        self.stopping: threading.Event = threading.Event()
        self.default_stop_timeout: int = default_stop_timeout
        # Allow the calling thread to handle HTTP errors for a short time at the start
        self.http_error_lock = http_error_lock or threading.Lock()

        # Make _target, _args, and _kwargs available to the subclass
        self._target: Optional[Callable] = target
        self._args: Iterable[Any] = args or ()
        self._kwargs: Dict[str, Any] = kwargs or {}

        # Nice string representation of target function
        self.target_string: str = (
            f"{self._target}(args={self._args}, kwargs={self._kwargs})"
        )

        # copy_current_request_context allows threads to access flask current_app
        if has_request_context():
            logging.debug("Copying request context to %s", self._target)
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
        self._return_value: Optional[Any] = None  # Return value
        self._request_time: datetime.datetime = datetime.datetime.now()
        self._start_time: Optional[datetime.datetime] = None  # Task start time
        self._end_time: Optional[datetime.datetime] = None  # Task end time
        self._exception: Optional[Exception] = None  # Propagate exceptions helpfully

        # Public state properties
        self.progress: Optional[int] = None  # Percent progress of the task
        self.data: dict = {}  # Dictionary of custom data added during the task
        self._log = LockableDeque(
            None, log_len
        )  # The log will hold dictionary objects with log information

        # Stuff for handling termination
        self._running_lock = (
            threading.Lock()
        )  # Lock obtained while self._target is running

    @property
    def id(self) -> uuid.UUID:
        """
        UUID for the thread. Note this not the same as the native thread ident.
        """
        return self._ID

    @property
    def output(self) -> Any:
        """
        Return value of the Action function. If the Action is still running, returns None.
        """
        return self._return_value

    @property
    def log(self):
        with self._log as logdeque:
            return list(logdeque)

    @property
    def status(self) -> str:
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
    def dead(self) -> bool:
        """
        Has the thread finished, by any means (return, exception, termination).
        """
        return not self.is_alive()

    @property
    def stopped(self) -> bool:
        """Has the thread been cancelled"""
        return self.stopping.is_set()

    @property
    def cancelled(self) -> bool:
        """Alias of `stopped`"""
        return self.stopped

    @property
    def exception(self) -> Optional[Exception]:
        """The Exception that caused the action to fail."""
        return self._exception

    def update_progress(self, progress: int):
        """
        Update the progress of the ActionThread.

        :param progress: int: Action progress, in percent (0-100)

        """
        # Update progress of the task
        self.progress = progress

    def update_data(self, data: Dict[Any, Any]):
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

    def _thread_proc(self, f: Callable):
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
            handler = ThreadLogHandler(self, self._log)
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
            except HTTPException as e:
                self._exception = e
                # If the lock is acquired elsewhere, assume the error
                # will be handled there.
                if self.http_error_lock.acquire(blocking=False):
                    self.http_error_lock.release()
                    logging.error(
                        "An HTTPException occurred in an action thread, but "
                        "the parent request was no longer waiting for it."
                    )
                    logging.error(traceback.format_exc())
                    raise e
            except Exception as e:  # skipcq: PYL-W0703
                self._exception = e
                logging.error(traceback.format_exc())
                raise e
            finally:
                self._end_time = datetime.datetime.now()
                logging.getLogger().removeHandler(handler)  # Stop logging this thread
                # If we don't remove the handler, it's a memory leak.
                if self._exception:
                    self._return_value = str(self._exception)
                    self._status = "error"

        return wrapped

    def get(self, block: bool = True, timeout: Optional[int] = None):
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

    def _is_thread_proc_running(self) -> bool:
        """Test if thread funtion (_thread_proc) is running,
        by attemtping to acquire the lock _thread_proc acquires at runtime.


        :returns: If _thread_proc is currently running

        :rtype: bool

        """
        could_acquire = self._running_lock.acquire(False)
        if could_acquire:
            self._running_lock.release()
            return False
        return True

    def terminate(self, exception=ActionKilledException) -> bool:
        """

        :param exception:  (Default value = ActionKilledException)
        :raises which: should cause the thread to exit silently

        """
        _LOG.warning("Terminating thread %s", self)
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

    def stop(self, timeout=None, exception=ActionKilledException) -> bool:
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
        logging.warning("Forcefully terminating thread %s", self)
        return self.terminate(exception=exception)


class ThreadLogHandler(logging.Handler):
    def __init__(
        self,
        thread: ActionThread,
        dest: LockableDeque,
        level=logging.INFO,
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
        self.dest = dest
        self.addFilter(self.check_thread)

    def check_thread(self, *_):
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
        with self.dest as logdeque:
            logdeque.append(record)
        # TODO: think about whether any of the keys are security flaws
