from labthings import tasks

import gevent


def test_spawn_without_context(task_pool):
    def task_func():
        pass

    task_obj = task_pool.spawn(task_func)
    assert isinstance(task_obj, gevent.Greenlet)


def test_spawn_with_context(app_ctx, task_pool):
    def task_func():
        pass

    with app_ctx.test_request_context():
        task_obj = task_pool.spawn(task_func)
        assert isinstance(task_obj, gevent.Greenlet)


def test_update_task_data(task_pool):
    def task_func():
        tasks.update_task_data({"key": "value"})

    task_obj = task_pool.spawn(task_func)
    task_obj.join()
    assert task_obj.data == {"key": "value"}


def test_update_task_data_main_thread():
    # Should do nothing
    tasks.update_task_data({"key": "value"})


def test_update_task_progress(task_pool):
    def task_func():
        tasks.update_task_progress(100)

    task_obj = task_pool.spawn(task_func)
    task_obj.join()
    assert task_obj.progress == 100


def test_update_task_progress_main_thread():
    # Should do nothing
    tasks.update_task_progress(100)


def test_tasks_list(task_pool):
    assert all(
        isinstance(task_obj, gevent.Greenlet) for task_obj in task_pool.greenlets
    )


def test_tasks_dict(task_pool):
    assert all(
        isinstance(task_obj, gevent.Greenlet)
        for task_obj in task_pool.to_dict().values()
    )

    assert all(k == str(t.id) for k, t in task_pool.to_dict().items())


def test_discard_id(task_pool):
    def task_func():
        pass

    task_obj = task_pool.spawn(task_func)
    assert str(task_obj.id) in task_pool.to_dict()
    task_obj.join()

    task_pool.discard_id(task_obj.id)
    assert not str(task_obj.id) in task_pool.to_dict()


def test_cleanup_task(task_pool):
    import time

    def task_func():
        pass

    # Make sure at least 1 tasks is around
    task_pool.spawn(task_func)

    # Wait for all tasks to finish
    gevent.joinall(task_pool.greenlets)

    assert len(task_pool.greenlets) > 0
    task_pool.cleanup()
    assert len(task_pool.greenlets) == 0
