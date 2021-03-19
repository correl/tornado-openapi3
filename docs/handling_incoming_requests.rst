Handling Incoming Requests
==========================

Tornado OpenAPI 3 allows you to validate requests coming in to your application
against your OpenAPI 3.0 specification with little additional code.

Defining a base handler with your OpenAPI 3.0 specification
-----------------------------------------------------------

By extending :class:`~tornado_openapi3.handler.OpenAPIRequestHandler`, you can
define your own base request handler with your specification attached, and use
that for each of your specialized request handlers for your application.

.. literalinclude:: examples/simple.py

A more complex example
----------------------

Your specification doesn't need to be embedded in your code. You may wish to
store it separately in your repository, or even templatize some aspects of it
(like your application version). Doing so is as simple as overriding your
request handler's
:attr:`~tornado_openapi3.handler.OpenAPIRequestHandler.spec_dict` property to
load your specification however you see fit.

By default, the specification is compiled on every request. To achieve better
performance, you may also wish to override the request handler's
:attr:`~tornado_openapi3.handler.OpenAPIRequestHandler.spec_dict` property to
cache the result on your application object.

.. literalinclude:: examples/cached.py

Adding custom deserializers
---------------------------

If your endpoints make use of content types beyond ``application/json``, you
must add them to this dictionary with a deserializing method that converts the
raw body (as :class:`bytes` or :class:`str`) to Python objects.

.. code-block:: python

   import json

   from tornado_openapi3.handler import OpenAPIRequestHandler


   class ResourceHandler(OpenAPIRequestHandler):
       custom_media_type_deserializers = {
           "application/vnd.example.resource+json": json.loads,
       }

       ...

Adding custom formatters
------------------------

If your schemas make use of format modifiers, you may specify them in this
dictionary paired with a :class:`~tornado_openapi3.types.Formatter` object that
provides methods to validate values and unmarshal them into Python objects.

.. code-block:: python

   import datetime

   from tornado_openapi3.handler import OpenAPIRequestHandler


   class USDateFormatter:
       def validate(self, value: str) -> bool:
           return bool(re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", value))

       def unmarshal(self, value: str) -> datetime.date:
           return datetime.datetime.strptime(value, "%m/%d/%Y").date()


   class ResourceHandler(OpenAPIRequestHandler):
       custom_formatters = {
           "usdate": USDateFormatter(),
       }

       ...
