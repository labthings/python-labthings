from gevent import Greenlet, GreenletExit
from gevent.thread import get_ident
from gevent.event import Event
from flask import copy_current_request_context, has_request_context
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
    def __init__(self, target, *args, **kwargs):
        Greenlet.__init__(self)

        # A UUID for the TaskThread (not the same as the threading.Thread ident)
        self._ID = uuid.uuid4()  # Task ID

        # Event to track if the task has started
        self.started_event = Event()

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
        else:
            logging.debug("No request context to copy")

        # Private state properties
        self._status: str = "pending"  # Task status
        self._return_value = None  # Return value
        self._request_time = datetime.datetime.now()
        self._start_time = None  # Task start time
        self._end_time = None  # Task end time

        # Public state properties
        self.progress: int = None  # Percent progress of the task
        self.data = {}  # Dictionary of custom data added during the task
        self.log = []  # The log will hold dictionary objects with log information

    @property
    def id(self):
        """Return ID of current TaskThread"""
        return self._ID

    @property
    def ident(self):
        """Compatibility with threading interface. A small, unique non-negative integer that identifies this object."""
        return get_ident(self)

    @property
    def output(self):
        return self._return_value

    @property
    def status(self):
        return self._status

    def update_progress(self, progress: int):
        # Update progress of the task
        self.progress = progress

    def update_data(self, data: dict):
        # Store data to be used before task finishes (eg for real-time plotting)
        self.data.update(data)

    def _run(self):  # pylint: disable=E0202
        return self._thread_proc(self._target)(*self._args, **self._kwargs)

    def _thread_proc(self, f):
        """
        Wraps the target function to handle recording `status` and `return` to `state`.
        Happens inside the task thread.
        """

        def wrapped(*args, **kwargs):
            nonlocal self

            # Capture just this thread's log messages
            handler = ThreadLogHandler(thread=self, dest=self.log)
            logging.getLogger().addHandler(handler)

            self._status = "running"
            self._start_time = datetime.datetime.now()
            self.started_event.set()
            try:
                self._return_value = f(*args, **kwargs)
                self._status = "success"
            except (TaskKillException, GreenletExit) as e:
                logging.error(e)
                # Set state to terminated
                self._status = "terminated"
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

    def kill(self, exception=TaskKillException, block=True, timeout=None):
        # Kill the greenlet
        Greenlet.kill(self, exception=exception, block=block, timeout=timeout)

    def terminate(self):
        return self.kill()


class ThreadLogHandler(logging.Handler):
    def __init__(self, thread=None, dest=None, level=logging.INFO):
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
        self.dest = dest if dest is not None else []
        self.addFilter(self.check_thread)

    def check_thread(self, record):
        """Determine if a thread matches the desired record"""
        if self.thread is None:
            return 1

        if get_ident() == get_ident(self.thread):
            return 1
        return 0

    def emit(self, record):
        """Do something with a logged message"""
        record_dict = {"message": record.getMessage()}
        for k in ["created", "levelname", "levelno", "lineno", "filename"]:
            record_dict[k] = getattr(record, k)
        self.dest.append(record_dict)
        # FIXME: make sure this doesn't become a memory disaster!
        # We probably need to check the size of the list...
        # TODO: think about whether any of the keys are security flaws
        # (this is why I don't dump the whole logrecord)
