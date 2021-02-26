from typing import Any

import tornado.httpclient  # type: ignore
import tornado.testing  # type: ignore

from openapi_core import create_spec  # type: ignore
from tornado_openapi3.responses import ResponseValidator


class AsyncOpenAPITestCase(tornado.testing.AsyncHTTPTestCase):
    @property
    def spec(self) -> dict:
        """The OpenAPI 3 specification as a Python dictionary.

        Override this in your request handlers to load or define your OpenAPI 3
        spec.

        """
        return dict()

    @property
    def custom_media_type_deserializers(self) -> dict:
        """A dictionary mapping media types to deserializing functions.

        If your endpoints make use of content types beyond ``application/json``,
        you must add them to this dictionary with a deserializing method that
        converts the raw body (as ``bytes`` or ``str``) to Python objects.

        """
        return dict()

    def setUp(self) -> None:
        """Hook method for setting up the test fixture before exercising it.

        Instantiates the :class:`tornado_openapi3.responses.ResponseValidator`
        for this test case.

        """
        super().setUp()
        self.validator = ResponseValidator(
            create_spec(self.spec),
            custom_media_type_deserializers=self.custom_media_type_deserializers,
        )

    def fetch(
        self, path: str, raise_error: bool = False, **kwargs: Any
    ) -> tornado.httpclient.HTTPResponse:
        """Convenience methiod to synchronously fetch a URL.

        Extends the fetch method in Tornado's
        :class:``tornado.testing.AsyncHTTPTestCase`` to perform OpenAPI 3
        validation on the response received before returning it. If validation
        fails, an :class:`openapi_core.exceptions.OpenAPIError` will be raised
        describing the failure.

        """
        response = super().fetch(path, raise_error=False, **kwargs)
        result = self.validator.validate(response)
        result.raise_for_errors()
        if raise_error:
            response.rethrow()
        return response
