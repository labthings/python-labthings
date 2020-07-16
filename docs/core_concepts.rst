Core Concepts
=============

LabThings is rooted in the `W3C Web of Things standards <https://www.w3.org/WoT/>`_. Using IP networking in labs is not itself new, though perhaps under-used. However lack of proper standardisation has stiffled widespread adoption. LabThings, rather than try to introduce new competing standards, uses the architecture and terminology introduced by the W3C Web of Things. A full description of the core architecture can be found in the `Web of Things (WoT) Architecture <https://www.w3.org/TR/wot-architecture/#sec-wot-architecture>`_ document. However, a brief outline of core terminology is given below.

Web Thing
---------

A Web Thing is defined as "an abstraction of a physical or a virtual entity whose metadata and interfaces are described by a WoT Thing description." For LabThings this corresponds to an individual lab instrument that exposes functionality available to the user via a web API, and that functionality is described by a Thing Description.

LabThings automatically generates a Thing Description as you add functionality. The functionality you add falls into one of three categories of "interaction affordance": Properties, Actions, and Events.

Properties
----------

A Property is defined as "an Interaction Affordance that exposes the state of the Thing. The state exposed by a Property MUST be retrievable (readable). Optionally, the state exposed by a Property MAY be updated (writeable)."

As a rule of thumb, any attribute of your device that can be quickly read, or optionally written, should be a Property. For example, simple device settings, or one-shot measurements such as temperature.

Actions
-------

An Action is defined as "an Interaction Affordance that allows to invoke a function of the Thing. An Action MAY manipulate state that is not directly exposed (cf. Properties), manipulate multiple Properties at a time, or manipulate Properties based on internal logic (e.g., toggle). Invoking an Action MAY also trigger a process on the Thing that manipulates state (including physical state through actuators) over time."

The key point here is that Actions are typically more complex in functionality than simply setting or getting a property. For example, they can set multiple properties simultaneously (for example, auto-exposing a camera), or they can manipulate the state of the Thing over time, for example starting a long-running data acquisition.

Python-LabThings automatically handles offloading Actions into background threads where appropriate. The Action has a short timeout to complete quickly and respond to the API request, after which time a ``201 - Started`` response is sent to the client with information on how to check the state of the Action at a later time. This is particularly useful for long-running data acquisitions, as it allows users to start an acquisition and get immediate confirmation that it has started, after which point they can poll for changes in status.

Events
------

An event "describes an event source that pushes data asynchronously from the Thing to the Consumer. Here not state, but state transitions (i.e., events) are communicated. Events MAY be triggered through conditions that are not exposed as Properties."

Common examples are notifying clients when a Property is changed, or when an Action starts or finishes. However, Thing developers can introduce new Events such as warnings, status messages, and logs. For example, a device may emit an events when the internal temperature gets too high, or when an interlock is tripped. This Event can then be pushed to both users AND other Things, allowing automtic response to external conditions.

A good example of this might be having Things automatically pause data-acquisition Actions upon detection of an overheat or interlock Event from another Thing.