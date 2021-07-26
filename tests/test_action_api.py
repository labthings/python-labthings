import json
import logging
import time

import pytest

from labthings import LabThing
from labthings.views import ActionView


@pytest.mark.filterwarnings("ignore:Exception in thread")
def test_action_exception_handling(thing_with_some_views, client):
    """Check errors in an Action are handled correctly



    `/FieldProperty` has a validation constraint - it
    should return a "bad response" error if invoked with
    anything other than
    """
    # `/FailAction` raises an `Exception`.
    # This ought to return a 201 code representing the
    # action that was successfully started - but should
    # show that it failed through the "status" field.

    # This is correct for the current (24/7/2021) behaviour
    # but may want to change for the next version, e.g.
    # returning a 500 code.  For further discussion...
    r = client.post("/FailAction")
    assert r.status_code == 201
    action = r.get_json()
    assert action["status"] == "error"


def test_action_abort(thing_with_some_views, client):
    """Check HTTPExceptions result in error codes.

    Subclasses of HTTPError should result in a non-200 return code, not
    just failures.  This covers Marshmallow validation (400) and
    use of `abort()`.
    """
    # `/AbortAction` should return a 418 error code
    r = client.post("/AbortAction")
    assert r.status_code == 418


@pytest.mark.filterwarnings("ignore:Exception in thread")
def test_action_abort_late(thing_with_some_views, client, caplog):
    """Check HTTPExceptions raised late are just regular errors."""
    caplog.set_level(logging.ERROR)
    caplog.clear()
    r = client.post("/AbortAction", data=json.dumps({"abort_after": 0.2}))
    assert r.status_code == 201  # Should have started OK
    time.sleep(0.3)
    # Now check the status - should be error
    r2 = client.get(r.get_json()["links"]["self"]["href"])
    assert r2.get_json()["status"] == "error"
    # Check it was logged as well
    error_was_raised = False
    for r in caplog.records:
        if r.levelname == "ERROR" and "HTTPException" in r.message:
            error_was_raised = True
    assert error_was_raised


def test_action_validate(thing_with_some_views, client):
    """Validation errors should result in 422 return codes."""
    # `/ActionWithValidation` should fail with a 400 error
    # if `test_arg` is not either `one` or `two`
    r = client.post("/ActionWithValidation", data=json.dumps({"test_arg": "one"}))
    assert r.status_code in [200, 201]
    assert r.get_json()["status"] == "completed"
    r = client.post("/ActionWithValidation", data=json.dumps({"test_arg": "three"}))
    assert r.status_code in [422]
