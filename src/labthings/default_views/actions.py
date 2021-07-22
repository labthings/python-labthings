from flask import abort

from .. import fields
from ..find import current_labthing
from ..marshalling import use_args
from ..schema import ActionSchema
from ..views import View, described_operation


class ActionQueueView(View):
    """List of all actions from the session"""

    @described_operation
    def get(self):
        """Action queue

        This endpoint returns a list of all actions that have run since
        the server was started, including ones that have completed and
        actions that are still running.  Each entry includes links to
        manage and inspect that action.
        """
        return ActionSchema(many=True).dump(current_labthing().actions.threads)

    get.responses = {
        "200": {
            "description": "List of Action objects",
            "content": {"application/json": {"schema": ActionSchema(many=True)}},
        }
    }


TASK_ID_PARAMETER = {
    "name": "task_id",
    "in": "path",
    "description": "The unique ID of the action",
    "required": True,
    "schema": {"type": "string"},
    "example": "eeae7ae9-0c0d-45a4-9ef2-7b84bb67a1d1",
}


class ActionObjectView(View):
    """Manage a particular action.

    GET will safely return the current action progress.
    DELETE will cancel the action, if pending or running.


    """

    parameters = [TASK_ID_PARAMETER]

    @described_operation
    def get(self, task_id):
        """Show the status of an Action

        A `GET` request will return the current status
        of an action, including logs.  For completed
        actions, it will include the return value.
        """
        task_dict = current_labthing().actions.to_dict()

        if task_id not in task_dict:
            return abort(404)  # 404 Not Found

        task = task_dict.get(task_id)

        return ActionSchema().dump(task)

    get.responses = {
        "200": {
            "description": "Action object",
            "content": {"application/json": {"schema": ActionSchema}},
        },
        "404": {"description": "Action not found"},
    }

    @described_operation
    @use_args({"timeout": fields.Int()})
    def delete(self, args, task_id):
        """Cancel a running Action

        A `DELETE` request will stop a running action.
        """
        timeout = args.get("timeout", None)
        task_dict = current_labthing().actions.to_dict()

        if task_id not in task_dict:
            return abort(404)  # 404 Not Found

        task = task_dict.get(task_id)
        task.stop(timeout=timeout)
        return ActionSchema().dump(task)

    delete.responses = {
        "200": {
            "description": "Action object that was cancelled",
            "content": {"application/json": {"schema": ActionSchema}},
        },
        "404": {"description": "Action not found"},
    }
