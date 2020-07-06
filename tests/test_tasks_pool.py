from labthings import tasks

import gevent


def test_taskify_without_context():
    def task_func():
        pass

    task_obj = tasks.taskify(task_func)()
    assert isinstance(task_obj, gevent.Greenlet)


def test_taskify_with_context(app_ctx):
    def task_func():
        pass

    with app_ctx.test_request_context():
        task_obj = tasks.taskify(task_func)()
        assert isinstance(task_obj, gevent.Greenlet)


def test_update_task_data():
    def task_func():
        tasks.update_task_data({"key": "value"})

    task_obj = tasks.taskify(task_func)()
    task_obj.join()
    assert task_obj.data == {"key": "value"}


def test_update_task_data_main_thread():
    # Should do nothing
    tasks.update_task_data({"key": "value"})


def test_update_task_progress():
    def task_func():
        tasks.update_task_progress(100)

    task_obj = tasks.taskify(task_func)()
    task_obj.join()
    assert task_obj.progress == 100


def test_update_task_progress_main_thread():
    # Should do nothing
    tasks.update_task_progress(100)


def test_tasks_list():
    assert all(isinstance(task_obj, gevent.Greenlet) for task_obj in tasks.tasks())


def test_tasks_dict():
    assert all(
        isinstance(task_obj, gevent.Greenlet) for task_obj in tasks.to_dict().values()
    )

    assert all(k == str(t.id) for k, t in tasks.to_dict().items())


def test_discard_id():
    def task_func():
        pass

    task_obj = tasks.taskify(task_func)()
    assert str(task_obj.id) in tasks.to_dict()
    task_obj.join()

    tasks.discard_id(task_obj.id)
    assert not str(task_obj.id) in tasks.to_dict()


def test_cleanup_task():
    import time

    def task_func():
        pass

    # Make sure at least 1 tasks is around
    tasks.taskify(task_func)()

    # Wait for all tasks to finish
    gevent.joinall(tasks.tasks())

    assert len(tasks.tasks()) > 0
    tasks.cleanup()
    assert len(tasks.tasks()) == 0
