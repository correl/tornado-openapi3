Testing API Responses
=====================

Tornado OpenAPI 3 includes a base test class to help you validate each of your
application's responses while you test its behavior.

Making your tests aware of your API specification
-------------------------------------------------

By extending :class:`~tornado_openapi3.testing.AsyncOpenAPITestCase`, you can
define your test cases with your specification attached. Every response returned
by :meth:`~tornado_openapi3.testing.AsyncOpenAPITestCase.fetch` will be
automatically checked against your specification to ensure they match the
formats documented, and exceptions will be raised when they do not.

Because it extends :class:`tornado.testing.AsyncHTTPTestCase`, you can write
your application tests as you normally would with added confidence that your API
is behaving exactly as you expect it to.

.. literalinclude:: examples/test.py

Adding custom deserializers
---------------------------

If your endpoints make use of content types beyond ``application/json``, you
must add them to this dictionary with a deserializing method that converts the
raw body (as :class:`bytes` or :class:`str`) to Python objects.

.. code-block:: python

   import json

   from tornado_openapi3.testing import AsyncOpenAPITestCase


   class TestCase(AsyncOpenAPITestCase):
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

   from tornado_openapi3.testing import AsyncOpenAPITestCase


   class USDateFormatter:
       def validate(self, value: str) -> bool:
           return bool(re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", value))

       def unmarshal(self, value: str) -> datetime.date:
           return datetime.datetime.strptime(value, "%m/%d/%Y").date()


   class TestCase(AsyncOpenAPITestCase):
       custom_formatters = {
           "usdate": USDateFormatter(),
       }

       ...
