from labthings.find import current_labthing

import gevent


def test_docs(thing, thing_client, schemas_path):

    with thing_client as c:
        json_out = c.get("/docs/swagger").json
        assert "openapi" in json_out
        assert "paths" in json_out
        assert "info" in json_out
        assert c.get("/docs/swagger-ui").status_code == 200


def test_extensions(thing_client):
    with thing_client as c:
        assert c.get("/extensions").json == []


def test_actions_list(thing_client):
    def task_func():
        pass

    task_obj = current_labthing().actions.spawn(task_func)

    with thing_client as c:
        response = c.get("/actions").json
        ids = [task.get("id") for task in response]
        assert str(task_obj.id) in ids


def test_action_representation(thing_client):
    def task_func():
        pass

    task_obj = current_labthing().actions.spawn(task_func)
    task_id = str(task_obj.id)

    with thing_client as c:
        response = c.get(f"/actions/{task_id}").json
        assert response


def test_action_representation_missing(thing_client):
    with thing_client as c:
        assert c.get("/actions/missing_id").status_code == 404


def test_action_kill(thing_client):
    def task_func():
        while True:
            gevent.sleep(0)

    task_obj = current_labthing().actions.spawn(task_func)
    task_id = str(task_obj.id)

    # Wait for task to start
    task_obj.started_event.wait()
    assert task_id in current_labthing().actions.to_dict()

    # Send a DELETE request to terminate the task
    with thing_client as c:
        response = c.delete(f"/actions/{task_id}")
        assert response.status_code == 200
    # Test task was terminated
    assert task_obj._status == "terminated"


def test_action_kill_missing(thing_client):
    with thing_client as c:
        assert c.delete("/actions/missing_id").status_code == 404
