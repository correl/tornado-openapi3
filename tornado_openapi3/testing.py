import typing

import tornado.httpclient
import tornado.testing
import openapi_core

from tornado_openapi3.requests import TornadoOpenAPIRequest
from tornado_openapi3.responses import TornadoOpenAPIResponse
from tornado_openapi3.types import Deserializer, Formatter


class AsyncOpenAPITestCase(tornado.testing.AsyncHTTPTestCase):
    """A test case that starts up an HTTP server.

    An async test case extending :class:`tornado.testing.AsyncHTTPTestCase`,
    providing OpenAPI spec validation on the responses from your application and
    raising errors in tests.

    """

    @property
    def spec_dict(self) -> dict:
        """The OpenAPI 3 specification

        Override this in your test cases to load or define your OpenAPI 3 spec.

        :rtype: dict

        """
        raise NotImplementedError()

    @property
    def spec(self) -> openapi_core.OpenAPI:
        """The OpenAPI 3 specification.

        Override this in your test cases to customize how your OpenAPI 3 spec is
        loaded and validated.

        :rtype: :class:`openapi_core.schema.specs.model.Spec`

        """
        config = openapi_core.Config(
            extra_format_unmarshallers={
                format: formatter.unmarshal
                for format, formatter in self.custom_formatters.items()
            },
            extra_format_validators={
                format: formatter.validate
                for format, formatter in self.custom_formatters.items()
            },
            extra_media_type_deserializers=self.custom_media_type_deserializers,
        )
        return openapi_core.OpenAPI.from_dict(self.spec_dict, config=config)

    @property
    def custom_formatters(self) -> typing.Dict[str, Formatter]:
        """A dictionary mapping value formats to formatter objects.

        A formatter object must provide:
        - validate(self, value) -> bool
        - unmarshal(self, value) -> Any
        """

        return dict()

    @property
    def custom_media_type_deserializers(self) -> typing.Dict[str, Deserializer]:
        """A dictionary mapping media types to deserializing functions.

        If your endpoints make use of content types beyond ``application/json``,
        you must add them to this dictionary with a deserializing method that
        converts the raw body (as ``bytes`` or ``str``) to Python objects.

        """
        return dict()

    def fetch(
        self, path: str, raise_error: bool = False, **kwargs: typing.Any
    ) -> tornado.httpclient.HTTPResponse:
        """Convenience methiod to synchronously fetch a URL.

        Extends the fetch method in Tornado's
        :class:``tornado.testing.AsyncHTTPTestCase`` to perform OpenAPI 3
        validation on the response received before returning it. If validation
        fails, an :class:`openapi_core.exceptions.OpenAPIError` will be raised
        describing the failure.

        If the path begins with http:// or https://, it will be treated as a
        full URL and will be fetched as-is, and no validation will occur.

        """
        if path.lower().startswith(("http://", "https://")):
            return super().fetch(path, raise_error=raise_error, **kwargs)

        response = super().fetch(path, raise_error=False, **kwargs)
        result = self.spec.unmarshal_response(
            request=TornadoOpenAPIRequest(response.request),
            response=TornadoOpenAPIResponse(response),
        )
        result.raise_for_errors()
        if raise_error:
            response.rethrow()
        return response
