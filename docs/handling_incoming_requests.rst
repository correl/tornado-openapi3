Handling Incoming Requests
==========================

Adding custom deserializers
---------------------------

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
