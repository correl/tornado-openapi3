from typing import Any

import tornado.httpclient  # type: ignore
import tornado.testing  # type: ignore

from openapi_core import create_spec  # type: ignore
from tornado_openapi3.responses import ResponseValidator


class AsyncOpenAPITestCase(tornado.testing.AsyncHTTPTestCase):
    spec: dict = {}
    custom_media_type_deserializers: dict = {}

    def setUp(self) -> None:
        super().setUp()
        self.validator = ResponseValidator(
            create_spec(self.spec),
            custom_media_type_deserializers=self.custom_media_type_deserializers,
        )

    def fetch(
        self, path: str, raise_error: bool = False, **kwargs: Any
    ) -> tornado.httpclient.HTTPResponse:
        response = super().fetch(path, raise_error=False, **kwargs)
        result = self.validator.validate(response)
        result.raise_for_errors()
        if raise_error:
            response.rethrow()
        return response
