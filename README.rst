===================
 Tornado OpenAPI 3
===================

.. image:: https://travis-ci.com/correl/tornado-openapi3.svg?branch=master
    :target: https://travis-ci.com/correl/tornado-openapi3
.. image:: https://codecov.io/gh/correl/tornado-openapi3/branch/master/graph/badge.svg?token=CTYWWDXTL9
    :target: https://codecov.io/gh/correl/tornado-openapi3
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black


Tornado OpenAPI 3 request and response validation library.

Provides integration between the `Tornado`_ web framework and `Openapi-core`_
library for validating request and response objects against an `OpenAPI 3`_
specification.

Usage
=====

Adding validation to request handlers
-------------------------------------

.. code:: python

    from openapi_core import create_spec  # type: ignore
    from openapi_core.exceptions import OpenAPIError  # type: ignore
    from openapi_core.deserializing.exceptions import DeserializeError  # type: ignore
    from openapi_core.schema.media_types.exceptions import (  # type: ignore
        InvalidContentType,
    )
    from openapi_core.unmarshalling.schemas.exceptions import ValidateError  # type: ignore
    from tornado.web import RequestHandler
    from tornado_openapi3 import RequestValidator
    import yaml


    class OpenAPIRequestHandler(RequestHandler):
        async def prepare(self) -> None:
            maybe_coro = super().prepare()
            if maybe_coro and asyncio.iscoroutine(maybe_coro):  # pragma: no cover
                await maybe_coro

            spec = create_spec(yaml.safe_load(self.render_string("openapi.yaml")))
            validator = RequestValidator(spec)
            result = validator.validate(self.request)
            try:
                result.raise_for_errors()
            except InvalidContentType:
                self.set_status(415)
                self.finish()
            except (DeserializeError, ValidateError) as e:
                self.set_status(400)
                self.finish()
            except OpenAPIError:
                raise

Validating a response
---------------------

.. code:: python

    from tornado.testing import AsyncHTTPTestCase
    from tornado_openapi3 import ResponseValidator

    from myapplication import create_app, spec


    class TestResponses(AsyncHTTPTestCase):
        def get_app(self) -> Application:
            return create_app()

        def test_status(self) -> None:
            validator = ResponseValidator(spec)
            response = self.fetch("/status")
            result = validator.validate(response)
            result.raise_for_errors()

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

``default``
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
