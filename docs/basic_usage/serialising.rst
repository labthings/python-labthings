Marshalling and Serialising views
=================================

Introduction
------------

LabThings makes use of the `Marshmallow library <https://github.com/marshmallow-code/marshmallow/>`_ for both response and argument marshaling. From the Marshmallow documentation:

    **marshmallow** is an ORM/ODM/framework-agnostic library for converting complex datatypes, such as objects, to and from native Python datatypes.

    In short, marshmallow schemas can be used to:

    - **Validate** input data.
    - **Deserialize** input data to app-level objects.
    - **Serialize** app-level objects to primitive Python types. The serialized objects can then be rendered to standard formats such as JSON for use in an HTTP API.

Marshalling schemas are used by LabThings to document the data types of properties, as well as the structure and types of Action arguments and return values. They allow arbitrary Python objects to be returned as serialized JSON, and ensure that input arguments are properly formated before being passed to your Python functions.

From our quickstart example, we use schemas for our `integration_time` property to inform LabThings that both responses *and* requests to the API should be integer formatted. Additional information about range, example values, and units can be added to the schema field.

.. code-block:: python

    labthing.build_property(
        my_spectrometer,  # Python object
        "integration_time",  # Objects attribute name
        description="A magic denoise property",
        schema=fields.Int(min=100, max=500, example=200, unit="microsecond")
    )

Actions require separate schemas for input and output, since the action return data is likely in a different format to the input arguments. In our quickstart example, our `schema` argument informs LabThings that the action return value should be a list of numbers. Meanwhile, our `args` argument informs LabThings that requests to start the action should include an attribute called `n`, which should be an integer. Human-readable descriptions, examples, and default values can be added to the args field.

.. code-block:: python

    labthing.build_action(
        my_spectrometer,  # Python object
        "average_data",  # Objects method name
        description="Take an averaged measurement",
        schema=fields.List(fields.Number()),
        args={  # How do we convert from the request input to function arguments?
            "n": fields.Int(description="Number of averages to take", example=5, default=5)
        },
    )


Schemas
-------

A schema is a collection of keys and fields describing how an object should be serialized/deserialized. Schemas can be created in several ways, either by creating a :class:`labthings.Schema` class, or by passing a dictionary of key-field pairs. 

Note that the :class:`labthings.Schema` class is an alias of :class:`marshmallow.Schema`, and the two can be used interchangeably.

Schemas are required for argument parsing. While Property views can be marshalled with a single field, arguments must be passed to the server as a JSON object, which gets mapped to a Python dictionary and passed to the Action method. 

For example, a Python function of the form: 

.. code-block:: python

    from typing import List

    def my_function(quantity: int, name: str, organizations: List(str)):
        return quantity * len(organizations)

would require `args` of the form:

.. code-block:: python

    args = {
        "quantity": fields.Int()
        "name": fields.String()
        "organisation": fields.List(fields.String())
    }

and a `schema` of :class:`labthings.fields.Int`.


Fields
------

Most data types are represented by fields in the Marshmallow library. All Marshmallow fields are imported and available from the :mod:`labthings.fields` submodule, however any field can be imported from Marshmallow and used in LabThings schemas.

.. automodule:: labthings.fields
    :members:
    :undoc-members:
