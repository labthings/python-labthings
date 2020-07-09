from flask import abort

from ..view import View
from ..view.marshalling import marshal_with
from ..schema import ActionSchema
from ..find import current_thing


class ActionQueue(View):
    """
    List of all actions from the session
    """

    def get(self):
        return ActionSchema(many=True).dump(current_thing.actions.greenlets)


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

    def delete(self, task_id):
        """
        Terminate a running task.

        If the task is finished, deletes its entry.
        """
        task_dict = current_thing.actions.to_dict()

        if task_id not in task_dict:
            return abort(404)  # 404 Not Found

        task = task_dict.get(task_id)

        task.kill(block=True, timeout=3)

        return ActionSchema().dump(task)
