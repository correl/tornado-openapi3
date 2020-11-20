===================
 Tornado OpenAPI 3
===================

.. image:: https://travis-ci.com/correl/tornado-openapi3.svg?branch=master
    :target: https://travis-ci.com/correl/tornado-openapi3

Tornado OpenAPI 3 request and response validation library.

Provides integration between the `Tornado`_ web framework and `Openapi-core`_
library for validating request and response objects against an `OpenAPI 3`_
specification.


.. _Tornado: https://www.tornadoweb.org/
.. _Openapi-core: https://github.com/p1c2u/openapi-core
.. _OpenAPI 3: https://swagger.io/specification/


Adding validation to request handlers
=====================================

.. code:: python

    from openapi_core import create_spec  # type: ignore
    from openapi_core.exceptions import OpenAPIError  # type: ignore
    from openapi_core.deserializing.exceptions import DeserializeError  # type: ignore
    from openapi_core.schema.media_types.exceptions import (  # type: ignore
        InvalidContentType,
    )
    from openapi_core.unmarshalling.schemas.exceptions import ValidateError  # type: ignore
    from tornado.web import RequestHandler
    from tornado_openapi3.requests import RequestValidator
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
