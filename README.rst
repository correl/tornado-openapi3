===================
 Tornado OpenAPI 3
===================

.. image:: https://travis-ci.com/correl/tornado-openapi3.svg?branch=master
    :target: https://travis-ci.com/correl/tornado-openapi3
.. image:: https://codecov.io/gh/correl/tornado-openapi3/branch/master/graph/badge.svg?token=CTYWWDXTL9
    :target: https://codecov.io/gh/correl/tornado-openapi3
.. image:: https://readthedocs.org/projects/tornado-openapi3/badge/
    :target: https://tornado-openapi3.readthedocs.io
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black


Tornado OpenAPI 3 request and response validation library.

Provides integration between the `Tornado`_ web framework and `Openapi-core`_
library for validating request and response objects against an `OpenAPI 3`_
specification.

Full documentation is available at https://tornado-openapi3.readthedocs.io

Usage
=====

Adding validation to request handlers
-------------------------------------

.. code:: python

   import tornado.ioloop
   import tornado.web
   from tornado_openapi3.handler import OpenAPIRequestHandler


   class MyRequestHandler(OpenAPIRequestHandler):
       spec_dict = {
           "openapi": "3.0.0",
           "info": {
               "title": "Simple Example",
               "version": "1.0.0",
           },
           "paths": {
               "/": {
                   "get": {
                       "responses": {
                           "200": {
                               "description": "Index",
                               "content": {
                                   "text/html": {
                                       "schema": {"type": "string"},
                                   }
                               },
                           }
                       }
                   }
               }
           },
       }


   class RootHandler(MyRequestHandler):
       async def get(self):
           self.finish("Hello, World!")


   if __name__ == "__main__":
       app = tornado.web.Application([(r"/", RootHandler)])
       app.listen(8888)
       tornado.ioloop.IOLoop.current().start()

Validating responses in tests
-----------------------------

.. code:: python

   import unittest

   import tornado.web
   from tornado_openapi3.testing import AsyncOpenAPITestCase


   class RootHandler(tornado.web.RequestHandler):
       async def get(self):
           self.finish("Hello, World!")


   class BaseTestCase(AsyncOpenAPITestCase):
       spec_dict = {
           "openapi": "3.0.0",
           "info": {
               "title": "Simple Example",
               "version": "1.0.0",
           },
           "paths": {
               "/": {
                   "get": {
                       "responses": {
                           "200": {
                               "description": "Index",
                               "content": {
                                   "text/html": {
                                       "schema": {"type": "string"},
                                   }
                               },
                           }
                       }
                   }
               }
           },
       }

       def get_app(self):
           return tornado.web.Application([(r"/", RootHandler)])

       def test_root_endpoint(self):
           response = self.fetch("/")
           self.assertEqual(200, response.code)
           self.assertEqual(b"Hello, World!", response.body)


   if __name__ == "__main__":
       unittest.main()

Contributing
============

Getting Started
---------------

This project uses `Poetry`_ to manage its dependencies. To set up a local
development environment, just run:

.. code:: sh

    poetry install

Formatting Code
---------------

The `Black`_ tool is used by this project to format Python code. It is included
as a development dependency, and should be run on all committed code. To format
code prior to committing it and submitting a PR, run:

.. code:: sh

    poetry run black .

Running Tests
-------------

`pytest`_ is the preferred test runner for this project. It is included as a
development dependency, and is configured to track code coverage, `Flake8`_
style compliance, and `Black`_ code formatting. Tests can be run in your
development environment by running:

.. code:: sh

    poetry run pytest

Additionally, tests can be run using `tox`_, which will run the tests using
multiple versions of both Python and Tornado to ensure broad compatibility.

Configuring Hypothesis
^^^^^^^^^^^^^^^^^^^^^^

Many of the tests make use of `Hypothesis`_ to specify their expectations and
generate a large volume of randomized test input. Because of this, the tests may
take a long time to run on slower computers. Two profiles are defined for
Hypothesis to use which can be selected by setting the ``HYPOTHESIS_PROFILE``
environment variable to one of the following values:

``ci``
  Runs tests using the default Hypothesis settings (100 examples per test) and
  no completion deadline.

``dev``
  The fastest profile, meant for local development only. Uses only 10 examples
  per test with no completion deadline.


.. _Black: https://github.com/psf/black
.. _Flake8: https://flake8.pycqa.org/
.. _Hypothesis: https://hypothesis.readthedocs.io/
.. _OpenAPI 3: https://swagger.io/specification/
.. _Openapi-core: https://github.com/p1c2u/openapi-core
.. _Poetry: https://python-poetry.org/
.. _Tornado: https://www.tornadoweb.org/
.. _pytest: https://pytest.org/
.. _tox: https://tox.readthedocs.io/
