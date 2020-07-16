from flask import abort

from ..view import View
from ..view.marshalling import marshal_with
from ..view.args import use_args
from ..schema import ActionSchema
from ..find import current_thing
from .. import fields


class ActionQueue(View):
    """
    List of all actions from the session
    """

    def get(self):
        return ActionSchema(many=True).dump(current_thing.actions.threads)


class ActionView(View):
    """
    Manage a particular action.

    GET will safely return the current action progress.
    DELETE will cancel the action, if pending or running.
    """

    def get(self, task_id):
        """
        Show status of a session task

        Includes progress and intermediate data.
        """
        task_dict = current_thing.actions.to_dict()

        if task_id not in task_dict:
            return abort(404)  # 404 Not Found

        task = task_dict.get(task_id)

        return ActionSchema().dump(task)

    @use_args({"timeout": fields.Int(missing=5)})
    def delete(self, args, task_id):
        """
        Terminate a running task.

        If the task is finished, deletes its entry.
        """
        timeout = args.get("timeout", 5)
        task_dict = current_thing.actions.to_dict()

        if task_id not in task_dict:
            return abort(404)  # 404 Not Found

        task = task_dict.get(task_id)

        # TODO: Make non-blocking?
        task.stop(timeout=timeout)

        return ActionSchema().dump(task)
