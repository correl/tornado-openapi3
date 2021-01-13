import itertools
from urllib.parse import parse_qsl
from typing import Union

from openapi_core.validation.request.datatypes import (  # type: ignore
    OpenAPIRequest,
    RequestParameters,
    RequestValidationResult,
)
from openapi_core.validation.request import validators  # type: ignore
from tornado.httpclient import HTTPRequest  # type: ignore
from tornado.httputil import HTTPServerRequest  # type: ignore
from werkzeug.datastructures import ImmutableMultiDict, Headers

from .util import parse_mimetype


class TornadoRequestFactory:
    @classmethod
    def create(cls, request: Union[HTTPRequest, HTTPServerRequest]) -> OpenAPIRequest:
        if isinstance(request, HTTPRequest):
            if request.url:
                path, _, querystring = request.url.partition("?")
                query_arguments: ImmutableMultiDict[str, str] = ImmutableMultiDict(
                    parse_qsl(querystring)
                )
            else:
                path = ""
                query_arguments = ImmutableMultiDict()
        else:
            path, _, _ = request.full_url().partition("?")
            if path == "://":
                path = ""
            query_arguments = ImmutableMultiDict(
                itertools.chain(
                    *[
                        [(k, v.decode("utf-8")) for v in vs]
                        for k, vs in request.query_arguments.items()
                    ]
                )
            )
        return OpenAPIRequest(
            full_url_pattern=path,
            method=request.method.lower() if request.method else "get",
            parameters=RequestParameters(
                query=query_arguments, header=Headers(request.headers.get_all())
            ),
            body=request.body if request.body else b"",
            mimetype=parse_mimetype(
                request.headers.get("Content-Type", "application/x-www-form-urlencoded")
            ),
        )


class RequestValidator(validators.RequestValidator):
    def validate(
        self, request: Union[HTTPRequest, HTTPServerRequest]
    ) -> RequestValidationResult:
        return super().validate(TornadoRequestFactory.create(request))


__all__ = ["RequestValidator", "TornadoRequestFactory"]
