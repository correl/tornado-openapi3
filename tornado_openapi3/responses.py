from openapi_core.validation.response.datatypes import (  # type: ignore
    OpenAPIResponse,
    ResponseValidationResult,
)
from openapi_core.validation.response import validators  # type: ignore
from tornado.httpclient import HTTPResponse  # type: ignore

from .requests import TornadoRequestFactory
from .util import parse_mimetype


class TornadoResponseFactory:
    @classmethod
    def create(cls, response: HTTPResponse) -> OpenAPIResponse:
        mimetype = parse_mimetype(response.headers.get("Content-Type", "text/html"))
        return OpenAPIResponse(
            data=response.body if response.body else b"",
            status_code=response.code,
            mimetype=mimetype,
        )


class ResponseValidator(validators.ResponseValidator):
    def validate(self, response: HTTPResponse) -> ResponseValidationResult:
        return super().validate(
            TornadoRequestFactory.create(response.request),
            TornadoResponseFactory.create(response),
        )


__all__ = ["ResponseValidator", "TornadoResponseFactory"]
