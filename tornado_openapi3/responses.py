import attrs
from typing import Mapping, Any, Optional
from openapi_core.protocols import Response
from openapi_core.validation.response import validators  # type: ignore
from tornado.httpclient import HTTPResponse  # type: ignore

from .requests import TornadoRequestFactory


@attrs.define
class Response:
    status_code: int
    content_type: str
    headers: Mapping[str, Any] = attrs.field(factory=dict)
    data: Optional[bytes] = None


class TornadoResponseFactory:
    """Factory for converting Tornado responses to OpenAPI response objects."""

    @classmethod
    def create(cls, response: HTTPResponse) -> Response:
        """Creates an OpenAPI response from Tornado response objects."""
        return Response(
            data=response.body if response.body else b"",
            status_code=response.code,
            content_type=response.headers.get("Content-Type", "text/html"),
            headers=response.headers
        )


class ResponseValidator(validators.V31ResponseValidator):
    """Validator for Tornado HTTP Responses."""

    def validate(self, response: HTTPResponse):
        """Validate a Tornado HTTP response object."""
        return super().validate(
            TornadoRequestFactory.create(response.request),
            TornadoResponseFactory.create(response),
        )


__all__ = ["ResponseValidator", "TornadoResponseFactory"]
