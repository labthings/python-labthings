from labthings.core import tasks
from flask import Flask, Response
import pytest

import gevent


@pytest.fixture()
def app(request):

    app = Flask(__name__)

    # pushes an application context manually
    ctx = app.app_context()
    ctx.push()

    # bind the test life with the context through the
    request.addfinalizer(ctx.pop)
    return app


@pytest.fixture()
def app_context(app):
    with app.app_context():
        yield app


def test_taskify_without_context():
    def task_func():
        pass

    task_obj = tasks.taskify(task_func)()
    assert isinstance(task_obj, gevent.Greenlet)


def test_taskify_with_context(app_context):
    def task_func():
        pass

    with app_context.test_request_context():
        task_obj = tasks.taskify(task_func)()
        assert isinstance(task_obj, gevent.Greenlet)


def test_update_task_data():
    def task_func():
        tasks.update_task_data({"key": "value"})

    task_obj = tasks.taskify(task_func)()
    task_obj.join()
    assert task_obj.state.get("data") == {"key": "value"}


def test_update_task_data_main_thread():
    # Should do nothing
    tasks.update_task_data({"key": "value"})


def test_update_task_progress():
    def task_func():
        tasks.update_task_progress(100)

    task_obj = tasks.taskify(task_func)()
    task_obj.join()
    assert task_obj.state.get("progress") == 100


def test_update_task_progress_main_thread():
    # Should do nothing
    tasks.update_task_progress(100)


def test_tasks_list():
    assert all([isinstance(task_obj, gevent.Greenlet) for task_obj in tasks.tasks()])


def test_tasks_dict():
    assert all(
        [
            isinstance(task_obj, gevent.Greenlet)
            for task_obj in tasks.dictionary().values()
        ]
    )

    assert all([k == str(t.id) for k, t in tasks.dictionary().items()])


def test_task_states():
    state_keys = {
        "function",
        "id",
        "status",
        "progress",
        "data",
        "return",
        "start_time",
        "end_time",
    }

    for state in tasks.states().values():
        assert all(k in state for k in state_keys)


def test_remove_task():
    def task_func():
        pass

    task_obj = tasks.taskify(task_func)()
    assert str(task_obj.id) in tasks.dictionary()
    task_obj.join()

    tasks.remove_task(task_obj.id)
    assert not str(task_obj.id) in tasks.dictionary()


def test_cleanup_task():
    import time

    def task_func():
        pass

    # Make sure at least 1 tasks is around
    tasks.taskify(task_func)()

    # Wait for all tasks to finish
    gevent.joinall(tasks.tasks())

    assert len(tasks.tasks()) > 0
    tasks.cleanup_tasks()
    assert len(tasks.tasks()) == 0
