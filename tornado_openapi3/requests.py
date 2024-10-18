import typing
import urllib.parse
from urllib.parse import parse_qsl

from openapi_core.validation.request.datatypes import RequestParameters

from tornado.httpclient import HTTPRequest
from tornado.httputil import HTTPServerRequest, parse_cookie
from werkzeug.datastructures import ImmutableMultiDict, Headers


class TornadoOpenAPIRequest:
    def __init__(self, request: typing.Union[HTTPRequest, HTTPServerRequest]) -> None:
        """Create an OpenAPI request from Tornado request objects.

        Supports both :class:`tornado.httpclient.HTTPRequest` and
        :class:`tornado.httputil.HTTPServerRequest` objects.

        """
        self.request = request
        if isinstance(request, HTTPRequest):
            parts = urllib.parse.urlparse(request.url)
        else:
            parts = urllib.parse.urlparse(request.full_url())
        protocol = parts.scheme
        host = parts.netloc
        path = parts.path
        query_arguments = parse_qsl(parts.query)
        self.protocol = protocol
        self.host = host
        self.path = path
        cookies = {}
        for values in request.headers.get_list("Cookie"):
            cookies.update(parse_cookie(values))
        self.parameters = RequestParameters(
            query=ImmutableMultiDict(query_arguments),
            header=Headers(request.headers.get_all()),
            cookie=ImmutableMultiDict(cookies),
        )
        self.content_type = request.headers.get(
            "Content-Type", "application/x-www-form-urlencoded"
        )

    @property
    def host_url(self) -> str:
        return "{}://{}".format(self.protocol, self.host)

    @property
    def method(self) -> str:
        method = self.request.method or "GET"
        return method.lower()

    @property
    def body(self) -> typing.Optional[bytes]:
        return self.request.body


__all__ = ["TornadoOpenAPIRequest"]
