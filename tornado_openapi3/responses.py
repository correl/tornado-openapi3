from openapi_core.validation.response.datatypes import (  # type: ignore
    OpenAPIResponse,
    ResponseValidationResult,
)
from openapi_core.validation.response import validators  # type: ignore
from tornado.httpclient import HTTPResponse  # type: ignore

from .requests import TornadoRequestFactory


class TornadoResponseFactory:
    @classmethod
    def create(cls, response: HTTPResponse) -> OpenAPIResponse:
        mimetype = response.headers.get("Content-Type", "text/html")
        return OpenAPIResponse(
            data=response.body.decode("utf-8") if response.body else "",
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
