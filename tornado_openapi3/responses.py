from openapi_core.validation.response.datatypes import (  # type: ignore
    OpenAPIResponse,
    ResponseValidationResult,
)
from openapi_core.validation.response import validators  # type: ignore
from tornado.httpclient import HTTPResponse  # type: ignore

from .requests import TornadoRequestFactory
from .util import parse_mimetype


class TornadoResponseFactory:
    """Factory for converting Tornado responses to OpenAPI response objects."""

    @classmethod
    def create(cls, response: HTTPResponse) -> OpenAPIResponse:
        """Creates an OpenAPI response from Tornado response objects."""
        mimetype = parse_mimetype(response.headers.get("Content-Type", "text/html"))
        return OpenAPIResponse(
            data=response.body if response.body else b"",
            status_code=response.code,
            mimetype=mimetype,
        )


class ResponseValidator(validators.ResponseValidator):
    """Validator for Tornado HTTP Responses."""

    def validate(self, response: HTTPResponse) -> ResponseValidationResult:
        """Validate a Tornado HTTP response object."""
        return super().validate(
            TornadoRequestFactory.create(response.request),
            TornadoResponseFactory.create(response),
        )


__all__ = ["ResponseValidator", "TornadoResponseFactory"]
