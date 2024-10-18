import dataclasses
import http.cookies
import string
import typing
import unittest
import urllib.parse

from hypothesis import given, provisional
import hypothesis.strategies as s
import openapi_core.datatypes
import openapi_core.protocols
from openapi_core.validation.request.datatypes import RequestParameters
import tornado.httpclient
import tornado.httputil
from werkzeug.datastructures import ImmutableMultiDict

import tornado_openapi3.requests

from tests import common

methods = s.sampled_from(
    ["get", "head", "post", "put", "delete", "connect", "options", "trace", "patch"]
)

queries: s.SearchStrategy[ImmutableMultiDict[str, str]] = s.builds(
    ImmutableMultiDict,
    s.lists(
        s.tuples(common.field_names, common.field_values),
    ),
)

cookies: s.SearchStrategy[ImmutableMultiDict[str, str]] = s.builds(
    ImmutableMultiDict,
    s.dictionaries(
        s.text(
            alphabet=string.ascii_letters + string.digits + "!#$%&'*+-.^_`|~:",
            min_size=1,
        ),
        common.field_values,
    ),
)

request_parameters = s.builds(
    RequestParameters,
    query=queries,
    header=common.headers,
    cookie=cookies,
)


@dataclasses.dataclass
class TestOpenAPIRequest:
    parameters: openapi_core.datatypes.RequestParameters
    method: str
    body: typing.Optional[bytes]
    content_type: str
    host_url: str
    path: str


@s.composite
def openapi_requests(
    draw: typing.Callable[[typing.Any], typing.Any]
) -> openapi_core.protocols.Request:
    url = draw(provisional.urls())
    parts = urllib.parse.urlparse(url)
    content_type = draw(common.field_values)
    parameters = draw(request_parameters)
    parameters.header["Content-Type"] = content_type
    if parameters.cookie:
        cookie = http.cookies.SimpleCookie()
        for key, value in parameters.cookie.items():
            cookie[key] = value

        for header in cookie.output(header="").splitlines():
            parameters.header.add_header("Cookie", header.strip())
    return TestOpenAPIRequest(
        parameters=parameters,
        method=draw(methods),
        body=draw(s.one_of(s.none(), s.binary())),
        content_type=content_type,
        host_url="{}://{}".format(parts.scheme, parts.netloc),
        path=parts.path,
    )


class RequestTests(unittest.TestCase):
    def assertOpenAPIRequestsEqual(
        self,
        value: openapi_core.protocols.Request,
        expected: openapi_core.protocols.Request,
    ) -> None:
        self.assertEqual(
            value.parameters.query,
            expected.parameters.query,
            "Query parameters are equal",
        )
        self.assertEqual(
            value.parameters.header, expected.parameters.header, "Headers are equal"
        )
        self.assertEqual(
            value.parameters.cookie, expected.parameters.cookie, "Cookies are equal"
        )
        self.assertEqual(value.method, expected.method, "HTTP methods are equal")
        self.assertEqual(value.body, expected.body, "Bodies are equal")
        self.assertEqual(
            value.content_type, expected.content_type, "Content types are equal"
        )
        self.assertEqual(value.host_url, expected.host_url, "Host URLs are equal")
        self.assertEqual(value.path, expected.path, "Paths are equal")

    def url_from_openapi_request(self, request: TestOpenAPIRequest) -> str:
        scheme, netloc = request.host_url.split("://")
        params = ""
        # Preserves multiple values if the parameters are a multidict. This
        # whole dance is because ImmutableMultiDict's .items() does not return
        # more than one pair per key. Curiously, the Headers structure from the
        # same library does.
        qsl: typing.List[typing.Tuple[str, str]] = []
        query_parameters = ImmutableMultiDict(request.parameters.query)
        for key in query_parameters.keys():
            for value in query_parameters.getlist(key):
                qsl.append((key, value))
        query = urllib.parse.urlencode(qsl)
        fragment = ""
        return urllib.parse.urlunparse(
            (
                scheme,
                netloc,
                request.path,
                params,
                query,
                fragment,
            )
        )

    def tornado_headers_from_openapi_request(
        self, request: TestOpenAPIRequest
    ) -> tornado.httputil.HTTPHeaders:
        headers = tornado.httputil.HTTPHeaders()
        for key, value in request.parameters.header.items():
            headers.add(key, value)
        headers["Content-Type"] = request.content_type
        if request.parameters.cookie:
            cookie = http.cookies.SimpleCookie()
            for key, value in request.parameters.cookie.items():
                cookie[key] = value
            for header in cookie.output(header="").splitlines():
                headers.add("Cookie", header.strip())
        return headers

    def openapi_to_tornado_request(
        self, request: TestOpenAPIRequest
    ) -> tornado.httpclient.HTTPRequest:
        url = self.url_from_openapi_request(request)
        headers = self.tornado_headers_from_openapi_request(request)
        return tornado.httpclient.HTTPRequest(
            url,
            method=request.method.upper(),
            headers=headers,
            body=request.body,
        )

    def openapi_to_tornado_server_request(
        self, request: TestOpenAPIRequest
    ) -> tornado.httputil.HTTPServerRequest:
        url = self.url_from_openapi_request(request)
        headers = self.tornado_headers_from_openapi_request(request)
        uri = url.removeprefix(request.host_url)
        server_request = tornado.httputil.HTTPServerRequest(
            method=request.method.upper(), uri=uri, headers=headers, body=request.body
        )
        scheme, netloc = request.host_url.split("://")
        server_request.protocol = scheme
        server_request.host = netloc
        return server_request

    @given(openapi_requests())
    def test_http_request_round_trip_conversion(
        self, request: TestOpenAPIRequest
    ) -> None:
        converted = tornado_openapi3.requests.TornadoOpenAPIRequest(
            self.openapi_to_tornado_request(request)
        )
        self.assertOpenAPIRequestsEqual(converted, request)

    @given(openapi_requests())
    def test_http_server_request_round_trip_conversion(
        self, request: TestOpenAPIRequest
    ) -> None:
        # HTTP Server request bodies are not optional
        request.body = request.body or b""
        converted = tornado_openapi3.requests.TornadoOpenAPIRequest(
            self.openapi_to_tornado_server_request(request)
        )
        self.assertOpenAPIRequestsEqual(converted, request)
