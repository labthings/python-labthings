import threading
import time

import pytest

from labthings.actions import pool, thread


def test_task_with_args():
    def task_func(arg, kwarg=False):
        pass

    task_obj = thread.ActionThread(
        "task_func", target=task_func, args=("String arg",), kwargs={"kwarg": True}
    )
    assert isinstance(task_obj, threading.Thread)
    assert task_obj._target == task_func
    assert task_obj._args == ("String arg",)
    assert task_obj._kwargs == {"kwarg": True}


def test_task_without_args():
    def task_func():
        pass

    task_obj = thread.ActionThread("task_func", target=task_func)

    assert isinstance(task_obj, threading.Thread)
    assert task_obj._target == task_func
    assert task_obj._args == ()
    assert task_obj._kwargs == {}


def test_task_properties():
    def task_func(arg, kwarg=False):
        pass

    task_obj = thread.ActionThread(
        "task_func", target=task_func, args=("String arg",), kwargs={"kwarg": True}
    )
    assert task_obj.status == task_obj._status
    assert task_obj.id == task_obj._ID
    assert task_obj.status == task_obj._status
    assert task_obj.output == task_obj._return_value


def test_task_update_progress():
    def task_func():
        pool.current_action().update_progress(100)
        return

    task_obj = thread.ActionThread("task_func", target=task_func)

    task_obj.start()
    task_obj.join()
    assert task_obj.progress == 100


def test_task_update_data():
    def task_func():
        pool.current_action().update_data({"key": "value"})
        return

    task_obj = thread.ActionThread("task_func", target=task_func)

    task_obj.start()
    task_obj.join()
    assert task_obj.data == {"key": "value"}


def test_task_start():
    def task_func():
        return "Return value"

    task_obj = thread.ActionThread("task_func", target=task_func)

    assert task_obj._status == "pending"
    assert task_obj._return_value is None

    task_obj.start()
    task_obj.join()
    assert task_obj._return_value == "Return value"
    assert task_obj._status == "completed"


def test_task_get():
    def task_func():
        time.sleep(0.1)
        return "Return value"

    task_obj = thread.ActionThread("task_func", target=task_func)
    task_obj.start()
    assert task_obj.get() == "Return value"


def test_task_get_noblock():
    def task_func():
        time.sleep(0.1)
        return "Return value"

    task_obj = thread.ActionThread("task_func", target=task_func)
    task_obj.start()
    task_obj.join()
    assert task_obj.get(block=False, timeout=0) == "Return value"


def test_task_get_noblock_timeout():
    def task_func():
        time.sleep(0.1)
        return "Return value"

    task_obj = thread.ActionThread("task_func", target=task_func)
    task_obj.start()
    with pytest.raises(TimeoutError):
        assert task_obj.get(block=False, timeout=0)


def test_task_exception():
    exc_to_raise = Exception("Exception message")

    def task_func():
        raise exc_to_raise

    task_obj = thread.ActionThread("task_func", target=task_func)
    task_obj.start()
    task_obj.join()

    assert task_obj._status == "error"
    assert task_obj._return_value == str(exc_to_raise)


def test_task_stop():
    def task_func():
        while not pool.current_action().stopped:
            time.sleep(0)

    task_obj = thread.ActionThread("task_func", target=task_func)
    task_obj.start()
    task_obj.started.wait()
    assert task_obj._status == "running"
    task_obj.stop()
    task_obj.join()
    assert task_obj._status == "cancelled"
    assert task_obj._return_value is None


def test_task_stop_timeout():
    def task_func():
        while True:
            time.sleep(0)

    task_obj = thread.ActionThread("task_func", target=task_func)
    task_obj.start()
    task_obj.started.wait()
    assert task_obj._status == "running"
    task_obj.stop(timeout=0)
    task_obj.join()
    assert task_obj._status == "cancelled"
    assert task_obj._return_value is None


def test_task_terminate():
    def task_func():
        while True:
            time.sleep(0.5)

    task_obj = thread.ActionThread("task_func", target=task_func)
    task_obj.start()
    task_obj.started.wait()
    assert task_obj._status == "running"
    task_obj.terminate()
    task_obj.join()
    assert task_obj._status == "cancelled"
    assert task_obj._return_value is None


def test_task_terminate_not_running():
    def task_func():
        return

    task_obj = thread.ActionThread("task_func", target=task_func)
    task_obj.start()
    task_obj.join()
    assert task_obj.terminate() is False


def test_task_log_without_thread():

    task_log_handler = thread.ThreadLogHandler()

    # Should always return True if not attached to a thread
    assert task_log_handler.check_thread(record=None)


def test_task_log_with_incorrect_thread():

    task_obj = thread.ActionThread(None)
    task_log_handler = thread.ThreadLogHandler(thread=task_obj)

    # Should always return False if called from outside the log handlers thread
    assert task_log_handler.thread == task_obj
    assert not task_log_handler.check_thread(record=None)
