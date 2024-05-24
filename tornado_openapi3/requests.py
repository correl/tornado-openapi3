import itertools
from typing import Union
from urllib.parse import parse_qsl, urlparse

import attrs
from openapi_core.datatypes import RequestParameters
from openapi_core.validation.request import validators
from openapi_core.validation.request.datatypes import RequestParameters
from tornado.httpclient import HTTPRequest
from tornado.httputil import HTTPServerRequest, parse_cookie
from werkzeug.datastructures import Headers, ImmutableMultiDict


@attrs.define
class Request:
    full_url_pattern: str
    method: str
    parameters: RequestParameters
    body: bytes
    content_type: str

    @property
    def path(self):
        return urlparse(self.full_url_pattern).path

    @property
    def host_url(self):
        parsed = urlparse(self.full_url_pattern)
        return f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""


class TornadoRequestFactory:
    """Factory for converting Tornado requests to OpenAPI request objects."""

    @classmethod
    def create(cls, request: Union[HTTPRequest, HTTPServerRequest]) -> Request:
        """Creates an OpenAPI request from Tornado request objects.

        Supports both :class:`tornado.httpclient.HTTPRequest` and
        :class:`tornado.httputil.HTTPServerRequest` objects.

        """
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

        return Request(
            full_url_pattern=path,
            method=request.method.lower() if request.method else "get",
            parameters=RequestParameters(
                query=query_arguments,
                header=Headers(request.headers.get_all()),
                cookie=parse_cookie(request.headers.get("Cookie", "")),
            ),
            body=request.body if request.body else b"",
            content_type=request.headers.get("Content-Type", "application/x-www-form-urlencoded")
        )


class RequestValidator(validators.V31RequestValidator):
    """Validator for Tornado HTTP Requests."""

    def validate(
        self, request: Union[HTTPRequest, HTTPServerRequest]
    ):
        """Validate a Tornado HTTP request object."""
        return super().validate(TornadoRequestFactory.create(request))


__all__ = ["RequestValidator", "TornadoRequestFactory"]
