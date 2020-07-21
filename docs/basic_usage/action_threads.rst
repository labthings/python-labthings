Action threads
==============

Many actions in your LabThing may perform tasks that take a long time (compared to the expected response time of a web request). For example, if you were to implement a timelapse action, this inherently runs over a long time.

This introduces a couple of problems. Firstly, a request that triggers a long function will, by default, block the Python interpreter for the duration of the function. This usually causes the connection to timeout, and the response will never be revieved.

Action threads are introduced to manage long-running functions in a way that does not block HTTP requests. Any API Action will automatically run as a background thread.

Internally, the :class:`labthings.LabThing` object stores a list of all requested actions, and their states. This state stores the running status of the action (if itis idle, running, error, or success), information about the start and end times, a unique ID, and, upon completion, the return value of the long-running function. 

By using threads, a function can be started in the background, and it's return value fetched at a later time once it has reported success. If a long-running action is started by some client, it should note the ID returned in the action state JSON, and use this to periodically check on the status of that particular action. 

API routes have been created to allow checking the state of all actions (GET ``/actions``), a particular action by ID (GET ``/actions/<action_id>``), and terminating or removing individual actions (DELETE ``/actions/<action_id>``).

All actions will return a serialized representation of the action state when your POST request returns. If the action completes within a default timeout period (usually 1 second) then the completed action representation will be returned. If the action is still running after this timeout period, the "in-progress" action representation will be returned. The final output value can then be retrieved at a later time.

Most users will not need to create instances of this class. Instead, they will be created automatically when a function is started by an API Action view.

.. autoclass:: labthings.actions.ActionThread
   :noindex:
   :members:

Accessing the current action thread
+++++++++++++++++++++++++++++++++++

A function running inside a :class:`labthings.actions.ActionThread` is able to access the instance it is running in using the :meth:`labthings.current_action` function. This allows the state of the Action to be modified freely.

.. autofunction:: labthings.current_action
   :noindex:


Updating action progress
++++++++++++++++++++++++

Some client applications may be able to display progress bars showing the progress of an action. Implementing progress updates in your actions is made easy with the :py:meth:`labthings.update_action_progress` function. This function takes a single argument, which is the action progress as an integer percent (0 - 100).

If your long running function was started within a :class:`labthings.actions.ActionThread`, this function will update the state of the corresponding :class:`labthings.actions.ActionThread` instance. If your function is called outside of an :class:`labthings.actions.ActionThread` (e.g. by some internal code, not the web API), then this function will silently do nothing.

.. autofunction:: labthings.update_action_progress
   :noindex:
