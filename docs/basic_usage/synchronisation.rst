Synchronisation objects
=======================


Locks
-----

Locks have been implemented to solve a distinct issue, most obvious when considering action tasks. During a long task, it may be  necesarry to block any completing interaction with the LabThing hardware.

The :py:class:`labthings.StrictLock` class is a form of re-entrant lock. Once acquired by a thread, that thread can re-acquire the same lock. This means that other requests or actions will block, or timeout, but the action which acquired the lock is able to re-acquire it.

.. autoclass:: labthings.StrictLock
   :members:
   :noindex:

A CompositeLock allows grouping multiple locks to be simultaneously acquired and released.

.. autoclass:: labthings.CompositeLock
   :members:
   :noindex:


Per-Client events
-----------------

.. autoclass:: labthings.ClientEvent
   :members:
   :noindex: