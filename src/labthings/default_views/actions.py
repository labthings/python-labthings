from flask import abort

from .. import fields
from ..find import current_labthing
from ..marshalling import use_args
from ..schema import ActionSchema
from ..views import View


class ActionQueueView(View):
    """List of all actions from the session"""

    def get(self):
        """Action queue
        ---
        description: Queue of most recent actions in the session
        summary: Queue of most recent actions in the session
        responses:
            200:
                content:
                    application/json:
                        schema: ActionSchema
        """
        return ActionSchema(many=True).dump(current_labthing().actions.threads)


class ActionObjectView(View):
    """Manage a particular action.

    GET will safely return the current action progress.
    DELETE will cancel the action, if pending or running.


    """

    def get(self, task_id):
        """Show the status of an Action
        ---
        description: Status of an Action
        summary: Status of an Action
        responses:
            200:
                content:
                    application/json:
                        schema: ActionSchema
        """
        task_dict = current_labthing().actions.to_dict()

        if task_id not in task_dict:
            return abort(404)  # 404 Not Found

        task = task_dict.get(task_id)

        return ActionSchema().dump(task)

    @use_args({"timeout": fields.Int()})
    def delete(self, args, task_id):
        """Cancel a running Action
        ---
        description: Cancel an Action
        summary: Cancel an Action
        responses:
            200:
                content:
                    application/json:
                        schema: ActionSchema
        """
        timeout = args.get("timeout", None)
        task_dict = current_labthing().actions.to_dict()

        if task_id not in task_dict:
            return abort(404)  # 404 Not Found

        task = task_dict.get(task_id)
        task.stop(timeout=timeout)
        return ActionSchema().dump(task)
